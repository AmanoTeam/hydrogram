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

import inspect
import re
from re import Pattern
from typing import Callable

import hydrogram
from hydrogram import enums
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineQuery,
    Message,
    ReplyKeyboardMarkup,
    Update,
)


class Filter:
    async def __call__(self, client: hydrogram.Client, update: Update):
        raise NotImplementedError

    def __invert__(self):
        return InvertFilter(self)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)


class InvertFilter(Filter):
    def __init__(self, base):
        self.base = base

    async def __call__(self, client: hydrogram.Client, update: Update):
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        return not x


class AndFilter(Filter):
    def __init__(self, base, other):
        self.base = base
        self.other = other

    async def __call__(self, client: hydrogram.Client, update: Update):
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        # short circuit
        if not x:
            return False

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, update)
        else:
            y = await client.loop.run_in_executor(client.executor, self.other, client, update)

        return x and y


class OrFilter(Filter):
    def __init__(self, base, other):
        self.base = base
        self.other = other

    async def __call__(self, client: hydrogram.Client, update: Update):
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        # short circuit
        if x:
            return True

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, update)
        else:
            y = await client.loop.run_in_executor(client.executor, self.other, client, update)

        return x or y


CUSTOM_FILTER_NAME = "CustomFilter"


def create(func: Callable, name: str | None = None, **kwargs) -> Filter:
    """Easily create a custom filter.

    Custom filters give you extra control over which updates are allowed or not to be processed by your handlers.

    Parameters:
        func (``Callable``):
            A function that accepts three positional arguments *(filter, client, update)* and returns a boolean: True if the
            update should be handled, False otherwise.
            The *filter* argument refers to the filter itself and can be used to access keyword arguments (read below).
            The *client* argument refers to the :obj:`~hydrogram.Client` that received the update.
            The *update* argument type will vary depending on which `Handler <handlers>`_ is coming from.
            For example, in a :obj:`~hydrogram.handlers.MessageHandler` the *update* argument will be a :obj:`~hydrogram.types.Message`; in a :obj:`~hydrogram.handlers.CallbackQueryHandler` the *update* will be a :obj:`~hydrogram.types.CallbackQuery`.
            Your function body can then access the incoming update attributes and decide whether to allow it or not.

        name (``str``, *optional*):
            Your filter's name. Can be anything you like.
            Defaults to "CustomFilter".

        **kwargs (``any``, *optional*):
            Any keyword argument you would like to pass. Useful when creating parameterized custom filters, such as
            :meth:`~hydrogram.filters.command` or :meth:`~hydrogram.filters.regex`.
    """
    return type(
        name or func.__name__ or CUSTOM_FILTER_NAME,
        (Filter,),
        {"__call__": func, **kwargs},
    )()


# region all_filter
def all_filter(_, __, ___):
    return True


all = create(all_filter)
"""Filter all messages."""


# endregion


# region me_filter
def me_filter(_, __, m: Message):
    return bool(m.from_user.is_self if m.from_user else getattr(m, "outgoing", False))


me = create(me_filter)
"""Filter messages generated by you yourself."""


# endregion


# region bot_filter
def bot_filter(_, __, m: Message):
    return bool(m.from_user and m.from_user.is_bot)


bot = create(bot_filter)
"""Filter messages coming from bots."""


# endregion


# region incoming_filter
def incoming_filter(_, __, m: Message):
    return not m.outgoing


incoming = create(incoming_filter)
"""Filter incoming messages. Messages sent to your own chat (Saved Messages) are also recognised as incoming."""


# endregion


# region outgoing_filter
def outgoing_filter(_, __, m: Message):
    return m.outgoing


outgoing = create(outgoing_filter)
"""Filter outgoing messages. Messages sent to your own chat (Saved Messages) are not recognized as outgoing."""


# endregion


# region text_filter
def text_filter(_, __, m: Message):
    return bool(m.text)


text = create(text_filter)
"""Filter text messages."""


# endregion


# region reply_filter
def reply_filter(_, __, m: Message):
    return bool(m.reply_to_message_id)


reply = create(reply_filter)
"""Filter messages that are replies to other messages."""


# endregion


