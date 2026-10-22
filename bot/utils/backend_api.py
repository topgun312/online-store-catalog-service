import asyncio
from http import HTTPStatus
from typing import Any

import httpx
from loguru import logger

MAX_ATTEMPTS = 3
BACKOFF_BASE_SEC = 0.5
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
REQUEST_TIMEOUT_SEC = 30.0


class BackendError(Exception):

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BackendUnavailableError(BackendError):

    def __init__(self, last_error: Exception) -> None:
        super().__init__(f'backend недоступен: {last_error}')


class BackendClient:
    """HTTP client for the catalog backend."""

    def __init__(self, base_url: str) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip('/'),
            timeout=REQUEST_TIMEOUT_SEC,
        )

    @property
    def base_url(self) -> str:
        return str(self._http.base_url)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a request with retries on transient failures."""
        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await self._http.request(method, url, **kwargs)
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning('backend unreachable (attempt {a}/{n}): {e}', a=attempt, n=MAX_ATTEMPTS, e=exc)
            else:
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    if response.status_code >= HTTPStatus.BAD_REQUEST:
                        raise BackendError(_error_detail(response), status_code=response.status_code)
                    return response
                last_error = BackendError(_error_detail(response), status_code=response.status_code)
                logger.warning(
                    'backend {s} (attempt {a}/{n}), retrying',
                    s=response.status_code,
                    a=attempt,
                    n=MAX_ATTEMPTS,
                )
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(BACKOFF_BASE_SEC * 2 ** (attempt - 1))
        raise BackendUnavailableError(last_error) from last_error

    async def create_product(
        self,
        *,
        title: str,
        file_bytes: bytes,
        content_type: str = 'image/jpeg',
        category_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a product via the backend."""
        data: dict[str, Any] = {'title': title}
        if category_id is not None:
            data['category_id'] = category_id
        files = {'file': ('photo.jpg', file_bytes, content_type)}
        response = await self._request('POST', '/api/v1/product/', data=data, files=files)
        return response.json()['payload']

    async def update_product(
        self,
        *,
        product_id: str,
        title: str | None = None,
        file_bytes: bytes | None = None,
        content_type: str = 'image/jpeg',
        category_id: str | None = None,
        remove_category: bool = False,
    ) -> dict[str, Any]:
        """Update a product via the backend."""
        data: dict[str, Any] = {}
        if title is not None:
            data['title'] = title
        if category_id is not None:
            data['category_id'] = category_id
        if remove_category:
            data['remove_category'] = 'true'
        files = None
        if file_bytes is not None:
            files = {'file': ('photo.jpg', file_bytes, content_type)}
        response = await self._request('PUT', f'/api/v1/product/{product_id}', data=data, files=files)
        return response.json()['payload']

    async def delete_product(self, product_id: str) -> None:
        await self._request('DELETE', f'/api/v1/product/{product_id}')

    async def get_products(self, *, page: int = 1, per_page: int = 20) -> list[dict[str, Any]]:
        """Get a page of products from the backend."""
        response = await self._request(
            'GET',
            '/api/v1/product/',
            params={'page': page, 'per_page': per_page},
        )
        return response.json()['payload']

    async def get_categories(self) -> list[dict[str, Any]]:
        """Get all categories from the backend."""
        response = await self._request('GET', '/api/v1/category/')
        return response.json()['payload']

    async def create_category(self, *, name: str, slug: str | None = None) -> dict[str, Any]:
        """Create a category via the backend."""
        data: dict[str, Any] = {'name': name}
        if slug is not None:
            data['slug'] = slug
        response = await self._request('POST', '/api/v1/category/', json=data)
        return response.json()['payload']

    async def find_category_by_name(self, name: str) -> dict[str, Any] | None:
        """Find a category by name (case-insensitive)."""
        wanted = name.casefold()
        categories = await self.get_categories()
        return next((category for category in categories if str(category.get('name', '')).casefold() == wanted), None)

    async def healthcheck(self) -> bool:
        """Check that the backend is alive."""
        try:
            response = await self._request('GET', '/api/healthz/')
        except BackendError:
            return False
        return response.status_code == HTTPStatus.OK


def _error_detail(response: httpx.Response) -> str:
    """Extract a human-readable error detail from a response."""
    try:
        body = response.json()
    except ValueError:
        return f'HTTP {response.status_code}'
    if isinstance(body, dict):
        detail = body.get('detail')
        if isinstance(detail, str) and detail:
            return detail
    return f'HTTP {response.status_code}'
