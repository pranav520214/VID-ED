"""
EditFlow AI - Event System

Event-driven architecture for decoupled communication between modules.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
from uuid import UUID, uuid4

from ..models.entities import EntityId, EntityType


class EventType(Enum):
    """All event types in the system."""
    # Graph events
    ENTITY_ADDED = auto()
    ENTITY_UPDATED = auto()
    ENTITY_REMOVED = auto()
    RELATIONSHIP_ADDED = auto()
    RELATIONSHIP_REMOVED = auto()
    
    # Command events
    COMMAND_EXECUTED = auto()
    COMMAND_UNDONE = auto()
    COMMAND_REDONE = auto()
    
    # Timeline events
    CLIP_MOVED = auto()
    CLIP_TRIMMED = auto()
    CLIP_SPLIT = auto()
    TRACK_ADDED = auto()
    TRACK_REMOVED = auto()
    
    # Asset events
    ASSET_IMPORTED = auto()
    ASSET_ANALYZED = auto()
    ASSET_GENERATED = auto()
    
    # AI events
    AI_OPERATION_STARTED = auto()
    AI_OPERATION_COMPLETED = auto()
    AI_OPERATION_FAILED = auto()
    
    # Render events
    RENDER_STARTED = auto()
    RENDER_PROGRESS = auto()
    RENDER_COMPLETED = auto()
    RENDER_FAILED = auto()
    
    # Project events
    PROJECT_CREATED = auto()
    PROJECT_SAVED = auto()
    PROJECT_LOADED = auto()
    PROJECT_CLOSED = auto()
    
    # UI events
    SELECTION_CHANGED = auto()
    PLAYHEAD_MOVED = auto()
    ZOOM_CHANGED = auto()
    
    # Custom/user events
    CUSTOM = auto()


@dataclass(frozen=True)
class Event:
    """
    Base class for all events in the system.
    
    Events are immutable and carry payload data.
    """
    id: UUID
    event_type: EventType
    timestamp: datetime
    source: str  # Module or component that emitted the event
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "event_type": self.event_type.name,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "payload": self.payload
        }
    
    @classmethod
    def create(
        cls,
        event_type: EventType,
        source: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> 'Event':
        return cls(
            id=uuid4(),
            event_type=event_type,
            timestamp=datetime.now(),
            source=source,
            payload=payload or {}
        )


EventHandler = Callable[[Event], None]


class EventBus:
    """
    Central event bus for publishing and subscribing to events.
    
    Supports:
    - Global subscriptions
    - Type-filtered subscriptions
    - One-time handlers
    - Async handling (optional)
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []
        self._once_handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._is_paused = False
        self._paused_events: List[Event] = []
    
    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
    
    def subscribe_once(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """Subscribe to receive only the next occurrence of an event."""
        if event_type not in self._once_handlers:
            self._once_handlers[event_type] = []
        self._once_handlers[event_type].append(handler)
    
    def subscribe_global(self, handler: EventHandler) -> None:
        """Subscribe to all events regardless of type."""
        self._global_subscribers.append(handler)
    
    def unsubscribe_global(self, handler: EventHandler) -> None:
        """Unsubscribe from global events."""
        self._global_subscribers.remove(handler)
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if self._is_paused:
            self._paused_events.append(event)
            return
        
        # Record in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify type-specific subscribers
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't break other handlers
                pass
        
        # Notify global subscribers
        for handler in self._global_subscribers:
            try:
                handler(event)
            except Exception as e:
                pass
        
        # Notify and remove once handlers
        once_handlers = self._once_handlers.pop(event.event_type, [])
        for handler in once_handlers:
            try:
                handler(event)
            except Exception as e:
                pass
    
    def emit(
        self,
        event_type: EventType,
        source: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Event:
        """Convenience method to create and publish an event."""
        event = Event.create(event_type, source, payload)
        self.publish(event)
        return event
    
    def pause(self) -> None:
        """Pause event delivery. Events will be queued."""
        self._is_paused = True
    
    def resume(self) -> None:
        """Resume event delivery and flush queued events."""
        self._is_paused = False
        queued = self._paused_events
        self._paused_events = []
        for event in queued:
            self.publish(event)
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get recent events, optionally filtered by type."""
        if event_type is None:
            return self._event_history[-limit:]
        
        filtered = [e for e in self._event_history if e.event_type == event_type]
        return filtered[-limit:]
    
    def replay(
        self,
        event_type: Optional[EventType] = None,
        from_timestamp: Optional[datetime] = None
    ) -> List[Event]:
        """Replay events, optionally filtered."""
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]
        
        for event in events:
            self.publish(event)
        
        return events


class EventStore:
    """
    Persistent storage for events (for audit trails, debugging, etc.).
    
    This is a simple in-memory implementation; production would use
    a database or file-based storage.
    """
    
    def __init__(self):
        self._events: List[Event] = []
        self._index_by_type: Dict[EventType, List[int]] = {}
        self._index_by_source: Dict[str, List[int]] = {}
    
    def store(self, event: Event) -> int:
        """Store an event and return its index."""
        idx = len(self._events)
        self._events.append(event)
        
        # Update indexes
        if event.event_type not in self._index_by_type:
            self._index_by_type[event.event_type] = []
        self._index_by_type[event.event_type].append(idx)
        
        if event.source not in self._index_by_source:
            self._index_by_source[event.source] = []
        self._index_by_source[event.source].append(idx)
        
        return idx
    
    def query(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Event]:
        """Query stored events with filters."""
        results = []
        
        # Start with the most restrictive filter
        if event_type and event_type in self._index_by_type:
            indices = self._index_by_type[event_type]
        elif source and source in self._index_by_source:
            indices = self._index_by_source[source]
        else:
            indices = range(len(self._events))
        
        for idx in indices:
            event = self._events[idx]
            
            if event_type and event.event_type != event_type:
                continue
            if source and event.source != source:
                continue
            if from_timestamp and event.timestamp < from_timestamp:
                continue
            if to_timestamp and event.timestamp > to_timestamp:
                continue
            
            results.append(event)
            if len(results) >= limit:
                break
        
        return results
    
    def get_count(self) -> int:
        """Get total number of stored events."""
        return len(self._events)
    
    def clear(self) -> None:
        """Clear all stored events."""
        self._events.clear()
        self._index_by_type.clear()
        self._index_by_source.clear()


# =============================================================================
# EVENT FACTORY HELPERS
# =============================================================================

def create_graph_event(
    event_type: EventType,
    entity_id: EntityId,
    source: str = "graph"
) -> Event:
    """Create a graph-related event."""
    return Event.create(
        event_type=event_type,
        source=source,
        payload={"entity_id": str(entity_id), "entity_type": entity_id.entity_type.name}
    )


def create_command_event(
    command_name: str,
    success: bool,
    error: Optional[str] = None
) -> Event:
    """Create a command-related event."""
    payload = {"command_name": command_name, "success": success}
    if error:
        payload["error"] = error
    
    event_type = EventType.COMMAND_EXECUTED if success else EventType.AI_OPERATION_FAILED
    
    return Event.create(
        event_type=event_type,
        source="command_history",
        payload=payload
    )


def create_timeline_event(
    event_type: EventType,
    clip_id: Optional[EntityId] = None,
    track_id: Optional[EntityId] = None,
    position_ms: Optional[int] = None
) -> Event:
    """Create a timeline-related event."""
    payload = {}
    if clip_id:
        payload["clip_id"] = str(clip_id)
    if track_id:
        payload["track_id"] = str(track_id)
    if position_ms is not None:
        payload["position_ms"] = position_ms
    
    return Event.create(
        event_type=event_type,
        source="timeline",
        payload=payload
    )


def create_ai_event(
    operation_type: str,
    status: str,  # "started", "completed", "failed"
    prompt: Optional[str] = None,
    result: Optional[Any] = None,
    error: Optional[str] = None
) -> Event:
    """Create an AI-related event."""
    payload = {
        "operation_type": operation_type,
        "status": status
    }
    if prompt:
        payload["prompt"] = prompt
    if result is not None:
        payload["result"] = result
    if error:
        payload["error"] = error
    
    if status == "started":
        event_type = EventType.AI_OPERATION_STARTED
    elif status == "completed":
        event_type = EventType.AI_OPERATION_COMPLETED
    else:
        event_type = EventType.AI_OPERATION_FAILED
    
    return Event.create(
        event_type=event_type,
        source="ai_engine",
        payload=payload
    )


__all__ = [
    'EventType',
    'Event',
    'EventHandler',
    'EventBus',
    'EventStore',
    'create_graph_event',
    'create_command_event',
    'create_timeline_event',
    'create_ai_event'
]
