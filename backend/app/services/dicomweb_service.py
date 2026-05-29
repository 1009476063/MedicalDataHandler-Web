"""DICOMweb client for QIDO-RS, WADO-RS, and STOW-RS operations."""

import httpx
from typing import Optional


class DicomwebService:
    """Async DICOMweb client supporting QIDO-RS, WADO-RS, and STOW-RS."""

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        headers = {"Accept": "application/dicom+json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        self.client = httpx.AsyncClient(timeout=60.0, headers=headers, verify=True)

    async def close(self):
        await self.client.aclose()

    # QIDO-RS: Query
    async def search_studies(self, params: Optional[dict] = None) -> list[dict]:
        resp = await self.client.get(f"{self.base_url}/studies", params=params or {})
        resp.raise_for_status()
        return resp.json()

    async def search_series(self, study_uid: str, params: Optional[dict] = None) -> list[dict]:
        resp = await self.client.get(f"{self.base_url}/studies/{study_uid}/series", params=params or {})
        resp.raise_for_status()
        return resp.json()

    async def search_instances(self, study_uid: str, series_uid: str, params: Optional[dict] = None) -> list[dict]:
        resp = await self.client.get(
            f"{self.base_url}/studies/{study_uid}/series/{series_uid}/instances",
            params=params or {},
        )
        resp.raise_for_status()
        return resp.json()

    # WADO-RS: Retrieve
    async def retrieve_study(self, study_uid: str) -> bytes:
        resp = await self.client.get(
            f"{self.base_url}/studies/{study_uid}",
            headers={"Accept": "multipart/related; type=\"application/dicom\""},
        )
        resp.raise_for_status()
        return resp.content

    async def retrieve_series(self, study_uid: str, series_uid: str) -> bytes:
        resp = await self.client.get(
            f"{self.base_url}/studies/{study_uid}/series/{series_uid}",
            headers={"Accept": "multipart/related; type=\"application/dicom\""},
        )
        resp.raise_for_status()
        return resp.content

    async def retrieve_instance(self, study_uid: str, series_uid: str, instance_uid: str) -> bytes:
        resp = await self.client.get(
            f"{self.base_url}/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}",
            headers={"Accept": "multipart/related; type=\"application/dicom\""},
        )
        resp.raise_for_status()
        return resp.content

    # STOW-RS: Store
    async def store_instances(self, study_uid: str, dicom_data: list[bytes]) -> dict:
        boundary = "----DicomwebBoundary"
        body = b""
        for item in dicom_data:
            body += f"--{boundary}\r\nContent-Type: application/dicom\r\n\r\n".encode()
            body += item
            body += b"\r\n"
        body += f"--{boundary}--\r\n".encode()

        resp = await self.client.post(
            f"{self.base_url}/studies/{study_uid}/stow",
            content=body,
            headers={"Content-Type": f"multipart/related; type=\"application/dicom\"; boundary={boundary}"},
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {"status": "ok"}
