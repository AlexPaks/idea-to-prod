import json
from typing import Any

from app.services.integrations.mcp_jsonrpc_client import (
    McpJsonRpcClient,
    McpJsonRpcError,
)


class JiraMcpError(Exception):
    """Raised when Jira MCP interaction fails."""


class JiraMcpClient:
    def __init__(
        self,
        server_url: str,
        tool_name: str = "jira",
        timeout_seconds: float = 30.0,
        arguments_template_json: str = "",
    ) -> None:
        self._tool_name = tool_name.strip()
        self._arguments_template = _parse_arguments_template(
            arguments_template_json,
            setting_name="JIRA_MCP_ARGUMENTS_TEMPLATE_JSON",
        )
        self._client = McpJsonRpcClient(
            server_url=server_url,
            timeout_seconds=timeout_seconds,
        )

        if not self._tool_name:
            raise JiraMcpError("JIRA_MCP_TOOL_NAME is required")

    def probe_connection(self, project_key: str = "") -> dict[str, Any]:
        try:
            probe = self._client.probe_tool(self._tool_name)
            if self._arguments_template is not None:
                rendered = _render_template(
                    self._arguments_template,
                    {
                        "project_key": project_key.strip(),
                    },
                )
                if not isinstance(rendered, dict):
                    raise JiraMcpError(
                        "JIRA_MCP_ARGUMENTS_TEMPLATE_JSON must render to a JSON object"
                    )
                self._client.call_tool(self._tool_name, rendered)
        except (McpJsonRpcError, ValueError) as error:
            raise JiraMcpError(str(error)) from error

        return {
            "tool_name": probe.tool_name,
            "argument_keys": probe.argument_keys,
            "available_tools": probe.available_tools,
            "tools_list_supported": probe.tools_list_supported,
        }


def _parse_arguments_template(
    arguments_template_json: str,
    setting_name: str,
) -> dict[str, Any] | None:
    raw = arguments_template_json.strip()
    if not raw:
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise JiraMcpError(f"{setting_name} must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise JiraMcpError(f"{setting_name} must be a JSON object")
    return parsed


def _render_template(value: Any, context: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _render_template(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [_render_template(item, context) for item in value]
    if isinstance(value, str):
        try:
            return value.format(**context)
        except KeyError as exc:
            raise JiraMcpError(
                "Template references unknown placeholder "
                f"'{exc.args[0]}' in Jira MCP arguments template"
            ) from exc
    return value

