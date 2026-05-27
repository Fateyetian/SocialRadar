"""TikHub MCP SSE client — handles initialize, tools/list, tools/call over SSE."""

import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PlatformTool:
    """Represents a known tool for a platform with its default params."""

    name: str
    params: dict[str, Any]


class TikHubClient:
    """Thin SSE-aware client for a TikHub platform MCP endpoint."""

    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.session_id: str | None = None
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

    def initialize(self) -> str:
        """Send MCP initialize request, return session ID."""
        resp = self._client.post(
            self.endpoint,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "social-radar", "version": "1.0"},
                },
            },
        )
        self.session_id = self._parse_session_id(resp)
        return self.session_id

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a tool on the platform, return JSON string result."""
        if not self.session_id:
            self.initialize()

        resp = self._client.post(
            self.endpoint,
            headers={"Mcp-Session-Id": self.session_id},
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            },
        )
        return self._parse_tool_result(resp)

    def search(self, tool_name: str, query: str, extra_params: dict[str, Any] | None = None) -> str:
        """Convenience: call a search tool with keyword."""
        params = {"keyword": query}
        if extra_params:
            params.update(extra_params)
        return self.call_tool(tool_name, params)

    def _parse_session_id(self, resp: httpx.Response) -> str:
        session_id = resp.headers.get("mcp-session-id", "")
        if not session_id:
            # Try reading SSE stream
            for line in resp.text.splitlines():
                if line.startswith("data:") and "result" in line:
                    # It's in the response body; but session is in headers
                    pass
        return session_id

    def _parse_tool_result(self, resp: httpx.Response) -> str:
        """Extract the inner JSON text from MCP SSE response.

        TikHub returns: {"result": {"content": [{"type": "text", "text": "{...}"}]}}
        We extract content[0].text — the actual platform API JSON string.
        """
        text = resp.text
        for line in text.splitlines():
            if line.startswith("data:"):
                chunk = line[len("data:"):].strip()
                try:
                    data = json.loads(chunk)
                    if "error" in data:
                        return json.dumps({"error": data["error"]}, ensure_ascii=False)
                    if "result" in data:
                        result = data["result"]
                        content_list = result.get("content", [])
                        if content_list and content_list[0].get("type") == "text":
                            # Return the inner JSON string from TikHub API
                            return content_list[0].get("text", json.dumps(result, ensure_ascii=False))
                        return json.dumps(result, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
        return text

    def close(self):
        self._client.close()
