from core.auth import AuthManager
from core.dashboard_loader import DashboardLoader
from views.streamdash_builder import get_available_csvs, render_streamdash_builder_page


def render_visual_builder_page(dashboard_loader: DashboardLoader, auth_manager: AuthManager):
    """Direct forwarder to the Streamdash Visual Canvas Builder."""
    render_streamdash_builder_page(dashboard_loader, auth_manager)
