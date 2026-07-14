"""
EditFlow AI - Core Module

This module provides the core domain models and graph operations for the semantic knowledge graph.
"""

from .models.entities import (
    # Primitives
    TimeRange,
    SpatialRect,
    EntityType,
    EntityId,
    MetadataEntry,
    Entity,
    
    # Core entities
    Workspace,
    Project,
    Library,
    Asset,
    AssetType,
    AssetSource,
    AssetMetadata,
    Sequence,
    Timeline,
    TimelineSettings,
    Track,
    TrackType,
    Clip,
    ClipType,
    ClipSource,
    Transform,
    Effect,
    EffectType,
    EffectParameters,
    Generator,
    Keyframe,
    Relationship,
    AIContext,
    
    # Utilities
    export_for_backward_compatibility,
)

from .graph.knowledge_graph import KnowledgeGraph, GraphQuery, GraphTraversal
from .commands.command import Command, CommandResult, CommandHistory
from .events.event import Event, EventHandler, EventBus
from .serialization.serializer import GraphSerializer, SerializationFormat

__all__ = [
    # Entities
    'TimeRange',
    'SpatialRect',
    'EntityType',
    'EntityId',
    'MetadataEntry',
    'Entity',
    'Workspace',
    'Project',
    'Library',
    'Asset',
    'AssetType',
    'AssetSource',
    'AssetMetadata',
    'Sequence',
    'Timeline',
    'TimelineSettings',
    'Track',
    'TrackType',
    'Clip',
    'ClipType',
    'ClipSource',
    'Transform',
    'Effect',
    'EffectType',
    'EffectParameters',
    'Generator',
    'Keyframe',
    'Relationship',
    'AIContext',
    
    # Graph
    'KnowledgeGraph',
    'GraphQuery',
    'GraphTraversal',
    
    # Commands
    'Command',
    'CommandResult',
    'CommandHistory',
    
    # Events
    'Event',
    'EventHandler',
    'EventBus',
    
    # Serialization
    'GraphSerializer',
    'SerializationFormat',
    
    # Utilities
    'export_for_backward_compatibility',
]
