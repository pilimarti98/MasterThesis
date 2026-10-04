from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests


@dataclass
class Server:
    name: str
    base_url: str
    auth_token: Optional[str] = None


@dataclass
class ApiClient:
    server: Server
    default_headers: Dict[str, str] = field(default_factory=dict)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:

        if not path:
            raise ValueError("Path is required.")

        if params is None:
            raise ValueError("Parameters are required.")

        request_headers = {
            **self.default_headers,
            **(headers or {}),
        }

        # Authorization is optional
        if self.server.auth_token:
            request_headers["Authorization"] = (
                f"Bearer {self.server.auth_token}"
            )

        url = f"{self.server.base_url.rstrip('/')}/{path.lstrip('/')}"

        response = requests.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=request_headers,
        )
        response.raise_for_status()

        return response