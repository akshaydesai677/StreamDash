from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class BaseDataAdapter(ABC):
    """Abstract base class for all Streamdash data adapters."""

    @abstractmethod
    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Load data into a pandas DataFrame based on the source config.

        Args:
            config: Dictionary containing adapter-specific configuration parameters.

        Returns:
            pd.DataFrame: Loaded and prepared data.
        """
        pass

    @abstractmethod
    def get_columns(self, config: Dict[str, Any]) -> List[str]:
        """Return list of column names for the dataset."""
        pass

    def filter_data(
        self, df: pd.DataFrame, active_filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply user-selected filters to the DataFrame.

        Default implementation handles common filter types:
        - List/Tuple/Set: isin filtering
        - 2-element tuple/list of numbers or dates: range filtering
        - Single scalar value: equality filtering
        """
        filtered_df = df.copy()

        for col, val in active_filters.items():
            if val is None or col not in filtered_df.columns:
                continue

            # Multi-select or list of values
            if isinstance(val, (list, tuple, set)):
                if len(val) == 0:
                    continue
                # Check if it's a 2-element range (e.g., date range or slider min/max)
                if (
                    len(val) == 2
                    and hasattr(val[0], "__lt__")
                    and type(val[0]) == type(val[1])
                    and not isinstance(val[0], str)
                ):
                    min_val, max_val = val
                    filtered_df = filtered_df[
                        (filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)
                    ]
                else:
                    # Regular categorical multi-selection
                    filtered_df = filtered_df[filtered_df[col].isin(val)]
            elif isinstance(val, str) and val != "All":
                filtered_df = filtered_df[filtered_df[col] == val]
            elif isinstance(val, (int, float)):
                filtered_df = filtered_df[filtered_df[col] == val]

        return filtered_df
