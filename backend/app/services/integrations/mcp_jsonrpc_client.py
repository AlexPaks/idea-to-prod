import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)


class McpJsonRpcError(Exception):
    """Raised when MCP JSON-RPC interaction fails."""


@dataclass(frozen=True)
class McpToolProbe:
    tool_name: str
    argument_keys: list[str]
    available_tools: list[str]
    tools_list_supported: bool


class McpJsonRpcClient:
    def __init__(self, server_url: str, timeout_seconds: float = 30.0) -> None:
        self._server_url = server_url.strip()
        self._timeout_seconds = timeout_seconds
        self._session_id = ""
        self._is_initialized = False
        self._request_id = 0

        if not self._server_url:
            raise McpJsonRpcError("MCP server_url is required")

    def probe_tool(self, tool_name: str) -> McpToolProbe:
        if not tool_name.strip():
            raise McpJsonRpcError("MCP tool_name is required")

        self._ensure_initialized()

        try:
            tools = self.list_tools()
        except McpJsonRpcError:
            logger.info("MCP tools/list is unavailable; continuing without tool schema")
            return McpToolProbe(
                tool_name=tool_name,
                argument_keys=[],
                available_tools=[],
                tools_list_supported=False,
            )

        available_tools = [item.get("name", "") for item in tools if isinstance(item, dict)]
        normalized_available_tools = [
            str(item).strip() for item in available_tools if str(item).strip()
        ]

        matching_tool = None
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            if str(tool.get("name", "")).strip() == tool_name:
                matching_tool = tool
                break

        if matching_tool is None:
            raise McpJsonRpcError(
                f"MCP tool '{tool_name}' was not found. Available tools: "
                + ", ".join(normalized_available_tools or ["<none>"])
            )

        argument_keys: list[str] = []
        input_schema = matching_tool.get("inputSchema")
        if isinstance(input_schema, dict):
            properties = input_schema.get("properties")
            if isinstance(properties, dict):
                argument_keys = sorted(str(key) for key in properties.keys())

        return McpToolProbe(
            tool_name=tool_name,
            argument_keys=argument_keys,
            available_tools=normalized_available_tools,
            tools_list_supported=True,
        )

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not tool_name.strip():
            raise McpJsonRpcError("MCP tool_name is required")
        if not isinstance(arguments, dict):
            raise McpJsonRpcError("MCP tool arguments must be a JSON object")

        self._ensure_initialized()
        return self._rpc(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._rpc("tools/list", {})
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise McpJsonRpcError("MCP tools/list returned invalid 'tools' payload")
        return [tool for tool in tools if isinstance(tool, dict)]

    def _ensure_initialized(self) -> None:
        if self._is_initialized:
            return

        init_payload = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "idea-to-prod-backend",
                "version": "0.1.0",
            },
        }

        try:
            self._rpc("initialize", init_payload)
        except McpJsonRpcError as exc:
            lowered = str(exc).lower()
            if "method not found" not in lowered and "not found" not in lowered:
                raise
            logger.info("MCP server did not require explicit initialize; proceeding")

        self._is_initialized = True

    def _rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        http_request = request.Request(
            self._server_url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                session_id = response.headers.get("Mcp-Session-Id")
                if isinstance(session_id, str) and session_id.strip():
                    self._session_id = session_id.strip()
        except error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise McpJsonRpcError(
                f"MCP HTTP error {exc.code} while calling '{method}': {err_body}"
            ) from exc
        except error.URLError as exc:
            raise McpJsonRpcError(
                f"MCP network error while calling '{method}': {exc}"
            ) from exc

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise McpJsonRpcError(
                f"MCP returned non-JSON response for '{method}'"
            ) from exc

        if not isinstance(parsed, dict):
            raise McpJsonRpcError(f"MCP returned invalid payload type for '{method}'")

        error_payload = parsed.get("error")
        if isinstance(error_payload, dict):
            message = str(error_payload.get("message", "Unknown MCP error"))
            code = error_payload.get("code")
            raise McpJsonRpcError(
                f"MCP call failed for '{method}' (code={code}): {message}"
            )

        result = parsed.get("result")
        if not isinstance(result, dict):
            raise McpJsonRpcError(f"MCP result missing for '{method}'")
        return result

