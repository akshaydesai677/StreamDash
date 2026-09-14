from typing import Any, Dict, List, Optional, Type
from core.charts.base import BaseChart
from core.charts.barchart import BarChart
from core.charts.linechart import LineChart
from core.charts.areachart import AreaChart
from core.charts.piechart import PieChart
from core.charts.scatterchart import ScatterChart
from core.charts.boxchart import BoxChart
from core.charts.metricchart import MetricChart
from core.charts.tablechart import TableChart


class ChartRegistry:
    """Registry managing available Chart visualizer implementations."""

    _registry: Dict[str, Type[BaseChart]] = {
        "bar": BarChart,
        "line": LineChart,
        "area": AreaChart,
        "pie": PieChart,
        "donut": PieChart,
        "scatter": ScatterChart,
        "box": BoxChart,
        "kpi": MetricChart,
        "metric": MetricChart,
        "table": TableChart,
    }

    @classmethod
    def register(cls, type_name: str, chart_cls: Type[BaseChart]):
        cls._registry[type_name.lower()] = chart_cls

    @classmethod
    def get(cls, type_name: str) -> Type[BaseChart]:
        normalized = str(type_name).lower()
        if normalized in cls._registry:
            return cls._registry[normalized]
        return BarChart

    @classmethod
    def list_types(cls) -> List[Dict[str, str]]:
        """List all unique chart types with labels."""
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
    def create(cls, config: Dict[str, Any]) -> BaseChart:
        c_type = config.get("type") or config.get("chart_type", "bar")
        chart_cls = cls.get(c_type)
        return chart_cls(config)
