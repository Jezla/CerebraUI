# adapters/langflow_adapter.py
import json
import asyncio
import random
from typing import Dict, Any, AsyncIterator, Optional

import httpx


class UpstreamError(Exception):
    pass


class UpstreamTimeout(UpstreamError):
    pass


class LangFlowAdapter:
    """
    LangFlow 适配器：
    - 优先 ?stream=true 真流式；若流式失败或无增量 → 回退一次性 (?stream=false)
    - 支持上游超时/重试（指数退避）
    - 透传 params.tweaks 到 LangFlow（温度、max tokens 等）
    - NEW: 对 422（部分 Flow 不支持流式/校验更严）自动回退到非流式
    """

    def __init__(
        self,
        base_url: str,
        flow_id: str,
        api_key: Optional[str] = None,
        run_path: str = "/api/v1/run/{flow_id}",
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        retry_max: int = 3,
        retry_base: float = 0.5,
        retry_max_backoff: float = 4.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.flow_id = flow_id
        self.run_url = f"{self.base_url}{run_path.format(flow_id=self.flow_id)}"
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.retry_max = max(0, int(retry_max))
        self.retry_base = max(0.05, float(retry_base))
        self.retry_max_backoff = max(self.retry_base, float(retry_max_backoff))

        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["x-api-key"] = api_key
            self.headers["Authorization"] = f"Bearer {api_key}"

    # --------------- 内部工具 ---------------

    def _pick_text(self, obj: dict) -> Optional[str]:
        """尽量从常见结构里提取文本"""
        try:
            t = (
                obj.get("outputs", [{}])[0]
                .get("outputs", [{}])[0]
                .get("results", {})
                .get("message", {})
                .get("text")
            )
            if t:
                return t
        except Exception:
            pass

        for key in ("text", "delta", "content", "token", "response", "output", "result"):
            v = obj.get(key)
            if isinstance(v, str) and v.strip():
                return v
            if key == "delta" and isinstance(v, dict):
                c = v.get("content")
                if isinstance(c, str) and c.strip():
                    return c
        return None

    def _payload(self, inputs: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "output_type": "chat",
            "input_type": "chat",
            "input_value": inputs.get("query", ""),
            # 透传 LangFlow 的 tweaks（如果 Flow/组件支持）
            "tweaks": params.get("tweaks", {}) or {},
        }

    async def _sleep_backoff(self, attempt: int):
        backoff = min(self.retry_max_backoff, self.retry_base * (2 ** attempt))
        await asyncio.sleep(backoff * (0.8 + random.random() * 0.4))

    # --------------- 非流式（支持重试） ---------------
    async def run_once(self, inputs: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._payload(inputs, params)
        url = f"{self.run_url}?stream=false"
        timeout = httpx.Timeout(self.read_timeout, connect=self.connect_timeout)

        last_exc: Optional[Exception] = None
        for attempt in range(self.retry_max + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    r = await client.post(url, json=payload, headers=self.headers)
                    # 429/5xx 参与重试，其它 4xx 直接抛出
                    if r.status_code == 429 or 500 <= r.status_code < 600:
                        r.raise_for_status()
                    r.raise_for_status()
                    return r.json()
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                last_exc = e
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response is not None else 0
                if status == 429 or 500 <= status < 600:
                    last_exc = e
                else:
                    # 把服务端返回体也带上，便于排障
                    body = e.response.text if getattr(e, "response", None) else ""
                    raise UpstreamError(f"LangFlow HTTP {status}: {body or e}") from e
            except Exception as e:
                last_exc = e

            if attempt < self.retry_max:
                await self._sleep_backoff(attempt)
            else:
                if isinstance(last_exc, (httpx.ConnectTimeout, httpx.ReadTimeout)):
                    raise UpstreamTimeout(f"LangFlow timeout after retries: {last_exc}") from last_exc
                raise UpstreamError(f"LangFlow request failed after retries: {last_exc}") from last_exc

        raise UpstreamError("Unknown error (run_once)")

    # --------------- 流式（连接阶段重试 + 422 回退） ---------------
    async def stream(self, inputs: Dict[str, Any], params: Dict[str, Any]) -> AsyncIterator[str]:
        """
        - 连接阶段（POST/打开流）失败：按策略重试
        - 读取阶段使用 read_timeout，若超过则抛 UpstreamTimeout
        - 一旦成功吐出内容，就不再进行重试（避免重复回复）
        - 若整个流期间没有任何片段：回退到一次性
        - NEW: 若遇到 422（不少 Flow 的流式端点不支持），立即回退到一次性
        """
        payload = self._payload(inputs, params)
        url = f"{self.run_url}?stream=true"

        if str(params.get("stream", "true")).lower() in ("false", "0", "no"):
            data = await self.run_once(inputs, params)
            text = self._pick_text(data) or str(data)
            yield text
            return

        yielded_any = False
        last_exc: Optional[Exception] = None

        for attempt in range(self.retry_max + 1):
            try:
                timeout = httpx.Timeout(self.read_timeout, connect=self.connect_timeout)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", url, json=payload, headers=self.headers) as resp:
                        # 422：直接回退非流式（很多 Flow 在 stream=true 时会 422）
                        if resp.status_code == 422:
                            data = await self.run_once(inputs, params)
                            text = self._pick_text(data) or str(data)
                            yield text
                            return

                        # 429/5xx 参与重试；其它 4xx 直接报错
                        if resp.status_code == 429 or 500 <= resp.status_code < 600:
                            resp.raise_for_status()
                        resp.raise_for_status()

                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            if line.startswith("data:"):
                                line = line[5:].strip()
                            if not line or line.startswith(":") or line.startswith("event:"):
                                continue

                            text = None
                            try:
                                obj = json.loads(line)
                                text = self._pick_text(obj)
                            except Exception:
                                text = line

                            if text and text.strip():
                                yielded_any = True
                                yield str(text)

                        # 正常流结束
                        break

            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                if yielded_any:
                    raise UpstreamTimeout(f"LangFlow stream read timeout: {e}") from e
                last_exc = e
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response is not None else 0
                if yielded_any:
                    raise UpstreamError(f"LangFlow stream HTTP {status}: {e}") from e
                if status == 429 or 500 <= status < 600:
                    last_exc = e
                else:
                    body = e.response.text if getattr(e, "response", None) else ""
                    # 保险：部分旧版本把 422 当 400/404，这里统一回退
                    if status in (400, 404, 422):
                        data = await self.run_once(inputs, params)
                        text = self._pick_text(data) or str(data)
                        yield text
                        return
                    raise UpstreamError(f"LangFlow stream HTTP {status}: {body or e}") from e
            except Exception as e:
                if yielded_any:
                    raise UpstreamError(f"LangFlow stream error: {e}") from e
                last_exc = e

            if not yielded_any:
                if attempt < self.retry_max:
                    await self._sleep_backoff(attempt)
                    continue
                else:
                    data = await self.run_once(inputs, params)
                    text = self._pick_text(data) or str(data)
                    yield text
                    return

        if not yielded_any:
            data = await self.run_once(inputs, params)
            text = self._pick_text(data) or str(data)
            yield text
