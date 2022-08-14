"""OneBot 事件模型搜索树。

FrontMatter:
    sidebar_position: 1
    description: onebot.collator 模块
"""
from typing import Any, Dict, List, Type, Tuple, Union, Generic, TypeVar, Optional

from pygtrie import StringTrie
from pydantic.fields import ModelField
from nonebot.utils import logger_wrapper
from pydantic.typing import is_literal_type, all_literal_values

from nonebot.adapters import Event

E = TypeVar("E", bound=Event)
SEPARATOR = "/"


class Collator(Generic[E]):
    def __init__(
        self,
        name: str,
        models: List[Type[E]],
        keys: Tuple[Union[str, Tuple[str, ...]], ...],
    ):
        self.name = name
        self.logger = logger_wrapper(self.name)

        self.models = models
        self.keys = keys

        self.tree = StringTrie(separator=SEPARATOR)
        self._refresh_tree()

    def add_model(self, *model: Type[E]):
        self.models.extend(model)
        self._refresh_tree()

    def get_model(self, data: Dict[str, Any]) -> List[Type[E]]:
        key = self._key_from_dict(data)
        return [model.value for model in self.tree.prefixes(key)][::-1]

    def _refresh_tree(self):
        self.tree.clear()
        for model in self.models:
            key = self._key_from_model(model)
            if key in self.tree:
                self.logger(
                    "WARNING",
                    f'Model for key "{key}" {self.tree[key]} is overridden by {model}',
                )
            self.tree[key] = model

    def _key_from_dict(self, data: Dict[str, Any]) -> str:
        keys: List[Optional[str]] = []
        for key in self.keys:
            if isinstance(key, tuple):
                fields = list(filter(None, map(lambda k: data.get(k, None), key)))
                if len(fields) > 1:
                    raise ValueError(f"Invalid data with incorrect fields: {fields}")
                field = fields[0] if fields else None
            else:
                field = data.get(key)
            keys.append(field)
        return self._generate_key(keys)

    def _key_from_model(self, model: Type[E]) -> str:
        keys: List[Optional[str]] = []
        for key in self.keys:
            if isinstance(key, tuple):
                fields = list(
                    filter(None, map(lambda k: self._get_model_field(model, k), key))
                )
                if len(fields) > 1:
                    raise ValueError(f"Invalid model with incorrect fields: {fields}")
                field = fields[0] if fields else None
            else:
                field = self._get_model_field(model, key)
            keys.append(field and self._get_literal_field_default(field))
        return self._generate_key(keys)

    def _generate_key(self, keys: List[Optional[str]]) -> str:
        if not self._check_key_list(keys):
            raise ValueError(
                "Invalid model with incorrect prefix "
                f"keys: {dict(zip(self.keys, keys))}"
            )
        tree_keys = [""] + list(filter(None, keys))
        return SEPARATOR.join(tree_keys)

    def _check_key_list(self, keys: List[Optional[str]]) -> bool:
        truthy = tuple(map(bool, keys))
        return all(truthy) or not any(truthy[truthy.index(False) :])

    def _get_model_field(self, model: Type[E], field: str) -> Optional[ModelField]:
        return model.__fields__.get(field, None)

    def _get_literal_field_default(self, field: ModelField) -> Optional[str]:
        if not is_literal_type(field.outer_type_):
            return
        allowed_values = all_literal_values(field.outer_type_)
        if len(allowed_values) > 1:
            return
        return allowed_values[0]
