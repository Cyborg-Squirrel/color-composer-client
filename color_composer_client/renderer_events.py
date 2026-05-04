"""
Data classes for events produced by the renderer.
"""

from dataclasses import dataclass


@dataclass
class RendererEvent:
    """Base class for all renderer events."""


@dataclass
class RendererBufferStatus(RendererEvent):
    """Frame was accepted and queued successfully."""
    frames_in_queue: int


@dataclass
class RendererError(RendererEvent):
    """Base class for renderer error events."""

@dataclass
class StaleFrameError(RendererError):
    """Frame timestamp is earlier than the current time."""
    frame_timestamp: int
    current_timestamp: int

@dataclass
class GenericError(RendererError):
    """Catch-all renderer error."""
    message: str

@dataclass
class BackpressureError(RendererError):
    """The sender is sending frames faster than the renderer can process them."""
    message: str
