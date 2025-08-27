# app/main.py
import os
import uuid
import json
import time
import asyncio
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, Header, HTTPException, Request, Depends, Body
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

import redis.asyncio as aioredis

# Auth libs
import jwt  # PyJWT
from jwt import PyJWKClient, InvalidTokenError

# Metrics
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

from adapters.langflow_adapter import LangFlowAdapter, UpstreamError, UpstreamTimeout

# DB
from app.db import AsyncSessionLocal, init_db
from app.models import Base, Run as RunModel, Workflow as WfModel

# -------------------- 日志 --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

app = FastAPI(title="AI Orchestrator")
Instrumentator().instrument(app).expose(app, include_in_schema=False)

# -------------------- 配置 --------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Auth 模式: disabled | hs256 | jwks
AUTH_MODE = os.getenv("AUTH_MODE", "disabled").lower()
JWT_SECRET = os.getenv("JWT_SECRET")          # hs256 模式
JWT_ALGS = os.getenv("JWT_ALGS", "HS256").split(",")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")      # 可选
JWT_ISSUER = os.getenv("JWT_ISSUER")          # 可选
JWT_JWKS_URL = os.getenv("JWT_JWKS_URL")      # jwks 模式

# 限流（每分钟）
RL_USER_PER_MIN = int(os.getenv("RL_USER_PER_MIN", "60"))
RL_WORKFLOW_PER_MIN = int(os.getenv("RL_WORKFLOW_PER_MIN", "30"))

# 默认 LangFlow（回退用）
LANGFLOW_BASE = os.getenv("LANGFLOW_BASE_URL", "http://localhost:7860")
LANGFLOW_FLOW_ID = os.getenv("LANGFLOW_FLOW_ID")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY")

# 适配器高级参数（超时/重试）
ADAPTER_CONNECT_TIMEOUT = float(os.getenv("ADAPTER_CONNECT_TIMEOUT", "10"))
ADAPTER_READ_TIMEOUT = float(os.getenv("ADAPTER_READ_TIMEOUT", "30"))
ADAPTER_RETRY_MAX = int(os.getenv("ADAPTER_RETRY_MAX", "3"))
ADAPTER_RETRY_BASE = float(os.getenv("ADAPTER_RETRY_BASE", "0.5"))
ADAPTER_RETRY_MAX_BACKOFF = float(os.getenv("ADAPTER_RETRY_MAX_BACKOFF", "4"))

# /stream 总超时（包含整个生成）：0 或负数表示不限制
STREAM_TOTAL_TIMEOUT = float(os.getenv("STREAM_TOTAL_TIMEOUT", "300"))

redis: Optional[aioredis.Redis] = None

# —— 按工作流缓存适配器 —— #
_adapter_cache: Dict[str, LangFlowAdapter] = {}

# -------------------- 指标 --------------------
RUNS_STARTED = Counter("orchestrator_runs_started", "Runs started", ["workflow_id", "user"])
RUNS_COMPLETED = Counter("orchestrator_runs_completed", "Runs completed", ["workflow_id", "user"])
RUNS_FAILED = Counter("orchestrator_runs_failed", "Runs failed", ["workflow_id", "user"])
RATE_LIMIT_HITS = Counter("orchestrator_rate_limit_hits", "Rate limit hits", ["scope"])
SSE_TTFB = Histogram(
    "orchestrator_sse_ttfb_seconds",
    "SSE time-to-first-byte",
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5)
)

# -------------------- 工具函数 --------------------
def mk_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:12]}"

# -------------------- Auth 依赖 --------------------
class UserCtx(dict):
    @property
    def sub(self) -> str:
        return self.get("sub", "anon")

_jwks_client: Optional[PyJWKClient] = None

