from typing import Any, Dict, List, Optional, Type
from core.filters.base import BaseFilter
from core.filters.multiselect import MultiselectFilter
from core.filters.select import SelectFilter
from core.filters.date_range import DateRangeFilter
from core.filters.numeric_range import NumericRangeFilter
from core.filters.search import SearchFilter
from core.filters.radio import RadioFilter
from core.filters.checkbox import CheckboxFilter


class FilterRegistry:
    """Registry managing available Filter implementations."""

    _registry: Dict[str, Type[BaseFilter]] = {
        "multiselect": MultiselectFilter,
        "selectbox": SelectFilter,
        "select": SelectFilter,
        "radio": RadioFilter,
        "checkbox": CheckboxFilter,
        "date_range": DateRangeFilter,
        "slider": NumericRangeFilter,
        "numeric_range": NumericRangeFilter,
        "search": SearchFilter,
    }

    @classmethod
    def register(cls, type_name: str, filter_cls: Type[BaseFilter]):
        cls._registry[type_name.lower()] = filter_cls

    @classmethod
    def get(cls, type_name: str) -> Type[BaseFilter]:
        normalized = str(type_name).lower()
        if normalized in cls._registry:
            return cls._registry[normalized]
        return MultiselectFilter

    @classmethod
    def list_types(cls) -> List[Dict[str, str]]:
        """List all unique filter types with labels."""
        unique_types = {}
        for k, v in cls._registry.items():
            t_id = v.get_type()
            if t_id not in unique_types:
                unique_types[t_id] = {
                    "type": t_id,
                    "label": v.get_label(),
                }
        return list(unique_types.values())

    @classmethod
    def create(cls, config: Dict[str, Any]) -> BaseFilter:
        f_type = config.get("type", "multiselect")
        filter_cls = cls.get(f_type)
        return filter_cls(config)
