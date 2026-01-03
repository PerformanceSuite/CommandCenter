"""Bridges to external systems."""
from .auto_claude import AutoClaudeBridge
from .sandbox import SandboxBridge

__all__ = ["AutoClaudeBridge", "SandboxBridge"]
