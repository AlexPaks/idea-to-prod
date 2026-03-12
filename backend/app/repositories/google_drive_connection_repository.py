from typing import Protocol

from app.models.google_drive_connection import GoogleDriveConnectionConfig


class GoogleDriveConnectionRepository(Protocol):
    async def get(self) -> GoogleDriveConnectionConfig | None: ...

    async def upsert(
        self, config: GoogleDriveConnectionConfig
    ) -> GoogleDriveConnectionConfig: ...
