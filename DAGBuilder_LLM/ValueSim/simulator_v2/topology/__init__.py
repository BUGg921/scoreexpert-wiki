"""Physical topology and communication-domain construction."""

from .models import Device, LinkProfile, LinkUnavailableError, Topology

__all__ = ["Device", "LinkProfile", "LinkUnavailableError", "Topology"]
