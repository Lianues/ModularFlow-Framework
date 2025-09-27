"""
轻量级 API 客户端
- 统一通过 HTTP 调用后端注册的 API（@register_api）
- 默认直连本机 API 网关: http://localhost:8050
- 路由规范：根据注册来源自动在路径中添加 '/modules' 或 '/workflow'
  • api/modules/* => /api/modules/...
  • api/workflow/* => /api/workflow/...
- 客户端支持 namespace 参数选择路径前缀；若不指定，将按顺序尝试 modules -> workflow

用法示例:
    from core.api_client import ApiClient, call_api

    # 直接使用全局客户端
    resp = call_api("web_server.restart_project", {"project_name": "ProjectManager"})  # 自动尝试 /modules 和 /workflow
    print(resp)

    # 指定命名空间
    resp = call_api("image_binding.embed_files_to_image", {"image_path": "...", "file_paths": [...]}, namespace="workflow")

    # 或者自定义客户端实例
    client = ApiClient(base_url="http://127.0.0.1:8050", api_prefix="/api", timeout=15)
    resp = client.call("project_manager.get_status", {"project_name": "ProjectManager"}, method="GET", namespace="modules")
"""

from typing import Any, Dict, Optional, Union, Tuple, List
import requests
from urllib.parse import urljoin


class ApiClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8050",
        api_prefix: str = "/api",
        timeout: Union[int, float] = 15,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        """
        初始化 API 客户端
        """
        self.base_url = base_url.rstrip("/")
        self.api_prefix = api_prefix if api_prefix.startswith("/") else f"/{api_prefix}"
        self.timeout = timeout
        self.session = requests.Session()
        self.default_headers = default_headers or {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def set_auth(self, token: Optional[str]) -> None:
        """
        设置鉴权头（Bearer Token）
        """
        if token:
            self.default_headers["Authorization"] = f"Bearer {token}"
        else:
            self.default_headers.pop("Authorization", None)

    def _paths_for(self, name: str, namespace: Optional[str]) -> List[str]:
        """
        根据函数名与命名空间生成可能的路径列表
        - namespace 可为 'modules' | 'workflow' | None
        - 当为 None 时，按 modules -> workflow 顺序尝试
        """
        name_path = name.replace(".", "/").lstrip("/")
        if namespace is None:
            return [
                f"{self.api_prefix}/modules/{name_path}",
                f"{self.api_prefix}/workflow/{name_path}",
            ]
        ns = namespace.strip("/").lower()
        if ns not in ("modules", "workflow"):
            # 非法 namespace 时仍按自动策略尝试
            return [
                f"{self.api_prefix}/modules/{name_path}",
                f"{self.api_prefix}/workflow/{name_path}",
            ]
        return [f"{self.api_prefix}/{ns}/{name_path}"]

    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        h = dict(self.default_headers or {})
        if headers:
            h.update(headers)
        return h

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Any]:
        """
        统一请求入口，返回 (status_code, parsed_body)
        优先解析为 JSON，不可解析时返回文本
        """
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        h = self._merge_headers(headers)
        try:
            if files:
                # 使用 multipart/form-data；移除 JSON Content-Type
                h.pop("Content-Type", None)
                resp = self.session.request(
                    method.upper(), url, params=params, files=files, data=json, headers=h, timeout=self.timeout
                )
            else:
                resp = self.session.request(
                    method.upper(), url, params=params, json=json, headers=h, timeout=self.timeout
                )
        except requests.RequestException as e:
            return 0, {"error_code": "NETWORK_ERROR", "message": str(e)}

        status = resp.status_code
        body: Any
        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        # 标准化错误输出
        if status >= 400:
            if isinstance(body, dict):
                body.setdefault("error_code", "HTTP_ERROR")
                body.setdefault("status", status)
            else:
                body = {"error_code": "HTTP_ERROR", "status": status, "message": str(body)}
        return status, body

    def call(
        self,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> Any:
        """
        通过函数名调用 API
        - namespace: 'modules' | 'workflow' | None(自动尝试)
        """
        paths = self._paths_for(name, namespace)
        last_status = None
        last_body = None
        for path in paths:
            if method.upper() == "GET":
                status, body = self.request("GET", path, params=payload, headers=headers)
            else:
                status, body = self.request("POST", path, json=payload, headers=headers, files=files)
            # 成功，或非 404 错误则直接返回
            if status and status < 400:
                return body
            last_status, last_body = status, body
            # 仅在 404 时尝试下一个命名空间
            if status != 404:
                break
        return last_body

    def call_get(
        self,
        name: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        namespace: Optional[str] = None,
    ) -> Any:
        paths = self._paths_for(name, namespace)
        last_status = None
        last_body = None
        for path in paths:
            status, body = self.request("GET", path, params=params, headers=headers)
            if status and status < 400:
                return body
            last_status, last_body = status, body
            if status != 404:
                break
        return last_body

    def call_post(
        self,
        name: str,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
    ) -> Any:
        paths = self._paths_for(name, namespace)
        last_status = None
        last_body = None
        for path in paths:
            status, body = self.request("POST", path, json=payload, headers=headers, files=files)
            if status and status < 400:
                return body
            last_status, last_body = status, body
            if status != 404:
                break
        return last_body

    def close(self) -> None:
        try:
            self.session.close()
        except Exception:
            pass


# 全局默认客户端
_default_client: Optional[ApiClient] = None

def get_client(
    base_url: Optional[str] = None,
    api_prefix: Optional[str] = None,
    timeout: Optional[Union[int, float]] = None,
) -> ApiClient:
    """
    获取或创建全局默认客户端
    """
    global _default_client
    if _default_client is None:
        _default_client = ApiClient(
            base_url=base_url or "http://localhost:8050",
            api_prefix=api_prefix or "/api",
            timeout=timeout or 15,
        )
    return _default_client

def call_api(
    name: str,
    payload: Optional[Dict[str, Any]] = None,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    files: Optional[Dict[str, Any]] = None,
    namespace: Optional[str] = None,
) -> Any:
    """
    使用全局客户端按函数名调用 API
    - namespace: 'modules' | 'workflow' | None(自动)
    """
    client = get_client()
    return client.call(name, payload=payload, method=method, headers=headers, files=files, namespace=namespace)


if __name__ == "__main__":
    # 简单的自检：健康检查
    client = get_client()
    status, body = client.request("GET", "/api/health")
    print("health:", status, body)
    # 示例调用（若注册了对应 API）
    try:
        print(call_api("api_gateway.info", method="GET", namespace="modules"))
    except Exception as e:
        print("call failed:", e)