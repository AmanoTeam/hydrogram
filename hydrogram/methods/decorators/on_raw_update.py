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

from typing import Callable

import hydrogram


class OnRawUpdate:
    def on_raw_update(self=None, group: int = 0) -> Callable:
        """Decorator for handling raw updates.

        This does the same thing as :meth:`~hydrogram.Client.add_handler` using the
        :obj:`~hydrogram.handlers.RawUpdateHandler`.

        Parameters:
            group (``int``, *optional*):
                The group identifier, defaults to 0.
        """

        def decorator(func: Callable) -> Callable:
            if isinstance(self, hydrogram.Client):
                self.add_handler(hydrogram.handlers.RawUpdateHandler(func), group)
            else:
                if not hasattr(func, "handlers"):
                    func.handlers = []

                func.handlers.append((hydrogram.handlers.RawUpdateHandler(func), group))

            return func

        return decorator
