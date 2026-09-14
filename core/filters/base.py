from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class BaseFilter(ABC):
    """Abstract Base Class for all Streamdash Filter types."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.id = config.get("id", "filter_generic")
        self.column = config.get("column", "")
        self.label = config.get("label", self.column)
        self.default = config.get("default")
        self.help = config.get("help", "")
        self.options = config.get("options", {})

    @abstractmethod
    def render(self, df: pd.DataFrame, key_prefix: str = "") -> Any:
        """Render the Streamlit filter widget and return the user's active selection."""
        pass

    @abstractmethod
    def apply(self, df: pd.DataFrame, selected_value: Any) -> pd.DataFrame:
        """Filter the dataframe according to the selected filter value."""
        pass

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        """Return the unique string identifier for this filter type."""
        pass

    @classmethod
    @abstractmethod
    def get_label(cls) -> str:
        """Return human-readable display label."""
        pass

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        """Return metadata describing configurable parameters for this filter type."""
        return []
