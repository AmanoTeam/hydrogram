#!/bin/env python
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

import inspect
import re
from typing import Literal

import httpx
from lxml import html

from hydrogram import Client, types

# Item can be ignored entirely (True) or have specific fields ignored with optional aliases
IgnoreSpec = Literal[True] | dict[str, str | Literal[True]]

# dict of items to ignore with optional field aliases
# fmt: off
ignored_items: dict[str, IgnoreSpec] = {
    "*": {
        "type": True,
        "from": "from_user",
        "thumbnail": "thumb",
    },
    "Message": {
        "message_id": "id",
    },
    # Polling and webhook related methods and objects. Ignored for us.
    "get_updates": True,
    "set_webhook": True,
    "delete_webhook": True,
    "get_webhook_info": True,
    "Update": True,
    "WebhookInfo": True,
}
# fmt: on


def snake(s: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def check_field_ignored(field: str, ignore_spec: IgnoreSpec, hydrogram_fields: list[str]) -> bool:
    """Check if a field should be ignored based on ignore specs"""
    if field in hydrogram_fields:
        return True

    if isinstance(ignore_spec, dict):
        alias = ignore_spec.get(field)
        if isinstance(alias, bool):
            return True
        if alias and alias in hydrogram_fields:
            return True

    wildcard_spec = ignored_items.get("*", {})
    if isinstance(wildcard_spec, dict):
        alias = wildcard_spec.get(field)
        if isinstance(alias, bool):
            return True
        if alias and alias in hydrogram_fields:
            return True

    return False


class BotAPISchema:
    def __init__(self):
        self.client = httpx.Client()
        self.methods: dict[str, list[str]] = {}
        self.objects: dict[str, list[str]] = {}

    def finish_parsing(self, obj_name: str, obj_fields: list[str]):
        """Detects whether we're parsing a method or an object and stores it accordingly."""
        if obj_name[0].isupper():
            self.objects[obj_name] = obj_fields
        else:
            self.methods[snake(obj_name)] = obj_fields

    def parse(self):
        """Parses the Telegram Bot API documentation to extract methods and objects."""
        response = self.client.get("https://core.telegram.org/bots/api")
        response.raise_for_status()

        tree = html.fromstring(response.content)
        content = tree.xpath('//div[@id="dev_page_content"]')[0]

        currently_parsing = ""
        last_sec_fields: list[str] = []
        scraping = False

        for tag in content:
            if not scraping and tag.xpath('.//a[@name="getting-updates"]'):
                scraping = True
            elif not scraping:
                continue

            if tag.tag == "h4":
                tag_content = tag.text_content().strip()

                # Telegram places other stuff alongside with methods and objects, just ignore them.
                if " " in tag_content:
                    continue

                if currently_parsing and currently_parsing != tag_content:
                    self.finish_parsing(currently_parsing, last_sec_fields)
                    last_sec_fields = []

                currently_parsing = tag_content

            elif tag.tag == "table":
                rows = tag.xpath(".//tbody/tr")
                for row in rows:
                    cells = row.xpath(".//td")
                    field_name = cells[0].text_content().strip()
                    last_sec_fields.append(field_name)

        if currently_parsing:
            self.finish_parsing(currently_parsing, last_sec_fields)

    def get_schema(self):
        """Returns the parsed methods and objects."""
        self.parse()
        return self.methods, self.objects


class HydrogramSchema:
    def __init__(self):
        self.methods: dict[str, list[str]] = {}
        self.objects: dict[str, list[str]] = {}

    def parse_methods(self):
        """Parses methods in hydrogram.Client and extracts their arguments."""
        client_methods = inspect.getmembers(Client, predicate=inspect.isfunction)
        for method_name, method in client_methods:
            sig = inspect.signature(method)
            args = [param.name for param in sig.parameters.values() if param.name != "self"]
            self.methods[method_name] = args

    def parse_objects(self):
        """Parses classes in hydrogram.types and extracts their arguments."""
        types_classes = inspect.getmembers(types, predicate=inspect.isclass)
        for class_name, cls in types_classes:
            if hasattr(cls, "__init__"):
                sig = inspect.signature(cls.__init__)
                args = [param.name for param in sig.parameters.values() if param.name != "self"]
                self.objects[class_name] = args

    def parse(self):
        """Parses both methods and objects."""
        self.parse_methods()
        self.parse_objects()

    def get_schema(self):
        """Returns the parsed methods and objects."""
        self.parse()
        return self.methods, self.objects


def compare_item(
    bot_api_item: str,
    bot_api_fields: list[str],
    hydrogram_fields: list[str],
    ignore_spec: IgnoreSpec,
) -> list[str]:
    """Compare fields between bot API and hydrogram implementations"""
    if ignore_spec is True:
        return []

    return [
        field
        for field in bot_api_fields
        if not check_field_ignored(field, ignore_spec, hydrogram_fields)
    ]


def compare_schemas(bot_api_methods, bot_api_objects, hydrogram_methods, hydrogram_objects):
    missing_methods = {}
    missing_objects = {}
    method_mismatches = {}
    object_mismatches = {}

    # Compare methods
    for method_name, bot_api_args in bot_api_methods.items():
        ignore_spec = ignored_items.get(method_name, {})
        if ignore_spec is True:
            continue

        if method_name not in hydrogram_methods:
            missing_methods[method_name] = bot_api_args
        else:
            missing_args = compare_item(
                method_name, bot_api_args, hydrogram_methods[method_name], ignore_spec
            )
            if missing_args:
                method_mismatches[method_name] = missing_args

    # Compare objects
    for obj_name, bot_api_fields in bot_api_objects.items():
        ignore_spec = ignored_items.get(obj_name, {})
        if ignore_spec is True:
            continue

        if obj_name not in hydrogram_objects:
            missing_objects[obj_name] = bot_api_fields
        else:
            missing_fields = compare_item(
                obj_name, bot_api_fields, hydrogram_objects[obj_name], ignore_spec
            )
            if missing_fields:
                object_mismatches[obj_name] = missing_fields

    return {
        "missing_methods": missing_methods,
        "missing_objects": missing_objects,
        "method_mismatches": method_mismatches,
        "object_mismatches": object_mismatches,
    }


def generate_implementation_stats(total: int, unimplemented: int, partial: int) -> tuple[int, int]:
    """Calculate implementation statistics"""
    implemented = total - unimplemented
    fully_implemented = implemented - partial
    return implemented, fully_implemented


def generate_report(
    comparison_results, bot_api_methods, bot_api_objects, hydrogram_methods, hydrogram_objects
):
    report = []

    partially_implemented_methods = comparison_results["method_mismatches"]
    partially_implemented_objects = comparison_results["object_mismatches"]
    unimplemented_methods = comparison_results["missing_methods"]
    unimplemented_objects = comparison_results["missing_objects"]

    report.append("## ❌ Unimplemented features")

    if unimplemented_methods:
        report.append("\n### Methods")
        report.extend(f"- {method_name}" for method_name in unimplemented_methods)

    if unimplemented_objects:
        report.append("\n### Objects")
        report.extend(f"- {obj_name}" for obj_name in unimplemented_objects)

    total_methods = len(bot_api_methods)
    total_objects = len(bot_api_objects)

    implemented_methods, fully_implemented_methods = generate_implementation_stats(
        total_methods, len(unimplemented_methods), len(partially_implemented_methods)
    )

    implemented_objects, fully_implemented_objects = generate_implementation_stats(
        total_objects, len(unimplemented_objects), len(partially_implemented_objects)
    )

    report.append("## 🚧 Partially implemented features")

    if partially_implemented_methods:
        report.append("\n### Methods")
        for method_name, missing_args in partially_implemented_methods.items():
            total_args = len(bot_api_methods[method_name])
            implemented_args = total_args - len(missing_args)
            report.append(f"\n#### {method_name} ({implemented_args}/{total_args}):")
            report.extend(f"- {arg}" for arg in missing_args)
        report.append("")

    if partially_implemented_objects:
        report.append("\n### Objects")
        for obj_name, missing_fields in partially_implemented_objects.items():
            total_fields = len(bot_api_objects[obj_name])
            implemented_fields = total_fields - len(missing_fields)
            report.append(f"\n#### {obj_name} ({implemented_fields}/{total_fields}):")
            report.extend(f"- {field}" for field in missing_fields)
        report.append("")

    report.append("")

    report.extend([
        f"At least partially implemented methods: {implemented_methods}/{total_methods} ({(implemented_methods / total_methods) * 100:.0f}%)",
        f"At least partially implemented objects: {implemented_objects}/{total_objects} ({(implemented_objects / total_objects) * 100:.0f}%)",
    ])

    report.append("")

    report.extend([
        f"Fully implemented methods: {fully_implemented_methods}/{total_methods} ({(fully_implemented_methods / total_methods) * 100:.0f}%)",
        f"Fully implemented objects: {fully_implemented_objects}/{total_objects} ({(fully_implemented_objects / total_objects) * 100:.0f}%)",
    ])

    return "\n".join(report)


if __name__ == "__main__":
    bot_api_parser = BotAPISchema()
    bot_api_parser.parse()
    bot_api_methods, bot_api_objects = bot_api_parser.get_schema()

    hydrogram_parser = HydrogramSchema()
    hydrogram_parser.parse()
    hydrogram_methods, hydrogram_objects = hydrogram_parser.get_schema()

    comparison_results = compare_schemas(
        bot_api_methods, bot_api_objects, hydrogram_methods, hydrogram_objects
    )
    report = generate_report(
        comparison_results, bot_api_methods, bot_api_objects, hydrogram_methods, hydrogram_objects
    )
    print(report)