async def require_user(request: Request, authorization: str | None = Header(default=None)) -> UserCtx:
    if AUTH_MODE == "disabled":
        return UserCtx(sub="anon")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()

    options = {"verify_signature": True, "verify_exp": True}
    kwargs: Dict[str, Any] = {"algorithms": JWT_ALGS}
    if JWT_AUDIENCE:
        kwargs["audience"] = JWT_AUDIENCE
    if JWT_ISSUER:
        kwargs["issuer"] = JWT_ISSUER

    try:
        if AUTH_MODE == "hs256":
            if not JWT_SECRET:
                raise HTTPException(500, "JWT_SECRET not configured")
            payload = jwt.decode(token, JWT_SECRET, options=options, **kwargs)
        elif AUTH_MODE == "jwks":
            global _jwks_client
            if not JWT_JWKS_URL:
                raise HTTPException(500, "JWT_JWKS_URL not configured")
            if _jwks_client is None:
                _jwks_client = PyJWKClient(JWT_JWKS_URL)
            signing_key = _jwks_client.get_signing_key_from_jwt(token).key
            payload = jwt.decode(token, signing_key, options=options, **kwargs)
        else:
            raise HTTPException(500, f"Unsupported AUTH_MODE={AUTH_MODE}")
    except InvalidTokenError as e:
        raise HTTPException(401, f"Invalid token: {e}") from e
    except Exception as e:
        raise HTTPException(401, f"Auth failed: {e}") from e

    sub = payload.get("sub") or payload.get("uid") or payload.get("user_id") or "unknown"
    email = payload.get("email")
    roles = payload.get("roles") or payload.get("scope") or payload.get("scopes")
    return UserCtx(sub=sub, email=email, roles=roles, claims=payload)

