#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
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

import hydrogram
from hydrogram import enums, raw, types, utils

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


async def get_chunk(
    client,
    chat_id: int | str,
    query: str = "",
    filter: enums.MessagesFilter = enums.MessagesFilter.EMPTY,
    offset: int = 0,
    limit: int = 100,
    from_user: int | str | None = None,
) -> list[types.Message]:
    r = await client.invoke(
        raw.functions.messages.Search(
            peer=await client.resolve_peer(chat_id),
            q=query,
            filter=filter.value(),
            min_date=0,
            max_date=0,
            offset_id=0,
            add_offset=offset,
            limit=limit,
            min_id=0,
            max_id=0,
            from_id=(await client.resolve_peer(from_user) if from_user else None),
            hash=0,
        ),
        sleep_threshold=60,
    )

    return await utils.parse_messages(client, r, replies=0)


class SearchMessages:
    async def search_messages(
        self: hydrogram.Client,
        chat_id: int | str,
        query: str = "",
        offset: int = 0,
        filter: enums.MessagesFilter = enums.MessagesFilter.EMPTY,
        limit: int = 0,
        from_user: int | str | None = None,
    ) -> AsyncGenerator[types.Message, None] | None:
        """Search for text and media messages inside a specific chat.

        If you want to get the messages count only, see :meth:`~hydrogram.Client.search_messages_count`.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            query (``str``, *optional*):
                Text query string.
                Required for text-only messages, optional for media messages (see the ``filter`` argument).
                When passed while searching for media messages, the query will be applied to captions.
                Defaults to "" (empty string).

            offset (``int``, *optional*):
                Sequential number of the first message to be returned.
                Defaults to 0.

            filter (:obj:`~hydrogram.enums.MessagesFilter`, *optional*):
                Pass a filter in order to search for specific kind of messages only.
                Defaults to any message (no filter).

            limit (``int``, *optional*):
                Limits the number of messages to be retrieved.
                By default, no limit is applied and all messages are returned.

            from_user (``int`` | ``str``, *optional*):
                Unique identifier (int) or username (str) of the target user you want to search for messages from.

        Returns:
            ``Generator``: A generator yielding :obj:`~hydrogram.types.Message` objects.

        Example:
            .. code-block:: python

                from hydrogram import enums

                # Search for text messages in chat. Get the last 120 results
                async for message in app.search_messages(chat_id, query="hello", limit=120):
                    print(message.text)

                # Search for pinned messages in chat
                async for message in app.search_messages(
                    chat_id, filter=enums.MessagesFilter.PINNED
                ):
                    print(message.text)

                # Search for messages containing "hello" sent by yourself in chat
                async for message in app.search_messages(chat, "hello", from_user="me"):
                    print(message.text)
        """

        current = 0
        total = abs(limit) or (1 << 31) - 1
        limit = min(100, total)

        while True:
            messages = await get_chunk(
                client=self,
                chat_id=chat_id,
                query=query,
                filter=filter,
                offset=offset,
                limit=limit,
                from_user=from_user,
            )

            if not messages:
                return

            offset += len(messages)

            for message in messages:
                yield message

                current += 1

                if current >= total:
                    return
