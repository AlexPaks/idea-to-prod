import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)


class GoogleDriveMcpError(Exception):
    """Raised when Google Drive MCP interaction fails."""


@dataclass(frozen=True)
class GoogleDriveDocumentRef:
    document_id: str | None
    document_url: str | None
    document_name: str | None
    raw_result: dict[str, Any]


class GoogleDriveMcpClient:
    def __init__(
        self,
        server_url: str,
        tool_name: str = "create_document",
        read_tool_name: str = "get_document",
        folder_id: str = "",
        timeout_seconds: float = 30.0,
        arguments_template_json: str = "",
        read_arguments_template_json: str = "",
    ) -> None:
        self._server_url = server_url.strip()
        self._tool_name = tool_name.strip()
        self._read_tool_name = read_tool_name.strip()
        self._folder_id = folder_id.strip()
        self._timeout_seconds = timeout_seconds
        self._session_id = ""
        self._is_initialized = False
        self._request_id = 0
        self._tool_property_names: set[str] | None = None
        self._read_tool_property_names: set[str] | None = None

        if not self._server_url:
            raise GoogleDriveMcpError("GOOGLE_DRIVE_MCP_URL is required")
        if not self._tool_name:
            raise GoogleDriveMcpError("GOOGLE_DRIVE_MCP_TOOL_NAME is required")
        if not self._read_tool_name:
            raise GoogleDriveMcpError("GOOGLE_DRIVE_MCP_READ_TOOL_NAME is required")

        self._arguments_template = self._parse_arguments_template(
            arguments_template_json,
            setting_name="GOOGLE_DRIVE_MCP_ARGUMENTS_TEMPLATE_JSON",
        )
        self._read_arguments_template = self._parse_arguments_template(
            read_arguments_template_json,
            setting_name="GOOGLE_DRIVE_MCP_READ_ARGUMENTS_TEMPLATE_JSON",
        )

    def create_high_level_design_document(
        self,
        title: str,
        content: str,
        project_name: str,
        project_id: str,
        run_id: str,
    ) -> GoogleDriveDocumentRef:
        self._ensure_initialized()
        self._ensure_tool_schema_loaded()

        arguments = self._build_tool_arguments(
            title=title,
            content=content,
            project_name=project_name,
            project_id=project_id,
            run_id=run_id,
        )

        result = self._rpc(
            "tools/call",
            {
                "name": self._tool_name,
                "arguments": arguments,
            },
        )
        if not isinstance(result, dict):
            raise GoogleDriveMcpError(
                "Google Drive MCP returned invalid tools/call result payload"
            )

        doc_ref = _extract_document_ref(result)
        logger.info(
            "Saved High-Level Design to Google Drive via MCP: run_id=%s doc_id=%s url=%s",
            run_id,
            doc_ref.document_id,
            doc_ref.document_url,
        )
        return doc_ref

    def probe_connection(self) -> dict[str, Any]:
        self._ensure_initialized()
        self._ensure_tool_schema_loaded()
        self._ensure_read_tool_schema_loaded()

        if self._tool_property_names is not None and not self._tool_property_names:
            logger.info(
                "MCP connection probe completed with no discovered schema properties for tool '%s'",
                self._tool_name,
            )
        if self._read_tool_property_names is not None and not self._read_tool_property_names:
            logger.info(
                "MCP connection probe completed with no discovered schema properties for read tool '%s'",
                self._read_tool_name,
            )

        return {
            "create_tool_name": self._tool_name,
            "create_argument_keys": sorted(self._tool_property_names or set()),
            "read_tool_name": self._read_tool_name,
            "read_argument_keys": sorted(self._read_tool_property_names or set()),
        }

    def read_document_content(
        self,
        document_id: str | None,
        document_url: str | None,
        project_id: str | None = None,
        run_id: str | None = None,
    ) -> str:
        if not (document_id or document_url):
            raise GoogleDriveMcpError(
                "Either document_id or document_url is required to read a Google document"
            )

        self._ensure_initialized()
        self._ensure_read_tool_schema_loaded()

        arguments = self._build_read_arguments(
            document_id=document_id,
            document_url=document_url,
            project_id=project_id,
            run_id=run_id,
        )
        result = self._rpc(
            "tools/call",
            {
                "name": self._read_tool_name,
                "arguments": arguments,
            },
        )
        if not isinstance(result, dict):
            raise GoogleDriveMcpError("Google Drive MCP read tool returned invalid result payload")

        extracted = _extract_document_content(result)
        if not extracted.strip():
            raise GoogleDriveMcpError("Google Drive MCP read tool returned empty document content")
        return extracted.strip()

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
        except GoogleDriveMcpError as exc:
            lowered = str(exc).lower()
            if "method not found" not in lowered and "not found" not in lowered:
                raise
            logger.info("MCP server did not require explicit initialize; proceeding")

        self._is_initialized = True

    def _ensure_tool_schema_loaded(self) -> None:
        if self._tool_property_names is not None:
            return

        self._tool_property_names = set()

        try:
            result = self._rpc("tools/list", {})
        except GoogleDriveMcpError:
            logger.info(
                "Could not load MCP tool schema; defaulting argument keys for '%s'",
                self._tool_name,
            )
            return

        if not isinstance(result, dict):
            return

        tools = result.get("tools")
        if not isinstance(tools, list):
            return

        for tool in tools:
            if not isinstance(tool, dict):
                continue
            if tool.get("name") != self._tool_name:
                continue
            input_schema = tool.get("inputSchema")
            if not isinstance(input_schema, dict):
                return
            properties = input_schema.get("properties")
            if not isinstance(properties, dict):
                return
            self._tool_property_names = {str(key) for key in properties.keys()}
            return

    def _ensure_read_tool_schema_loaded(self) -> None:
        if self._read_tool_property_names is not None:
            return

        self._read_tool_property_names = set()

        try:
            result = self._rpc("tools/list", {})
        except GoogleDriveMcpError:
            logger.info(
                "Could not load MCP tool schema; defaulting argument keys for read tool '%s'",
                self._read_tool_name,
            )
            return

        if not isinstance(result, dict):
            return

        tools = result.get("tools")
        if not isinstance(tools, list):
            return

        for tool in tools:
            if not isinstance(tool, dict):
                continue
            if tool.get("name") != self._read_tool_name:
                continue
            input_schema = tool.get("inputSchema")
            if not isinstance(input_schema, dict):
                return
            properties = input_schema.get("properties")
            if not isinstance(properties, dict):
                return
            self._read_tool_property_names = {str(key) for key in properties.keys()}
            return

    def _build_tool_arguments(
        self,
        title: str,
        content: str,
        project_name: str,
        project_id: str,
        run_id: str,
    ) -> dict[str, Any]:
        context = {
            "title": title,
            "content": content,
            "project_name": project_name,
            "project_id": project_id,
            "run_id": run_id,
            "folder_id": self._folder_id,
        }

        if self._arguments_template is not None:
            rendered = _render_template(self._arguments_template, context)
            if not isinstance(rendered, dict):
                raise GoogleDriveMcpError(
                    "GOOGLE_DRIVE_MCP_ARGUMENTS_TEMPLATE_JSON must render to a JSON object"
                )
            return rendered

        return self._build_default_arguments(title=title, content=content)

    def _build_read_arguments(
        self,
        document_id: str | None,
        document_url: str | None,
        project_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        context = {
            "document_id": document_id or "",
            "document_url": document_url or "",
            "project_id": project_id or "",
            "run_id": run_id or "",
        }

        if self._read_arguments_template is not None:
            rendered = _render_template(self._read_arguments_template, context)
            if not isinstance(rendered, dict):
                raise GoogleDriveMcpError(
                    "GOOGLE_DRIVE_MCP_READ_ARGUMENTS_TEMPLATE_JSON must render to a JSON object"
                )
            return rendered

        property_names = self._read_tool_property_names or set()
        id_key = _pick_first_key(
            property_names,
            ["document_id", "documentId", "file_id", "fileId", "id"],
        )
        url_key = _pick_first_key(
            property_names,
            ["document_url", "documentUrl", "url", "link", "webViewLink"],
        )

        payload: dict[str, Any] = {}
        if document_id:
            payload[id_key or "document_id"] = document_id
        if document_url:
            payload[url_key or "document_url"] = document_url

        if not payload:
            raise GoogleDriveMcpError(
                "Read tool arguments could not be built because document reference is empty"
            )
        return payload

    def _build_default_arguments(self, title: str, content: str) -> dict[str, Any]:
        property_names = self._tool_property_names or set()
        title_key = _pick_first_key(
            property_names,
            ["title", "name", "document_title", "file_name", "filename"],
        )
        content_key = _pick_first_key(
            property_names,
            [
                "content",
                "body",
                "text",
                "markdown",
                "document_content",
                "initial_content",
                "initialContent",
            ],
        )
        folder_key = _pick_first_key(
            property_names,
            [
                "folder_id",
                "folderId",
                "parent_id",
                "parentId",
                "directory_id",
                "directoryId",
            ],
        )

        payload: dict[str, Any] = {
            (title_key or "title"): title,
            (content_key or "content"): content,
        }
        if self._folder_id and folder_key:
            payload[folder_key] = self._folder_id

        return payload

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
            raise GoogleDriveMcpError(
                f"MCP HTTP error {exc.code} while calling '{method}': {err_body}"
            ) from exc
        except error.URLError as exc:
            raise GoogleDriveMcpError(
                f"MCP network error while calling '{method}': {exc}"
            ) from exc

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise GoogleDriveMcpError(
                f"MCP returned non-JSON response for '{method}'"
            ) from exc

        if not isinstance(parsed, dict):
            raise GoogleDriveMcpError(f"MCP returned invalid payload type for '{method}'")

        error_payload = parsed.get("error")
        if isinstance(error_payload, dict):
            message = str(error_payload.get("message", "Unknown MCP error"))
            code = error_payload.get("code")
            raise GoogleDriveMcpError(
                f"MCP call failed for '{method}' (code={code}): {message}"
            )

        result = parsed.get("result")
        if not isinstance(result, dict):
            raise GoogleDriveMcpError(f"MCP result missing for '{method}'")
        return result

    def _parse_arguments_template(
        self,
        arguments_template_json: str,
        setting_name: str,
    ) -> dict[str, Any] | None:
        raw = arguments_template_json.strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GoogleDriveMcpError(
                f"{setting_name} must be valid JSON"
            ) from exc
        if not isinstance(parsed, dict):
            raise GoogleDriveMcpError(
                f"{setting_name} must be a JSON object"
            )
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
            raise GoogleDriveMcpError(
                "Template references unknown placeholder "
                f"'{exc.args[0]}' in Google Drive MCP arguments template"
            ) from exc
    return value


def _pick_first_key(candidates: set[str], preferred: list[str]) -> str | None:
    for key in preferred:
        if key in candidates:
            return key
    return None


def _extract_document_ref(result: dict[str, Any]) -> GoogleDriveDocumentRef:
    values = list(_iter_dict_values(result))
    urls = [value for value in values if isinstance(value, str) and _is_http_url(value)]
    url = _pick_first_google_docs_url(urls) or _pick_first(urls)

    text_urls: list[str] = []
    for value in values:
        if isinstance(value, str):
            text_urls.extend(_extract_urls_from_text(value))
    if url is None and text_urls:
        url = _pick_first_google_docs_url(text_urls) or _pick_first(text_urls)

    doc_id = _find_by_keys(
        result,
        {
            "document_id",
            "documentId",
            "file_id",
            "fileId",
            "id",
        },
    )
    if not isinstance(doc_id, str):
        doc_id = None
    if doc_id is None and isinstance(url, str):
        doc_id = _extract_doc_id_from_url(url)

    doc_name = _find_by_keys(
        result,
        {
            "title",
            "name",
            "document_name",
            "documentName",
        },
    )
    if not isinstance(doc_name, str):
        doc_name = None

    return GoogleDriveDocumentRef(
        document_id=doc_id,
        document_url=url,
        document_name=doc_name,
        raw_result=result,
    )


def _extract_document_content(result: dict[str, Any]) -> str:
    direct_content = _find_by_keys(
        result,
        {
            "document_content",
            "documentContent",
            "content",
            "text",
            "body",
            "markdown",
        },
    )
    if isinstance(direct_content, str) and direct_content.strip():
        return direct_content

    content_node = result.get("content")
    if isinstance(content_node, list):
        text_chunks: list[str] = []
        for item in content_node:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                text_chunks.append(text.strip())
        if text_chunks:
            return "\n\n".join(text_chunks)

    all_texts = [
        value
        for value in _iter_dict_values(result)
        if isinstance(value, str) and value.strip()
    ]
    return "\n\n".join(all_texts)


def _iter_dict_values(value: Any):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _iter_dict_values(nested)
        return
    if isinstance(value, list):
        for nested in value:
            yield from _iter_dict_values(nested)
        return
    yield value


def _find_by_keys(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        for key in keys:
            if key in value:
                return value[key]
        for nested in value.values():
            found = _find_by_keys(nested, keys)
            if found is not None:
                return found
    if isinstance(value, list):
        for nested in value:
            found = _find_by_keys(nested, keys)
            if found is not None:
                return found
    return None


def _is_http_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _pick_first(values: list[str]) -> str | None:
    return values[0] if values else None


def _pick_first_google_docs_url(values: list[str]) -> str | None:
    for value in values:
        if "docs.google.com" in value:
            return value
    return None


def _extract_urls_from_text(value: str) -> list[str]:
    return re.findall(r"https?://[^\s\)\]]+", value)


def _extract_doc_id_from_url(url: str) -> str | None:
    match = re.search(r"/d/([a-zA-Z0-9_-]{10,})", url)
    if not match:
        return None
    return match.group(1)
