"""
title: Langflow Deep Research (Streaming)
author: CerebraUI Team
version: 2.0.0
description: Execute Langflow Deep Research workflow with real-time streaming output
required_open_webui_version: 0.4.0
"""

import asyncio
import aiohttp
import json
import logging
from typing import Callable, Awaitable, Optional
from pydantic import BaseModel


log = logging.getLogger(__name__)


class Tools:
    def __init__(self):
        self.valves = self.Valves()

    class Valves(BaseModel):
        LANGFLOW_URL: str = "http://langflow:7860"
        FLOW_ID: str = "9671f43a-1943-4114-8a63-cf8a72309bb2"
        API_KEY: str = "sk-rr4GqyzgDLadZqzZTl24sYItQEcx1a3U6Z0TnnKxmEE"
        DEBUG: bool = True  # Set to True for detailed logging

    async def langflow_deep_research(
        self,
        input_value: str,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> str:
        """
        Execute Langflow Deep Research workflow with real-time streaming output.

        :param input_value: The research question or topic to investigate
        :return: Final research report with complete thinking process
        """

        url = f"{self.valves.LANGFLOW_URL}/api/v1/run/{self.valves.FLOW_ID}?stream=true"

        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
        }

        if self.valves.API_KEY:
            headers["x-api-key"] = self.valves.API_KEY

        payload = {
            "input_value": input_value,
            "input_type": "chat",
            "output_type": "chat",
        }

        collected_outputs = []
        buffer = ""
        accumulated_message = ""  # Track all messages for final output

        try:
            # Emit initial message
            if __event_emitter__:
                initial_msg = f"🔍 **Starting Deep Research:** {input_value}\n\n"
                accumulated_message += initial_msg
                await __event_emitter__({
                    "type": "message",
                    "data": {"content": initial_msg}
                })

            # Make streaming request
            timeout = aiohttp.ClientTimeout(total=600)  # 10 minutes
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"❌ Error: HTTP {response.status} - {error_text[:200]}"
                        log.error(error_msg)
                        return error_msg

                    log.info(f"Langflow streaming response started for: {input_value}")
                    if self.valves.DEBUG:
                        log.info(f"Response status: {response.status}")
                        log.info(f"Response headers: {dict(response.headers)}")

                    # Read stream chunk by chunk with smaller buffer to reduce latency
                    chunk_count = 0
                    current_message_text = ""  # Accumulate token chunks
                    seen_message_ids = set()  # Track processed message IDs to avoid duplicates
                    current_message_id = None  # Track current streaming message
                    emitted_headers = set()  # Track which message IDs we've emitted headers for
                    message_texts = {}  # Track last seen text for each message_id to compute diffs

                    async for chunk_bytes in response.content.iter_any():
                        chunk_count += 1
                        try:
                            chunk = chunk_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            log.warning("Failed to decode chunk")
                            continue

                        buffer += chunk
                        lines = buffer.split("\n")
                        buffer = lines[-1]  # Keep incomplete line in buffer

                        # Process complete lines
                        for line in lines[:-1]:
                            line = line.strip()
                            if not line:
                                continue

                            # Try to parse as JSON (Langflow returns JSON lines, not SSE)
                            try:
                                data = json.loads(line)

                                if isinstance(data, dict) and "event" in data:
                                    event_type = data.get("event")
                                    event_data = data.get("data", {})

                                    # Log ALL event types for debugging
                                    if self.valves.DEBUG:
                                        log.info(f"Received event: {event_type}")

                                    # Handle token events - real-time LLM output
                                    if event_type == "token":
                                        token_chunk = event_data.get("chunk", "")
                                        message_id = event_data.get("id")

                                        if token_chunk:
                                            # Check if this is a new message (new message_id)
                                            is_new_message = message_id and message_id != current_message_id

                                            if is_new_message:
                                                # New message starting - emit header if not already done
                                                if message_id not in emitted_headers:
                                                    header = f"\n\n**AI Response:**\n\n"
                                                    accumulated_message += header
                                                    if __event_emitter__:
                                                        await __event_emitter__({
                                                            "type": "message",
                                                            "data": {"content": header}
                                                        })
                                                    emitted_headers.add(message_id)
                                                    log.info(f"New AI message started (ID: {message_id})")

                                                current_message_id = message_id
                                                current_message_text = ""

                                            current_message_text += token_chunk
                                            accumulated_message += token_chunk

                                            # Emit token in real-time
                                            if __event_emitter__:
                                                await __event_emitter__({
                                                    "type": "message",
                                                    "data": {"content": token_chunk}
                                                })

                                            if self.valves.DEBUG:
                                                log.info(f"Token: {token_chunk}")

                                    # Handle add_message events
                                    elif event_type == "add_message":
                                        sender = event_data.get("sender", "")
                                        text = event_data.get("text", "")
                                        sender_name = event_data.get("sender_name", sender)
                                        message_id = event_data.get("id")

                                        # Debug log for add_message events
                                        if self.valves.DEBUG:
                                            log.info(f"add_message: sender={sender}, text_len={len(text)}, msg_id={message_id}")

                                        # Handle User messages
                                        if sender == "User" and text:
                                            # Only process first occurrence of user message
                                            if message_id not in seen_message_ids:
                                                # User message with separator
                                                msg_chunk = f"\n\n---\n\n**User Query:** {text}\n\n"
                                                accumulated_message += msg_chunk
                                                if __event_emitter__:
                                                    await __event_emitter__({
                                                        "type": "message",
                                                        "data": {"content": msg_chunk}
                                                    })
                                                log.info(f"User query: {text[:100]}...")
                                                seen_message_ids.add(message_id)

                                        # Handle Machine messages - these stream via text updates
                                        elif sender == "Machine" and text and message_id:
                                            # Emit header only once for this message
                                            if message_id not in emitted_headers:
                                                header = f"\n\n**{sender_name} Response:**\n\n"
                                                accumulated_message += header
                                                if __event_emitter__:
                                                    await __event_emitter__({
                                                        "type": "message",
                                                        "data": {"content": header}
                                                    })
                                                emitted_headers.add(message_id)
                                                log.info(f"New {sender_name} message started (ID: {message_id})")

                                            # Calculate text difference (incremental update)
                                            last_text = message_texts.get(message_id, "")

                                            if text != last_text:
                                                # Get the new text portion
                                                if text.startswith(last_text):
                                                    # Text is appended - get the new part
                                                    new_text = text[len(last_text):]
                                                else:
                                                    # Text completely changed - use full text
                                                    new_text = text

                                                if new_text:
                                                    # Emit the incremental text
                                                    accumulated_message += new_text
                                                    if __event_emitter__:
                                                        await __event_emitter__({
                                                            "type": "message",
                                                            "data": {"content": new_text}
                                                        })

                                                    if self.valves.DEBUG:
                                                        log.info(f"Streaming increment: +{len(new_text)} chars")

                                                # Update last seen text
                                                message_texts[message_id] = text

                                    # Handle end event - final results
                                    elif event_type == "end":
                                        # Add completion marker
                                        completion_msg = "\n\n✅ **Research Completed**\n\n"
                                        accumulated_message += completion_msg
                                        if __event_emitter__:
                                            await __event_emitter__({
                                                "type": "message",
                                                "data": {"content": completion_msg}
                                            })

                                        result = event_data.get("result", {})
                                        if "outputs" in result:
                                            for output_item in result["outputs"]:
                                                # Navigate the nested structure
                                                for output in output_item.get("outputs", []):
                                                    results = output.get("results", {})
                                                    message = results.get("message", {})
                                                    data_obj = message.get("data", {})
                                                    text = data_obj.get("text", "")

                                                    if text:
                                                        log.info(f"Final output: {text[:200]}...")
                                                        collected_outputs.append(text)

                                        # Reset current message for next potential response
                                        current_message_text = ""

                                    # Log unhandled event types
                                    else:
                                        if self.valves.DEBUG:
                                            log.warning(f"Unhandled event type: {event_type}")

                            except json.JSONDecodeError as e:
                                # Not valid JSON - might be plain text
                                if self.valves.DEBUG:
                                    log.warning(f"Failed to parse JSON: {line[:100]} - {e}")

            log.info(f"Langflow research completed. Received {chunk_count} chunks")

            if self.valves.DEBUG and len(collected_outputs) == 0 and not accumulated_message:
                log.warning("No outputs collected! Check Langflow logs for errors.")
                log.warning(f"Last buffer content: {buffer[:200] if buffer else 'empty'}")

            # Return the complete accumulated message that includes all thinking process
            # This will be saved in the chat history
            if accumulated_message:
                return accumulated_message
            elif collected_outputs:
                return "\n\n".join(collected_outputs)
            else:
                return "✅ Research workflow completed."

        except asyncio.TimeoutError:
            error_msg = "⏱️ Error: Research timed out after 10 minutes"
            log.error(error_msg)
            return error_msg
        except aiohttp.ClientError as e:
            error_msg = f"🔌 Error: Network error - {str(e)}"
            log.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Error during research: {str(e)}"
            log.error(error_msg)
            import traceback
            log.error(traceback.format_exc())
            return error_msg
