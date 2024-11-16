#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import TYPE_CHECKING

from hydrogram.types.object import Object

if TYPE_CHECKING:
    from hydrogram import raw


class Session(Object):
    """Contains info about a device session.

    Parameters:
        id (``int``):
            Session id.

        device_model (``str``):
            Device model used for authorization.

        platform (``str``):
            Platform used for authorization.

        system_version (``str``):
            System version used for authorization.

        api_id (``int``):
            API ID used for authorization.

        app_name (``str``):
            App name used for authorization.

        app_version (``str``):
            App version used for authorization.

        date_created (``int``):
            Date when authorization was created.

        date_active (``int``):
            Date when authorization was last active.

        ip (``str``):
            IP address used for authorization.

        country (``str``):
            Country where authorization occurred.

        region (``str``):
            Region where authorization occurred.

        is_current (``bool``):
            Whether this is the current authorization.

        is_official_app (``bool``):
            Whether this is an official app.

        is_password_pending (``bool``):
            Whether a password is pending.

        accepts_secret_chats (``bool``):
            Whether secret chat requests are allowed.

        accepts_calls (``bool``):
            Whether call requests are allowed.

        is_confirmed (``bool``):
            Whether the authorization is confirmed.
    """

    def __init__(
        self,
        *,
        id: int,
        device_model: str,
        platform: str,
        system_version: str,
        api_id: int,
        app_name: str,
        app_version: str,
        date_created: int,
        date_active: int,
        ip: str,
        country: str,
        region: str,
        is_current: bool,
        is_official_app: bool,
        is_password_pending: bool,
        accepts_secret_chats: bool,
        accepts_calls: bool,
        is_confirmed: bool,
    ):
        super().__init__()

        self.id = id
        self.device_model = device_model
        self.platform = platform
        self.system_version = system_version
        self.api_id = api_id
        self.app_name = app_name
        self.app_version = app_version
        self.date_created = date_created
        self.date_active = date_active
        self.ip = ip
        self.country = country
        self.region = region
        self.is_current = is_current
        self.is_official_app = is_official_app
        self.is_password_pending = is_password_pending
        self.accepts_secret_chats = accepts_secret_chats
        self.accepts_calls = accepts_calls
        self.is_confirmed = is_confirmed

    @staticmethod
    def _parse(authorization: raw.types.Authorization) -> Session:
        return Session(
            id=authorization.hash,
            device_model=authorization.device_model,
            platform=authorization.platform,
            system_version=authorization.system_version,
            api_id=authorization.api_id,
            app_name=authorization.app_name,
            app_version=authorization.app_version,
            date_created=authorization.date_created,
            date_active=authorization.date_active,
            ip=authorization.ip,
            country=authorization.country,
            region=authorization.region,
            is_current=authorization.current,
            is_official_app=authorization.official_app,
            is_password_pending=authorization.password_pending,
            accepts_secret_chats=not authorization.encrypted_requests_disabled,
            accepts_calls=not authorization.call_requests_disabled,
            is_confirmed=not authorization.unconfirmed,
        )
