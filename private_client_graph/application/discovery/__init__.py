"""Application boundary for scoped, private synthetic Workspace discovery."""
from .google import WorkspaceScope
from .limits import Limits
from .session import DiscoverySession

__all__ = ["DiscoverySession", "Limits", "WorkspaceScope"]
