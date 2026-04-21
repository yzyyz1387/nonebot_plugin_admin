from __future__ import annotations

import datetime
import importlib.util
import sys
import types
from typing import Any


def install_fake_orm_modules() -> None:
    plugin_module = sys.modules.get("nonebot_plugin_tortoise_orm")
    if plugin_module is None:
        plugin_module = types.ModuleType("nonebot_plugin_tortoise_orm")
        plugin_module.registered_models = []
        plugin_module.__spec__ = importlib.util.spec_from_loader(
            "nonebot_plugin_tortoise_orm",
            loader=None,
        )

        def _fake_add_model(model_path: str) -> None:
            plugin_module.registered_models.append(model_path)

        plugin_module.add_model = _fake_add_model
        sys.modules["nonebot_plugin_tortoise_orm"] = plugin_module

    if "tortoise" in sys.modules:
        return

    tortoise_module = types.ModuleType("tortoise")
    fields_module = types.ModuleType("tortoise.fields")
    models_module = types.ModuleType("tortoise.models")

    def _fake_field(*args, **kwargs):
        return None

    for field_name in [
        "IntField",
        "BigIntField",
        "CharField",
        "TextField",
        "BooleanField",
        "DatetimeField",
        "DateField",
        "SmallIntField",
    ]:
        setattr(fields_module, field_name, _fake_field)

    class FakeQuerySet:
        def __init__(
            self,
            model_cls,
            *,
            lookups: list[dict[str, Any]] | None = None,
            order_fields: list[str] | None = None,
            limit_count: int | None = None,
            offset_count: int = 0,
        ):
            self.model_cls = model_cls
            self.lookups = list(lookups or [])
            self.order_fields = list(order_fields or [])
            self.limit_count = limit_count
            self.offset_count = offset_count

        def _clone(
            self,
            *,
            lookups: list[dict[str, Any]] | None = None,
            order_fields: list[str] | None = None,
            limit_count: int | None = None,
            offset_count: int | None = None,
        ):
            return FakeQuerySet(
                self.model_cls,
                lookups=self.lookups if lookups is None else lookups,
                order_fields=self.order_fields if order_fields is None else order_fields,
                limit_count=self.limit_count if limit_count is None else limit_count,
                offset_count=self.offset_count if offset_count is None else offset_count,
            )

        @staticmethod
        def _matches_lookup(record, key: str, value: Any) -> bool:
            field_name, _, operator = key.partition("__")
            actual = getattr(record, field_name, None)

            if not operator:
                return actual == value
            if operator == "gt":
                return actual is not None and actual > value
            if operator == "lt":
                return actual is not None and actual < value
            if operator == "icontains":
                return str(value).lower() in str(actual or "").lower()
            return False

        def _results(self) -> list[Any]:
            records = list(self.model_cls._records)
            for lookup in self.lookups:
                records = [
                    record
                    for record in records
                    if all(self._matches_lookup(record, key, value) for key, value in lookup.items())
                ]

            for field_name in reversed(self.order_fields):
                reverse = field_name.startswith("-")
                key = field_name[1:] if reverse else field_name
                records.sort(
                    key=lambda record: (
                        getattr(record, key, None) is None,
                        getattr(record, key, None),
                    ),
                    reverse=reverse,
                )

            if self.offset_count:
                records = records[self.offset_count :]
            if self.limit_count is not None:
                records = records[: self.limit_count]
            return records

        async def _resolve(self) -> list[Any]:
            return list(self._results())

        def __await__(self):
            return self._resolve().__await__()

        def filter(self, **lookup):
            return self._clone(lookups=self.lookups + [lookup])

        def order_by(self, *field_names: str):
            return self._clone(order_fields=list(field_names))

        def limit(self, count: int):
            return self._clone(limit_count=int(count))

        def offset(self, count: int):
            return self._clone(offset_count=int(count))

        def all(self):
            return self

        async def first(self):
            results = self._results()
            return results[0] if results else None

        async def delete(self):
            targets = {id(record) for record in self._results()}
            self.model_cls._records = [
                record for record in self.model_cls._records if id(record) not in targets
            ]
            return len(targets)

        async def count(self):
            return len(self._results())

        async def exists(self):
            return bool(self._results())

    class FakeModel:
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls._records = []
            cls._next_id = 1

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
            now = datetime.datetime.now()
            if getattr(self, "created_at", None) is None:
                self.created_at = now
            if getattr(self, "updated_at", None) is None:
                self.updated_at = now
            if getattr(self, "id", None) is None:
                self.id = self.__class__._next_id
                self.__class__._next_id += 1

        async def save(self):
            records = self.__class__._records
            for index, record in enumerate(records):
                if getattr(record, "id", None) == getattr(self, "id", None):
                    records[index] = self
                    return
            records.append(self)

        @classmethod
        async def create(cls, **kwargs):
            record = cls(**kwargs)
            cls._records.append(record)
            return record

        @classmethod
        async def get_or_create(cls, defaults=None, **lookup):
            defaults = defaults or {}
            for record in cls._records:
                if all(getattr(record, key, None) == value for key, value in lookup.items()):
                    return record, False
            record = cls(**lookup, **defaults)
            cls._records.append(record)
            return record, True

        @classmethod
        async def update_or_create(cls, defaults=None, **lookup):
            defaults = defaults or {}
            for record in cls._records:
                if all(getattr(record, key, None) == value for key, value in lookup.items()):
                    for key, value in defaults.items():
                        setattr(record, key, value)
                    return record, False
            record = cls(**lookup, **defaults)
            cls._records.append(record)
            return record, True

        @classmethod
        def filter(cls, **lookup):
            return FakeQuerySet(cls).filter(**lookup)

        @classmethod
        def all(cls):
            return FakeQuerySet(cls)

        @classmethod
        async def bulk_create(cls, objs):
            for obj in objs:
                if getattr(obj, "id", None) is None:
                    obj.id = cls._next_id
                    cls._next_id += 1
                cls._records.append(obj)

    tortoise_module.fields = fields_module
    models_module.Model = FakeModel

    sys.modules["tortoise"] = tortoise_module
    sys.modules["tortoise.fields"] = fields_module
    sys.modules["tortoise.models"] = models_module