# region forwarded_filter
def forwarded_filter(_, __, m: Message):
    return bool(m.forward_date)


forwarded = create(forwarded_filter)
"""Filter messages that are forwarded."""


# endregion


# region caption_filter
def caption_filter(_, __, m: Message):
    return bool(m.caption)


caption = create(caption_filter)
"""Filter media messages that contain captions."""


# endregion


# region audio_filter
def audio_filter(_, __, m: Message):
    return bool(m.audio)


audio = create(audio_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Audio` objects."""


# endregion


# region document_filter
def document_filter(_, __, m: Message):
    return bool(m.document)


document = create(document_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Document` objects."""


# endregion


# region photo_filter
def photo_filter(_, __, m: Message):
    return bool(m.photo)


photo = create(photo_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Photo` objects."""


# endregion


# region sticker_filter
def sticker_filter(_, __, m: Message):
    return bool(m.sticker)


sticker = create(sticker_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Sticker` objects."""


# endregion


# region animation_filter
def animation_filter(_, __, m: Message):
    return bool(m.animation)


animation = create(animation_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Animation` objects."""


# endregion


# region game_filter
def game_filter(_, __, m: Message):
    return bool(m.game)


game = create(game_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Game` objects."""


# endregion


# region video_filter
def video_filter(_, __, m: Message):
    return bool(m.video)


video = create(video_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Video` objects."""


# endregion


# region media_group_filter
def media_group_filter(_, __, m: Message):
    return bool(m.media_group_id)


media_group = create(media_group_filter)
"""Filter messages containing photos or videos being part of an album."""


# endregion


# region voice_filter
def voice_filter(_, __, m: Message):
    return bool(m.voice)


voice = create(voice_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Voice` note objects."""


# endregion


# region video_note_filter
def video_note_filter(_, __, m: Message):
    return bool(m.video_note)


video_note = create(video_note_filter)
"""Filter messages that contain :obj:`~hydrogram.types.VideoNote` objects."""


# endregion


# region contact_filter
def contact_filter(_, __, m: Message):
    return bool(m.contact)


contact = create(contact_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Contact` objects."""


# endregion


# region location_filter
def location_filter(_, __, m: Message):
    return bool(m.location)


location = create(location_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Location` objects."""


# endregion


# region venue_filter
def venue_filter(_, __, m: Message):
    return bool(m.venue)


venue = create(venue_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Venue` objects."""


# endregion


# region web_page_filter
def web_page_filter(_, __, m: Message):
    return bool(m.web_page)


web_page = create(web_page_filter)
"""Filter messages sent with a webpage preview."""


# endregion


# region poll_filter
def poll_filter(_, __, m: Message):
    return bool(m.poll)


poll = create(poll_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Poll` objects."""


# endregion


# region dice_filter
def dice_filter(_, __, m: Message):
    return bool(m.dice)


dice = create(dice_filter)
"""Filter messages that contain :obj:`~hydrogram.types.Dice` objects."""


# endregion


# region media_spoiler
def media_spoiler_filter(_, __, m: Message):
    return bool(m.has_media_spoiler)


media_spoiler = create(media_spoiler_filter)
"""Filter media messages that contain a spoiler."""


# endregion


# region private_filter
def private_filter(_, __, m: CallbackQuery | Message):
    if isinstance(m, Message):
        value = m.chat
    elif isinstance(m, CallbackQuery):
        value = m.message.chat
    else:
        raise ValueError(f"Private filter doesn't work with {type(m)}")
    return bool(value and value.type in {enums.ChatType.PRIVATE, enums.ChatType.BOT})


private = create(private_filter)
"""Filter messages sent in private chats."""


# endregion


# region group_filter
def group_filter(_, __, m: CallbackQuery | Message):
    if isinstance(m, Message):
        value = m.chat
    elif isinstance(m, CallbackQuery):
        value = m.message.chat
    else:
        raise ValueError(f"Group filter doesn't work with {type(m)}")
    return bool(value and value.type in {enums.ChatType.GROUP, enums.ChatType.SUPERGROUP})


group = create(group_filter)
"""Filter messages sent in group or supergroup chats."""


# endregion


# region channel_filter
def channel_filter(_, __, m: CallbackQuery | Message):
    if isinstance(m, Message):
        value = m.chat
    elif isinstance(m, CallbackQuery):
        value = m.message.chat
    else:
        raise ValueError(f"Channel filter doesn't work with {type(m)}")
    return bool(value and value.type == enums.ChatType.CHANNEL)


channel = create(channel_filter)
"""Filter messages sent in channels."""


# endregion


# region new_chat_members_filter
def new_chat_members_filter(_, __, m: Message):
    return bool(m.new_chat_members)


new_chat_members = create(new_chat_members_filter)
"""Filter service messages for new chat members."""


# endregion


# region left_chat_member_filter
def left_chat_member_filter(_, __, m: Message):
    return bool(m.left_chat_member)


left_chat_member = create(left_chat_member_filter)
"""Filter service messages for members that left the chat."""


# endregion


# region new_chat_title_filter
def new_chat_title_filter(_, __, m: Message):
    return bool(m.new_chat_title)


new_chat_title = create(new_chat_title_filter)
"""Filter service messages for new chat titles."""


# endregion


# region new_chat_photo_filter
def new_chat_photo_filter(_, __, m: Message):
    return bool(m.new_chat_photo)


new_chat_photo = create(new_chat_photo_filter)
"""Filter service messages for new chat photos."""


# endregion


# region delete_chat_photo_filter
def delete_chat_photo_filter(_, __, m: Message):
    return bool(m.delete_chat_photo)


delete_chat_photo = create(delete_chat_photo_filter)
"""Filter service messages for deleted photos."""


# endregion


# region group_chat_created_filter
def group_chat_created_filter(_, __, m: Message):
    return bool(m.group_chat_created)


group_chat_created = create(group_chat_created_filter)
"""Filter service messages for group chat creations."""


# endregion


# region supergroup_chat_created_filter
def supergroup_chat_created_filter(_, __, m: Message):
    return bool(m.supergroup_chat_created)


supergroup_chat_created = create(supergroup_chat_created_filter)
"""Filter service messages for supergroup chat creations."""


# endregion


# region channel_chat_created_filter
def channel_chat_created_filter(_, __, m: Message):
    return bool(m.channel_chat_created)


channel_chat_created = create(channel_chat_created_filter)
"""Filter service messages for channel chat creations."""


# endregion


# region migrate_to_chat_id_filter
def migrate_to_chat_id_filter(_, __, m: Message):
    return bool(m.migrate_to_chat_id)


migrate_to_chat_id = create(migrate_to_chat_id_filter)
"""Filter service messages that contain migrate_to_chat_id."""


# endregion


# region migrate_from_chat_id_filter
def migrate_from_chat_id_filter(_, __, m: Message):
    return bool(m.migrate_from_chat_id)


migrate_from_chat_id = create(migrate_from_chat_id_filter)
"""Filter service messages that contain migrate_from_chat_id."""


# endregion


# region pinned_message_filter
def pinned_message_filter(_, __, m: Message):
    return bool(m.pinned_message)


pinned_message = create(pinned_message_filter)
"""Filter service messages for pinned messages."""


# endregion


# region game_high_score_filter
def game_high_score_filter(_, __, m: Message):
    return bool(m.game_high_score)


game_high_score = create(game_high_score_filter)
"""Filter service messages for game high scores."""


# endregion


# region reply_keyboard_filter
def reply_keyboard_filter(_, __, m: Message):
    return isinstance(m.reply_markup, ReplyKeyboardMarkup)


reply_keyboard = create(reply_keyboard_filter)
"""Filter messages containing reply keyboard markups"""


# endregion


# region inline_keyboard_filter
def inline_keyboard_filter(_, __, m: Message):
    return isinstance(m.reply_markup, InlineKeyboardMarkup)


inline_keyboard = create(inline_keyboard_filter)
"""Filter messages containing inline keyboard markups"""


# endregion


# region mentioned_filter
def mentioned_filter(_, __, m: Message):
    return bool(m.mentioned)


mentioned = create(mentioned_filter)
"""Filter messages containing mentions"""


# endregion


# region via_bot_filter
def via_bot_filter(_, __, m: Message):
    return bool(m.via_bot)


via_bot = create(via_bot_filter)
"""Filter messages sent via inline bots"""


# endregion


# region video_chat_started_filter
def video_chat_started_filter(_, __, m: Message):
    return bool(m.video_chat_started)


video_chat_started = create(video_chat_started_filter)
"""Filter messages for started video chats"""


# endregion


# region video_chat_ended_filter
def video_chat_ended_filter(_, __, m: Message):
    return bool(m.video_chat_ended)


video_chat_ended = create(video_chat_ended_filter)
"""Filter messages for ended video chats"""


# endregion


# region video_chat_members_invited_filter
def video_chat_members_invited_filter(_, __, m: Message):
    return bool(m.video_chat_members_invited)


video_chat_members_invited = create(video_chat_members_invited_filter)
"""Filter messages for voice chat invited members"""


# endregion


# region service_filter
def service_filter(_, __, m: Message):
    return bool(m.service)


service = create(service_filter)
"""Filter service messages.

A service message contains any of the following fields set: *left_chat_member*,
*new_chat_title*, *new_chat_photo*, *delete_chat_photo*, *group_chat_created*, *supergroup_chat_created*,
*channel_chat_created*, *migrate_to_chat_id*, *migrate_from_chat_id*, *pinned_message*, *game_score*,
*video_chat_started*, *video_chat_ended*, *video_chat_members_invited*.
"""


# endregion


# region media_filter
def media_filter(_, __, m: Message):
    return bool(m.media)


media = create(media_filter)
"""Filter media messages.

A media message contains any of the following fields set: *audio*, *document*, *photo*, *sticker*, *video*,
*animation*, *voice*, *video_note*, *contact*, *location*, *venue*, *poll*.
"""


# endregion


# region scheduled_filter
def scheduled_filter(_, __, m: Message):
    return bool(m.scheduled)


scheduled = create(scheduled_filter)
"""Filter messages that have been scheduled (not yet sent)."""


# endregion


# region from_scheduled_filter
def from_scheduled_filter(_, __, m: Message):
    return bool(m.from_scheduled)


from_scheduled = create(from_scheduled_filter)
"""Filter new automatically sent messages that were previously scheduled."""


# endregion


# region linked_channel_filter
def linked_channel_filter(_, __, m: Message):
    return bool(m.forward_from_chat and not m.from_user)


linked_channel = create(linked_channel_filter)
"""Filter messages that are automatically forwarded from the linked channel to the group chat."""


# endregion


# region command_filter
def command(
    commands: str | list[str],
    prefixes: str | list[str] = "/",
    case_sensitive: bool = False,
):
    """Filter commands, i.e.: text messages starting with "/" or any other custom prefix.

    Parameters:
        commands (``str`` | ``list``):
            The command or list of commands as string the filter should look for.
            Examples: "start", ["start", "help", "settings"]. When a message text containing
            a command arrives, the command itself and its arguments will be stored in the *command*
            field of the :obj:`~hydrogram.types.Message`.

        prefixes (``str`` | ``list``, *optional*):
            A prefix or a list of prefixes as string the filter should look for.
            Defaults to "/" (slash). Examples: ".", "!", ["/", "!", "."], list(".:!").
            Pass None or "" (empty string) to allow commands with no prefix at all.

        case_sensitive (``bool``, *optional*):
            Pass True if you want your command(s) to be case sensitive. Defaults to False.
            Examples: when True, command="Start" would trigger /Start but not /start.
    """
    command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

    def func(flt, client: hydrogram.Client, message: Message):
        username = client.me.username or ""
        text = message.text or message.caption
        message.command = None

        if not text:
            return False

        for prefix in flt.prefixes:
            if not text.startswith(prefix):
                continue

            without_prefix = text[len(prefix) :]

            for cmd in flt.commands:
                if not re.match(
                    rf"^(?:{cmd}(?:@?{username})?)(?:\s|$)",
                    without_prefix,
                    flags=0 if flt.case_sensitive else re.IGNORECASE,
                ):
                    continue

                without_command = re.sub(
                    rf"{cmd}(?:@?{username})?\s?",
                    "",
                    without_prefix,
                    count=1,
                    flags=0 if flt.case_sensitive else re.IGNORECASE,
                )

                # match.groups are 1-indexed, group(1) is the quote, group(2) is the text
                # between the quotes, group(3) is unquoted, whitespace-split text

                # Remove the escape character from the arguments
                message.command = [cmd] + [
                    re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
                    for m in command_re.finditer(without_command)
                ]

                return True

        return False

    commands = commands if isinstance(commands, list) else [commands]
    commands = {c if case_sensitive else c.lower() for c in commands}

    prefixes = [] if prefixes is None else prefixes
    prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
    prefixes = set(prefixes) if prefixes else {""}

    return create(
        func,
        "CommandFilter",
        commands=commands,
        prefixes=prefixes,
        case_sensitive=case_sensitive,
    )


# endregion


def regex(pattern: str | Pattern, flags: int = 0):
    """Filter updates that match a given regular expression pattern.

    Can be applied to handlers that receive one of the following updates:

    - :obj:`~hydrogram.types.Message`: The filter will match ``text`` or ``caption``.
    - :obj:`~hydrogram.types.CallbackQuery`: The filter will match ``data``.
    - :obj:`~hydrogram.types.InlineQuery`: The filter will match ``query``.

    When a pattern matches, all the `Match Objects <https://docs.python.org/3/library/re.html#match-objects>`_ are
    stored in the ``matches`` field of the update object itself.

    Parameters:
        pattern (``str`` | ``Pattern``):
            The regex pattern as string or as pre-compiled pattern.

        flags (``int``, *optional*):
            Regex flags.
    """

    def func(flt, _, update: Update):
        if isinstance(update, Message):
            value = update.text or update.caption
        elif isinstance(update, CallbackQuery):
            value = update.data
        elif isinstance(update, InlineQuery):
            value = update.query
        else:
            raise ValueError(f"Regex filter doesn't work with {type(update)}")

        if value:
            update.matches = list(flt.p.finditer(value)) or None

        return bool(update.matches)

    return create(
        func,
        "RegexFilter",
        p=pattern if isinstance(pattern, Pattern) else re.compile(pattern, flags),
    )


class user(Filter, set):  # noqa: N801
    """Filter messages coming from one or more users.

    You can use `set bound methods <https://docs.python.org/3/library/stdtypes.html#set>`_ to manipulate the
    users container.

    Parameters:
        users (``int`` | ``str`` | ``list``):
            Pass one or more user ids/usernames to filter users.
            For you yourself, "me" or "self" can be used as well.
            Defaults to None (no users).
    """

    def __init__(self, users: int | str | list[int | str] | None = None):
        users = [] if users is None else users if isinstance(users, list) else [users]

        super().__init__(
            "me" if u in {"me", "self"} else u.lower().strip("@") if isinstance(u, str) else u
            for u in users
        )

    async def __call__(self, _, message: Message):
        return message.from_user and (
            message.from_user.id in self
            or (message.from_user.username and message.from_user.username.lower() in self)
            or ("me" in self and message.from_user.is_self)
        )


class chat(Filter, set):  # noqa: N801
    """Filter messages coming from one or more chats.

    You can use `set bound methods <https://docs.python.org/3/library/stdtypes.html#set>`_ to manipulate the
    chats container.

    Parameters:
        chats (``int`` | ``str`` | ``list``):
            Pass one or more chat ids/usernames to filter chats.
            For your personal cloud (Saved Messages) you can simply use "me" or "self".
            Defaults to None (no chats).
    """

    def __init__(self, chats: int | str | list[int | str] | None = None):
        chats = [] if chats is None else chats if isinstance(chats, list) else [chats]

        super().__init__(
            "me" if c in {"me", "self"} else c.lower().strip("@") if isinstance(c, str) else c
            for c in chats
        )

    async def __call__(self, _, message: Message):
        return message.chat and (
            message.chat.id in self
            or (message.chat.username and message.chat.username.lower() in self)
            or (
                "me" in self
                and message.from_user
                and message.from_user.is_self
                and not message.outgoing
            )
        )