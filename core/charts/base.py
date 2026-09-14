from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.express as px
import streamlit as st

from core.renderer import PALETTES, compute_aggregation


class BaseChart(ABC):
    """Abstract Base Class for all Streamdash Chart visualizers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.id = config.get("id", "chart_generic")
        self.title = config.get("title", "Chart")
        self.x = config.get("x")
        self.y = config.get("y")
        self.agg = str(config.get("agg", "sum")).lower()
        self.color = config.get("color")
        self.theme = config.get("theme", "plotly_white")
        self.palette = config.get("palette", "streamdash")
        self.labels = config.get("labels", config.get("show_labels", "none"))
        self.col_width = config.get("col_width", 6)
        self.height = config.get("height", 350)
        self.options = config.get("options", {})

    def get_color_sequence(self) -> List[str]:
        return PALETTES.get(self.palette, PALETTES["streamdash"])

    def prepare_color(self, df: pd.DataFrame):
        """Safely prepare dataframe and return single column name for Plotly color shelf."""
        if not self.color:
            return df, None
        if isinstance(self.color, list):
            if len(self.color) == 0:
                return df, None
            elif len(self.color) == 1:
                return df, self.color[0]
            else:
                combined_col = " • ".join(self.color)
                plot_df = df.copy()
                plot_df[combined_col] = plot_df[self.color[0]].astype(str)
                for c in self.color[1:]:
                    plot_df[combined_col] = plot_df[combined_col] + " • " + plot_df[c].astype(str)
                return plot_df, combined_col
        return df, str(self.color)

    @abstractmethod
    def render(self, df: pd.DataFrame):
        """Render the chart visual using Streamlit / Plotly."""
        pass

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        """Return unique string identifier."""
        pass

    @classmethod
    @abstractmethod
    def get_label(cls) -> str:
        """Return human-readable display label."""
        pass

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        """Return metadata describing configurable parameters for this chart type."""
        return []

    def apply_standard_layout(self, fig):
        """Apply shared Streamdash aesthetic layout to a Plotly figure."""
        fig.update_layout(
            template=self.theme,
            margin=dict(l=15, r=15, t=25, b=15),
            height=self.height,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                title_text="",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
        fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
        return fig