# -------------------- 限流 --------------------
async def check_rate_limit(user: UserCtx, workflow_id: str):
    now_min = int(time.time() // 60)
    uid = user.sub or "anon"

    key_user = f"rl:user:{uid}:{now_min}"
    n_user = await redis.incr(key_user)
    if n_user == 1:
        await redis.expire(key_user, 70)
    if RL_USER_PER_MIN > 0 and n_user > RL_USER_PER_MIN:
        RATE_LIMIT_HITS.labels(scope="user").inc()
        raise HTTPException(status_code=429, detail="Rate limit exceeded (user/min)")

    key_wf = f"rl:user:{uid}:wf:{workflow_id}:{now_min}"
    n_wf = await redis.incr(key_wf)
    if n_wf == 1:
        await redis.expire(key_wf, 70)
    if RL_WORKFLOW_PER_MIN > 0 and n_wf > RL_WORKFLOW_PER_MIN:
        RATE_LIMIT_HITS.labels(scope="workflow").inc()
        raise HTTPException(status_code=429, detail="Rate limit exceeded (workflow/min)")

# -------------------- 适配器（按工作流） --------------------
async def get_adapter_for_workflow(workflow_id: str) -> LangFlowAdapter:
    if workflow_id in _adapter_cache:
        return _adapter_cache[workflow_id]

    # 从 DB 取配置；没有则回退到 env
    async with AsyncSessionLocal() as session:
        wf = await session.get(WfModel, workflow_id)

    if wf and wf.enabled:
        if wf.adapter != "langflow":
            raise HTTPException(501, f"Adapter '{wf.adapter}' not implemented yet")
        cfg = wf.config or {}
        base = cfg.get("base_url") or LANGFLOW_BASE
        fid = cfg.get("flow_id") or LANGFLOW_FLOW_ID
        key = cfg.get("api_key") or LANGFLOW_API_KEY
        if not fid:
            raise HTTPException(503, f"Workflow '{workflow_id}' has no flow_id configured")
    else:
        base = LANGFLOW_BASE
        fid = LANGFLOW_FLOW_ID
        key = LANGFLOW_API_KEY
        if not fid:
            raise HTTPException(503, "LangFlow adapter not configured (missing LANGFLOW_FLOW_ID ?)")

    adapter = LangFlowAdapter(
        base_url=base,
        flow_id=fid,
        api_key=key,
        connect_timeout=ADAPTER_CONNECT_TIMEOUT,
        read_timeout=ADAPTER_READ_TIMEOUT,
        retry_max=ADAPTER_RETRY_MAX,
        retry_base=ADAPTER_RETRY_BASE,
        retry_max_backoff=ADAPTER_RETRY_MAX_BACKOFF,
    )
    _adapter_cache[workflow_id] = adapter
    return adapter

# -------------------- 生命周期 --------------------
@app.on_event("startup")
async def startup():
    global redis
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    # 初始化 DB
    await init_db(Base.metadata)

    # 注册/更新默认工作流（wf_basic）
    if LANGFLOW_FLOW_ID:
        async with AsyncSessionLocal() as session:
            wf = await session.get(WfModel, "wf_basic")
            cfg = {"base_url": LANGFLOW_BASE, "flow_id": LANGFLOW_FLOW_ID}
            if LANGFLOW_API_KEY:
                cfg["api_key"] = LANGFLOW_API_KEY
            if not wf:
                session.add(WfModel(
                    workflow_id="wf_basic",
                    name="Basic Prompting (LangFlow)",
                    adapter="langflow",
                    config=cfg,
                    enabled=True
                ))
            else:
                wf.name = wf.name or "Basic Prompting (LangFlow)"
                wf.adapter = "langflow"
                wf.config = cfg
                wf.enabled = True
            await session.commit()
            logger.info("Default workflow 'wf_basic' is registered/updated.")

@app.on_event("shutdown")
async def shutdown():
    if redis:
        await redis.close()

# -------------------- 中间件：访问日志 --------------------
@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        dur = time.perf_counter() - start
        logger.info(json.dumps({
            "type": "access",
            "method": request.method,
            "path": request.url.path,
            "status": getattr(response, "status_code", 0),
            "duration_ms": round(dur * 1000, 2)
        }))

# -------------------- 健康检查 --------------------
@app.get("/healthz")
async def healthz():
    try:
        pong = await redis.ping()
        return {"ok": True, "redis": pong, "auth_mode": AUTH_MODE}
    except Exception as e:
        raise HTTPException(503, f"redis not ok: {e}")

# -------------------- 业务接口：Run --------------------
@app.post("/ai/agent/run")
async def run_agent(
    payload: dict,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: UserCtx = Depends(require_user),
):
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key required")

    workflow_id = str(payload.get("workflow_id") or "wf_basic")
    inputs = payload.get("inputs", {})
    params = payload.get("params", {})

    await check_rate_limit(user, workflow_id)

    cached = await redis.get(f"idem:{idempotency_key}:{user.sub}")
    if cached:
        return {"run_id": cached, "status": "queued"}

    run_id = mk_run_id()

    # Redis 短期态
    await redis.setex(f"idem:{idempotency_key}:{user.sub}", 24 * 3600, run_id)
    await redis.hset(
        f"run:{run_id}",
        mapping={
            "status": "queued",
            "created_at": str(asyncio.get_event_loop().time()),
            "user": user.sub,
            "workflow_id": workflow_id,
        },
    )
    await redis.setex(f"run:{run_id}:payload", 24 * 3600, json.dumps(payload))

    # DB 长期态
    async with AsyncSessionLocal() as session:
        session.add(RunModel(
            run_id=run_id,
            user=user.sub,
            workflow_id=workflow_id,
            status="queued",
            inputs=inputs,
            params=params
        ))
        await session.commit()

    RUNS_STARTED.labels(workflow_id=workflow_id, user=user.sub).inc()
    return JSONResponse({"run_id": run_id, "status": "queued"}, status_code=202)

@app.get("/ai/agent/{run_id}/status")
async def status(run_id: str, user: UserCtx = Depends(require_user)):
    st = await redis.hgetall(f"run:{run_id}")
    if not st:
        raise HTTPException(404, "run not found")
    owner = st.get("user")
    if owner and owner != user.sub and user.sub != "anon":
        raise HTTPException(403, "forbidden")
    return {"run_id": run_id, **st}

@app.get("/ai/agent/{run_id}/stream")
async def stream(run_id: str, user: UserCtx = Depends(require_user)):
    st = await redis.hgetall(f"run:{run_id}")
    if not st:
        raise HTTPException(404, "run not found")
    if st.get("user") and st["user"] != user.sub and user.sub != "anon":
        raise HTTPException(403, "forbidden")

    raw = await redis.get(f"run:{run_id}:payload")
    if not raw:
        raise HTTPException(404, "run payload not found")
    payload = json.loads(raw)

    workflow_id = st.get("workflow_id") or payload.get("workflow_id") or "wf_basic"
    inputs = payload.get("inputs", {})
    params = payload.get("params", {})

    adapter = await get_adapter_for_workflow(workflow_id)

    # —— TTFB 与 metrics 兜底 ——
    ttfb_start = time.perf_counter()
    ttfb_observed = False

    def _pick(obj: dict) -> str:
        try:
            t = (obj.get("outputs", [{}])[0]
                    .get("outputs", [{}])[0]
                    .get("results", {})
                    .get("message", {})
                    .get("text"))
            if t:
                return t
        except Exception:
            pass
        for k in ("text", "delta", "content", "token", "response", "output", "result"):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v
            if k == "delta" and isinstance(v, dict):
                c = v.get("content")
                if isinstance(c, str) and c.strip():
                    return c
        return ""

    async def inner_stream():
        yielded = False
        first_preview: Optional[str] = None

        try:
            async for chunk in adapter.stream(inputs, params):
                nonlocal ttfb_observed
                if not ttfb_observed:
                    SSE_TTFB.observe(time.perf_counter() - ttfb_start)
                    ttfb_observed = True

                cur = await redis.hget(f"run:{run_id}", "status")
                if cur == "canceled":
                    yield {"event": "ended", "data": json.dumps({"ok": False, "canceled": True})}
                    return

                text = str(chunk)
                if not first_preview and text.strip():
                    first_preview = text[:500]

                yielded = True
                yield {"event": "partial", "data": json.dumps({"text": text})}

            if not yielded:
                data = await adapter.run_once(inputs, params)
                if not ttfb_observed:
                    SSE_TTFB.observe(time.perf_counter() - ttfb_start)
                    ttfb_observed = True
                text = _pick(data) or "[no content]"
                first_preview = first_preview or text[:500]
                yield {"event": "partial", "data": json.dumps({"text": text})}

            await redis.hset(f"run:{run_id}", mapping={"status": "completed"})
            # DB 状态更新
            async with AsyncSessionLocal() as session:
                run = await session.get(RunModel, run_id)
                if run:
                    run.status = "completed"
                    if first_preview and not run.output_preview:
                        run.output_preview = first_preview
                await session.commit()

            RUNS_COMPLETED.labels(workflow_id=workflow_id, user=user.sub).inc()
            yield {"event": "ended", "data": json.dumps({"ok": True})}

        except UpstreamTimeout as e:
            await redis.hset(f"run:{run_id}", mapping={"status": "failed", "error": "upstream_timeout"})
            async with AsyncSessionLocal() as session:
                run = await session.get(RunModel, run_id)
                if run:
                    run.status = "failed"
                    run.error = "upstream_timeout"
                await session.commit()
            RUNS_FAILED.labels(workflow_id=workflow_id, user=user.sub).inc()
            yield {"event": "error", "data": json.dumps({"error": "upstream_timeout", "detail": str(e)})}

        except UpstreamError as e:
            await redis.hset(f"run:{run_id}", mapping={"status": "failed", "error": "upstream_error"})
            async with AsyncSessionLocal() as session:
                run = await session.get(RunModel, run_id)
                if run:
                    run.status = "failed"
                    run.error = "upstream_error"
                await session.commit()
            RUNS_FAILED.labels(workflow_id=workflow_id, user=user.sub).inc()
            yield {"event": "error", "data": json.dumps({"error": "upstream_error", "detail": str(e)})}

        except HTTPException as he:
            await redis.hset(f"run:{run_id}", mapping={"status": "failed", "error": str(he.detail)})
            async with AsyncSessionLocal() as session:
                run = await session.get(RunModel, run_id)
                if run:
                    run.status = "failed"
                    run.error = str(he.detail)
                await session.commit()
            RUNS_FAILED.labels(workflow_id=workflow_id, user=user.sub).inc()
            yield {"event": "error", "data": json.dumps({"error": he.detail})}

        except Exception as e:
            await redis.hset(f"run:{run_id}", mapping={"status": "failed", "error": str(e)})
            async with AsyncSessionLocal() as session:
                run = await session.get(RunModel, run_id)
                if run:
                    run.status = "failed"
                    run.error = str(e)
                await session.commit()
            RUNS_FAILED.labels(workflow_id=workflow_id, user=user.sub).inc()
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    async def gen():
        yield {"event": "started", "data": json.dumps({"run_id": run_id})}
        await redis.hset(f"run:{run_id}", mapping={"status": "streaming"})
        async with AsyncSessionLocal() as session:
            run = await session.get(RunModel, run_id)
            if run:
                run.status = "streaming"
            await session.commit()

        if STREAM_TOTAL_TIMEOUT and STREAM_TOTAL_TIMEOUT > 0:
            try:
                async with asyncio.timeout(STREAM_TOTAL_TIMEOUT):
                    async for ev in inner_stream():
                        yield ev
                    return
            except TimeoutError:
                await redis.hset(f"run:{run_id}", mapping={"status": "failed", "error": "stream_total_timeout"})
                async with AsyncSessionLocal() as session:
                    run = await session.get(RunModel, run_id)
                    if run:
                        run.status = "failed"
                        run.error = "stream_total_timeout"
                    await session.commit()
                RUNS_FAILED.labels(workflow_id=workflow_id, user=user.sub).inc()
                yield {"event": "error", "data": json.dumps({"error": "stream_total_timeout"})}
                return
        else:
            async for ev in inner_stream():
                yield ev

    return EventSourceResponse(gen())

@app.post("/ai/agent/{run_id}/cancel")
async def cancel(run_id: str, user: UserCtx = Depends(require_user)):
    st = await redis.hgetall(f"run:{run_id}")
    if not st:
        raise HTTPException(404, "run not found")
    if st.get("user") and st["user"] != user.sub and user.sub != "anon":
        raise HTTPException(403, "forbidden")

    await redis.hset(
        f"run:{run_id}",
        mapping={"status": "canceled", "canceled_at": str(asyncio.get_event_loop().time())},
    )
    async with AsyncSessionLocal() as session:
        run = await session.get(RunModel, run_id)
        if run:
            run.status = "canceled"
        await session.commit()
    return {"run_id": run_id, "status": "canceled"}

# -------------------- 业务接口：Workflows --------------------
@app.get("/ai/workflows")
async def list_workflows(user: UserCtx = Depends(require_user)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(WfModel.__table__.select().order_by(WfModel.workflow_id))
        rows = res.mappings().all()
        return [dict(r) for r in rows]

@app.post("/ai/workflows")
async def upsert_workflow(
    wf: Dict[str, Any] = Body(..., example={
        "workflow_id": "wf_basic",
        "name": "Basic Prompting (LangFlow)",
        "adapter": "langflow",
        "config": {"base_url": "http://localhost:7860", "flow_id": "xxx", "api_key": "optional"},
        "enabled": True
    }),
    user: UserCtx = Depends(require_user),
):
    required = ("workflow_id", "name", "adapter", "config")
    for k in required:
        if k not in wf:
            raise HTTPException(400, f"missing field: {k}")

    if wf["adapter"] != "langflow":
        raise HTTPException(501, f"Adapter '{wf['adapter']}' not implemented yet")

    async with AsyncSessionLocal() as session:
        existing = await session.get(WfModel, wf["workflow_id"])
        if not existing:
            session.add(WfModel(
                workflow_id=wf["workflow_id"],
                name=wf["name"],
                adapter=wf["adapter"],
                config=wf.get("config") or {},
                enabled=bool(wf.get("enabled", True))
            ))
        else:
            existing.name = wf["name"]
            existing.adapter = wf["adapter"]
            existing.config = wf.get("config") or {}
            existing.enabled = bool(wf.get("enabled", True))
        await session.commit()

    # 清缓存，让新配置立刻生效
    _adapter_cache.pop(wf["workflow_id"], None)
    return {"ok": True, "workflow_id": wf["workflow_id"]}
