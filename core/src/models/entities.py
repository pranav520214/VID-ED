"""
EditFlow AI - Core Domain Models

This module defines the immutable domain models for the semantic knowledge graph.
Every object in the editor is represented as data that can be queried, serialized,
and reasoned about by AI agents.

Architecture Principles:
- Immutability: All entities are frozen after creation; modifications create new versions
- Type Safety: Full TypeScript/Python type annotations
- Graph-Native: Every entity has relationships and metadata
- Undo/Redo Ready: Entities support versioning through commands
- AI-Queryable: Rich metadata enables semantic reasoning
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Generic, List, Optional, Set, TypeVar, Union
from uuid import UUID, uuid4
import json


# =============================================================================
# PRIMITIVE TYPES & BASE CLASSES
# =============================================================================

@dataclass(frozen=True)
class TimeRange:
    """Represents a time range with start and end in milliseconds."""
    start_ms: int = 0
    end_ms: int = 0
    
    def __post_init__(self):
        if self.start_ms < 0:
            raise ValueError("start_ms must be non-negative")
        if self.end_ms < self.start_ms:
            raise ValueError("end_ms must be >= start_ms")
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms
    
    @property
    def duration_seconds(self) -> float:
        return self.duration_ms / 1000.0
    
    def overlaps(self, other: TimeRange) -> bool:
        return self.start_ms < other.end_ms and other.start_ms < self.end_ms
    
    def contains(self, time_ms: int) -> bool:
        return self.start_ms <= time_ms <= self.end_ms
    
    def to_dict(self) -> Dict[str, Any]:
        return {"start_ms": self.start_ms, "end_ms": self.end_ms}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimeRange:
        return cls(start_ms=data["start_ms"], end_ms=data["end_ms"])


@dataclass(frozen=True)
class SpatialRect:
    """Represents a 2D rectangle with position and size."""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpatialRect:
        return cls(
            x=data.get("x", 0.0), y=data.get("y", 0.0),
            width=data.get("width", 0.0), height=data.get("height", 0.0)
        )


class EntityType(Enum):
    """All entity types in the knowledge graph."""
    WORKSPACE = auto()
    PROJECT = auto()
    LIBRARY = auto()
    ASSET = auto()
    SEQUENCE = auto()
    TIMELINE = auto()
    TRACK = auto()
    CLIP = auto()
    EFFECT = auto()
    GENERATOR = auto()
    KEYFRAME = auto()
    METADATA = auto()
    AI_CONTEXT = auto()
    RELATIONSHIP = auto()


T = TypeVar('T', bound='Entity')


@dataclass(frozen=True)
class EntityId:
    """Unique identifier for any entity in the graph."""
    value: UUID
    entity_type: EntityType
    
    def __str__(self) -> str:
        return f"{self.entity_type.name}:{self.value}"
    
    def to_dict(self) -> Dict[str, str]:
        return {"value": str(self.value), "entity_type": self.entity_type.name}
    
    @classmethod
    def new(cls, entity_type: EntityType) -> EntityId:
        return cls(value=uuid4(), entity_type=entity_type)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EntityId:
        return cls(
            value=UUID(data["value"]),
            entity_type=EntityType[data["entity_type"]]
        )


@dataclass(frozen=True)
class MetadataEntry:
    """A single metadata entry with key, value, and optional schema."""
    key: str
    value: Any
    schema_type: Optional[str] = None  # e.g., "string", "number", "color", "tag"
    namespace: str = "default"  # For namespacing metadata (e.g., "ai", "user", "system")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "schema_type": self.schema_type,
            "namespace": self.namespace
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MetadataEntry:
        return cls(
            key=data["key"],
            value=data["value"],
            schema_type=data.get("schema_type"),
            namespace=data.get("namespace", "default")
        )


@dataclass(frozen=True)
class Entity(ABC):
    """
    Base class for all entities in the knowledge graph.
    
    All entities are immutable. To modify an entity, create a new instance
    with the desired changes using a Command pattern.
    """
    id: EntityId
    created_at: datetime
    updated_at: datetime
    metadata: tuple[MetadataEntry, ...] = field(default_factory=tuple)
    
    @property
    @abstractmethod
    def entity_type(self) -> EntityType:
        pass
    
    def get_metadata(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get metadata value by key and namespace."""
        for entry in self.metadata:
            if entry.key == key and entry.namespace == namespace:
                return entry.value
        return None
    
    def with_metadata(self, entry: MetadataEntry) -> 'Entity':
        """Return a new entity with added/updated metadata."""
        new_metadata = tuple(
            e for e in self.metadata 
            if not (e.key == entry.key and e.namespace == entry.namespace)
        ) + (entry,)
        return self._replace(metadata=new_metadata)
    
    def _replace(self, **kwargs) -> 'Entity':
        """Create a modified copy of this entity."""
        return type(self)(**{**self.__dict__, **kwargs})
    
    def to_base_dict(self) -> Dict[str, Any]:
        """Serialize base entity fields."""
        return {
            "id": self.id.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": [m.to_dict() for m in self.metadata],
            "entity_type": self.entity_type.name
        }


# =============================================================================
# CORE DOMAIN ENTITIES
# =============================================================================

@dataclass(frozen=True)
class Workspace(Entity):
    """
    Top-level container representing a user's workspace.
    
    A workspace contains multiple projects and libraries.
    It represents the highest level of organization.
    """
    name: str = "Untitled Workspace"
    description: str = ""
    project_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    library_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.WORKSPACE
    
    def add_project(self, project_id: EntityId) -> 'Workspace':
        if project_id in self.project_ids:
            return self
        return self._replace(
            project_ids=self.project_ids + (project_id,),
            updated_at=datetime.now()
        )
    
    def remove_project(self, project_id: EntityId) -> 'Workspace':
        return self._replace(
            project_ids=tuple(p for p in self.project_ids if p != project_id),
            updated_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "description": self.description,
            "project_ids": [pid.to_dict() for pid in self.project_ids],
            "library_ids": [lid.to_dict() for lid in self.library_ids],
            "settings": self.settings
        }
    
    @classmethod
    def create(cls, name: str = "Untitled Workspace") -> 'Workspace':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.WORKSPACE),
            created_at=now,
            updated_at=now,
            name=name
        )


@dataclass(frozen=True)
class Library(Entity):
    """
    A collection of assets that can be shared across projects.
    
    Libraries enable asset reuse and organization independent of specific projects.
    """
    name: str = "Untitled Library"
    description: str = ""
    asset_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.LIBRARY
    
    def add_asset(self, asset_id: EntityId) -> 'Library':
        if asset_id in self.asset_ids:
            return self
        return self._replace(
            asset_ids=self.asset_ids + (asset_id,),
            updated_at=datetime.now()
        )
    
    def remove_asset(self, asset_id: EntityId) -> 'Library':
        return self._replace(
            asset_ids=tuple(a for a in self.asset_ids if a != asset_id),
            updated_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "description": self.description,
            "asset_ids": [aid.to_dict() for aid in self.asset_ids],
            "tags": list(self.tags)
        }
    
    @classmethod
    def create(cls, name: str = "Untitled Library") -> 'Library':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.LIBRARY),
            created_at=now,
            updated_at=now,
            name=name
        )


class AssetType(Enum):
    VIDEO = auto()
    AUDIO = auto()
    IMAGE = auto()
    FONT = auto()
    LUT = auto()
    PRESET = auto()
    COMPOUND = auto()  # A compound clip (nested sequence)
    GENERATED = auto()  # AI-generated content


@dataclass(frozen=True)
class AssetSource:
    """Describes the source of an asset."""
    uri: str  # File path or URL
    source_type: str = "file"  # file, url, generated, stream
    format: Optional[str] = None
    codec: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None  # SHA256 for integrity verification
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uri": self.uri,
            "source_type": self.source_type,
            "format": self.format,
            "codec": self.codec,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AssetSource:
        return cls(
            uri=data["uri"],
            source_type=data.get("source_type", "file"),
            format=data.get("format"),
            codec=data.get("codec"),
            size_bytes=data.get("size_bytes"),
            checksum=data.get("checksum")
        )


@dataclass(frozen=True)
class AssetMetadata:
    """Technical metadata specific to different asset types."""
    asset_type: AssetType
    duration_ms: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_rate: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    color_space: Optional[str] = None
    has_alpha: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_type": self.asset_type.name,
            "duration_ms": self.duration_ms,
            "width": self.width,
            "height": self.height,
            "frame_rate": self.frame_rate,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "color_space": self.color_space,
            "has_alpha": self.has_alpha
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AssetMetadata:
        return cls(
            asset_type=AssetType[data["asset_type"]],
            duration_ms=data.get("duration_ms"),
            width=data.get("width"),
            height=data.get("height"),
            frame_rate=data.get("frame_rate"),
            sample_rate=data.get("sample_rate"),
            channels=data.get("channels"),
            color_space=data.get("color_space"),
            has_alpha=data.get("has_alpha", False)
        )


@dataclass(frozen=True)
class Asset(Entity):
    """
    Represents media or resources that can be used in projects.
    
    Assets are the fundamental building blocks - video files, audio files,
    images, fonts, LUTs, presets, and AI-generated content.
    """
    name: str = "Untitled Asset"
    source: Optional[AssetSource] = None
    asset_metadata: Optional[AssetMetadata] = None
    library_id: Optional[EntityId] = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    thumbnail_uri: Optional[str] = None
    ai_embeddings: Optional[Dict[str, Any]] = None  # Vector embeddings for semantic search
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.ASSET
    
    def with_name(self, name: str) -> 'Asset':
        return self._replace(name=name, updated_at=datetime.now())
    
    def with_thumbnail(self, uri: str) -> 'Asset':
        return self._replace(thumbnail_uri=uri, updated_at=datetime.now())
    
    def with_embeddings(self, embeddings: Dict[str, Any]) -> 'Asset':
        return self._replace(ai_embeddings=embeddings, updated_at=datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "source": self.source.to_dict() if self.source else None,
            "asset_metadata": self.asset_metadata.to_dict() if self.asset_metadata else None,
            "library_id": self.library_id.to_dict() if self.library_id else None,
            "tags": list(self.tags),
            "thumbnail_uri": self.thumbnail_uri,
            "ai_embeddings": self.ai_embeddings
        }
    
    @classmethod
    def create(
        cls,
        name: str,
        source: AssetSource,
        asset_metadata: Optional[AssetMetadata] = None
    ) -> 'Asset':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.ASSET),
            created_at=now,
            updated_at=now,
            name=name,
            source=source,
            asset_metadata=asset_metadata
        )


@dataclass(frozen=True)
class Project(Entity):
    """
    A project contains sequences and references to assets.
    
    Projects are the primary organizational unit for editing work.
    """
    name: str = "Untitled Project"
    description: str = ""
    sequence_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    active_sequence_id: Optional[EntityId] = None
    workspace_id: Optional[EntityId] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.PROJECT
    
    def add_sequence(self, sequence_id: EntityId) -> 'Project':
        if sequence_id in self.sequence_ids:
            return self
        new_sequences = self.sequence_ids + (sequence_id,)
        active = self.active_sequence_id or sequence_id
        return self._replace(
            sequence_ids=new_sequences,
            active_sequence_id=active,
            updated_at=datetime.now()
        )
    
    def set_active_sequence(self, sequence_id: EntityId) -> 'Project':
        if sequence_id not in self.sequence_ids:
            raise ValueError(f"Sequence {sequence_id} not in project")
        return self._replace(
            active_sequence_id=sequence_id,
            updated_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "description": self.description,
            "sequence_ids": [sid.to_dict() for sid in self.sequence_ids],
            "active_sequence_id": self.active_sequence_id.to_dict() if self.active_sequence_id else None,
            "workspace_id": self.workspace_id.to_dict() if self.workspace_id else None,
            "settings": self.settings
        }
    
    @classmethod
    def create(cls, name: str = "Untitled Project") -> 'Project':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.PROJECT),
            created_at=now,
            updated_at=now,
            name=name
        )


@dataclass(frozen=True)
class TimelineSettings:
    """Configuration for timeline behavior and appearance."""
    frame_rate: float = 24.0
    width: int = 1920
    height: int = 1080
    pixel_aspect_ratio: float = 1.0
    display_format: str = "timecode"  # timecode, frames, seconds, percentage
    start_timecode: str = "00:00:00:00"
    drop_frame: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_rate": self.frame_rate,
            "width": self.width,
            "height": self.height,
            "pixel_aspect_ratio": self.pixel_aspect_ratio,
            "display_format": self.display_format,
            "start_timecode": self.start_timecode,
            "drop_frame": self.drop_frame
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimelineSettings:
        return cls(
            frame_rate=data.get("frame_rate", 24.0),
            width=data.get("width", 1920),
            height=data.get("height", 1080),
            pixel_aspect_ratio=data.get("pixel_aspect_ratio", 1.0),
            display_format=data.get("display_format", "timecode"),
            start_timecode=data.get("start_timecode", "00:00:00:00"),
            drop_frame=data.get("drop_frame", False)
        )


@dataclass(frozen=True)
class Timeline(Entity):
    """
    The timeline represents the temporal arrangement of tracks and clips.
    
    A timeline has settings (resolution, framerate) and contains multiple tracks.
    This is separate from Sequence to allow for nested timelines and variations.
    """
    name: str = "Timeline"
    settings: TimelineSettings = field(default_factory=TimelineSettings)
    track_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    duration_ms: int = 0
    sequence_id: Optional[EntityId] = None
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.TIMELINE
    
    def add_track(self, track_id: EntityId, index: Optional[int] = None) -> 'Timeline':
        if track_id in self.track_ids:
            return self
        if index is None:
            new_tracks = self.track_ids + (track_id,)
        else:
            tracks_list = list(self.track_ids)
            tracks_list.insert(index, track_id)
            new_tracks = tuple(tracks_list)
        return self._replace(
            track_ids=new_tracks,
            updated_at=datetime.now()
        )
    
    def remove_track(self, track_id: EntityId) -> 'Timeline':
        return self._replace(
            track_ids=tuple(t for t in self.track_ids if t != track_id),
            updated_at=datetime.now()
        )
    
    def update_duration(self, duration_ms: int) -> 'Timeline':
        return self._replace(duration_ms=duration_ms, updated_at=datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "settings": self.settings.to_dict(),
            "track_ids": [tid.to_dict() for tid in self.track_ids],
            "duration_ms": self.duration_ms,
            "sequence_id": self.sequence_id.to_dict() if self.sequence_id else None
        }
    
    @classmethod
    def create(
        cls,
        name: str = "Timeline",
        settings: Optional[TimelineSettings] = None
    ) -> 'Timeline':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.TIMELINE),
            created_at=now,
            updated_at=now,
            name=name,
            settings=settings or TimelineSettings()
        )


class TrackType(Enum):
    VIDEO = auto()
    AUDIO = auto()
    SUBTITLE = auto()
    GRAPHICS = auto()
    ADJUSTMENT = auto()  # Adjustment layer
    MASTER = auto()


@dataclass(frozen=True)
class Track(Entity):
    """
    A track within a timeline that holds clips.
    
    Tracks can be video, audio, subtitle, graphics, or adjustment layers.
    """
    name: str = "Track"
    track_type: TrackType = TrackType.VIDEO
    timeline_id: Optional[EntityId] = None
    clip_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    is_locked: bool = False
    is_muted: bool = False  # For audio tracks
    is_visible: bool = True  # For video tracks
    volume: float = 1.0  # 0.0 to 1.0
    pan: float = 0.0  # -1.0 (left) to 1.0 (right)
    height: int = 100  # UI track height in pixels
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.TRACK
    
    def add_clip(self, clip_id: EntityId, index: Optional[int] = None) -> 'Track':
        if clip_id in self.clip_ids:
            return self
        if index is None:
            new_clips = self.clip_ids + (clip_id,)
        else:
            clips_list = list(self.clip_ids)
            clips_list.insert(index, clip_id)
            new_clips = tuple(clips_list)
        return self._replace(
            clip_ids=new_clips,
            updated_at=datetime.now()
        )
    
    def remove_clip(self, clip_id: EntityId) -> 'Track':
        return self._replace(
            clip_ids=tuple(c for c in self.clip_ids if c != clip_id),
            updated_at=datetime.now()
        )
    
    def lock(self) -> 'Track':
        return self._replace(is_locked=True, updated_at=datetime.now())
    
    def unlock(self) -> 'Track':
        return self._replace(is_locked=False, updated_at=datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "track_type": self.track_type.name,
            "timeline_id": self.timeline_id.to_dict() if self.timeline_id else None,
            "clip_ids": [cid.to_dict() for cid in self.clip_ids],
            "is_locked": self.is_locked,
            "is_muted": self.is_muted,
            "is_visible": self.is_visible,
            "volume": self.volume,
            "pan": self.pan,
            "height": self.height
        }
    
    @classmethod
    def create(
        cls,
        name: str = "Track",
        track_type: TrackType = TrackType.VIDEO
    ) -> 'Track':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.TRACK),
            created_at=now,
            updated_at=now,
            name=name,
            track_type=track_type
        )


class ClipType(Enum):
    PRIMARY = auto()  # Main media clip
    CONNECTED = auto()  # Connected to primary (e.g., audio attached to video)
    COMPOUND = auto()  # Nested sequence
    GENERATOR = auto()  # Generated content (solid, gradient, etc.)
    TITLE = auto()  # Text title
    TRANSITION = auto()  # Transition between clips
    ADJUSTMENT = auto()  # Adjustment clip
    SLICE = auto()  # A slice/subset of an asset


@dataclass(frozen=True)
class ClipSource:
    """Describes what media a clip uses."""
    asset_id: Optional[EntityId] = None
    time_range: Optional[TimeRange] = None  # Source time range in the asset
    speed_multiplier: float = 1.0  # Playback speed (0.5 = slow-mo, 2.0 = fast)
    is_frozen: bool = False
    freeze_frame_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id.to_dict() if self.asset_id else None,
            "time_range": self.time_range.to_dict() if self.time_range else None,
            "speed_multiplier": self.speed_multiplier,
            "is_frozen": self.is_frozen,
            "freeze_frame_time_ms": self.freeze_frame_time_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClipSource:
        return cls(
            asset_id=EntityId.from_dict(data["asset_id"]) if data.get("asset_id") else None,
            time_range=TimeRange.from_dict(data["time_range"]) if data.get("time_range") else None,
            speed_multiplier=data.get("speed_multiplier", 1.0),
            is_frozen=data.get("is_frozen", False),
            freeze_frame_time_ms=data.get("freeze_frame_time_ms")
        )


@dataclass(frozen=True)
class Transform:
    """Spatial and temporal transform properties for a clip."""
    position_x: float = 0.0
    position_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0  # degrees
    anchor_x: float = 0.5  # 0-1 relative to width
    anchor_y: float = 0.5  # 0-1 relative to height
    opacity: float = 1.0  # 0.0 to 1.0
    blend_mode: str = "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_x": self.position_x,
            "position_y": self.position_y,
            "scale_x": self.scale_x,
            "scale_y": self.scale_y,
            "rotation": self.rotation,
            "anchor_x": self.anchor_x,
            "anchor_y": self.anchor_y,
            "opacity": self.opacity,
            "blend_mode": self.blend_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Transform:
        return cls(
            position_x=data.get("position_x", 0.0),
            position_y=data.get("position_y", 0.0),
            scale_x=data.get("scale_x", 1.0),
            scale_y=data.get("scale_y", 1.0),
            rotation=data.get("rotation", 0.0),
            anchor_x=data.get("anchor_x", 0.5),
            anchor_y=data.get("anchor_y", 0.5),
            opacity=data.get("opacity", 1.0),
            blend_mode=data.get("blend_mode", "normal")
        )


@dataclass(frozen=True)
class Clip(Entity):
    """
    A clip on a timeline track.
    
    Clips reference assets and define how they appear in the timeline
    (time range, transforms, effects, etc.).
    """
    name: str = "Clip"
    clip_type: ClipType = ClipType.PRIMARY
    track_id: Optional[EntityId] = None
    timeline_position_ms: int = 0
    duration_ms: int = 0
    source: Optional[ClipSource] = None
    transform: Transform = field(default_factory=Transform)
    effect_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    is_selected: bool = False
    compound_sequence_id: Optional[EntityId] = None  # For compound clips
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.CLIP
    
    @property
    def time_range(self) -> TimeRange:
        return TimeRange(
            start_ms=self.timeline_position_ms,
            end_ms=self.timeline_position_ms + self.duration_ms
        )
    
    def move_to(self, position_ms: int) -> 'Clip':
        return self._replace(
            timeline_position_ms=position_ms,
            updated_at=datetime.now()
        )
    
    def trim_start(self, delta_ms: int) -> 'Clip':
        new_pos = self.timeline_position_ms + delta_ms
        new_duration = self.duration_ms - delta_ms
        if new_duration <= 0:
            raise ValueError("Cannot trim to zero or negative duration")
        return self._replace(
            timeline_position_ms=new_pos,
            duration_ms=new_duration,
            updated_at=datetime.now()
        )
    
    def trim_end(self, delta_ms: int) -> 'Clip':
        new_duration = self.duration_ms + delta_ms
        if new_duration <= 0:
            raise ValueError("Cannot trim to zero or negative duration")
        return self._replace(
            duration_ms=new_duration,
            updated_at=datetime.now()
        )
    
    def add_effect(self, effect_id: EntityId) -> 'Clip':
        return self._replace(
            effect_ids=self.effect_ids + (effect_id,),
            updated_at=datetime.now()
        )
    
    def remove_effect(self, effect_id: EntityId) -> 'Clip':
        return self._replace(
            effect_ids=tuple(e for e in self.effect_ids if e != effect_id),
            updated_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "clip_type": self.clip_type.name,
            "track_id": self.track_id.to_dict() if self.track_id else None,
            "timeline_position_ms": self.timeline_position_ms,
            "duration_ms": self.duration_ms,
            "source": self.source.to_dict() if self.source else None,
            "transform": self.transform.to_dict(),
            "effect_ids": [eid.to_dict() for eid in self.effect_ids],
            "is_selected": self.is_selected,
            "compound_sequence_id": self.compound_sequence_id.to_dict() if self.compound_sequence_id else None
        }
    
    @classmethod
    def create(
        cls,
        name: str = "Clip",
        clip_type: ClipType = ClipType.PRIMARY,
        duration_ms: int = 0
    ) -> 'Clip':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.CLIP),
            created_at=now,
            updated_at=now,
            name=name,
            clip_type=clip_type,
            duration_ms=duration_ms
        )


class EffectType(Enum):
    COLOR_CORRECTION = auto()
    BLUR = auto()
    SHARPEN = auto()
    DISTORTION = auto()
    KEYING = auto()
    STABILIZATION = auto()
    NOISE_REDUCTION = auto()
    AUDIO_FILTER = auto()
    AUDIO_EFFECT = auto()
    TRANSITION = auto()
    GENERATOR = auto()
    CUSTOM = auto()


@dataclass(frozen=True)
class EffectParameters:
    """Effect-specific parameters."""
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"params": self.params}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EffectParameters:
        return cls(params=data.get("params", {}))


@dataclass(frozen=True)
class Effect(Entity):
    """
    An effect applied to a clip or track.
    
    Effects can be color corrections, blurs, transitions, audio filters, etc.
    """
    name: str = "Effect"
    effect_type: EffectType = EffectType.CUSTOM
    clip_id: Optional[EntityId] = None
    track_id: Optional[EntityId] = None
    parameters: EffectParameters = field(default_factory=EffectParameters)
    is_enabled: bool = True
    order: int = 0  # Rendering order
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.EFFECT
    
    def with_parameters(self, params: Dict[str, Any]) -> 'Effect':
        return self._replace(
            parameters=EffectParameters(params=params),
            updated_at=datetime.now()
        )
    
    def enable(self) -> 'Effect':
        return self._replace(is_enabled=True, updated_at=datetime.now())
    
    def disable(self) -> 'Effect':
        return self._replace(is_enabled=False, updated_at=datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "effect_type": self.effect_type.name,
            "clip_id": self.clip_id.to_dict() if self.clip_id else None,
            "track_id": self.track_id.to_dict() if self.track_id else None,
            "parameters": self.parameters.to_dict(),
            "is_enabled": self.is_enabled,
            "order": self.order
        }
    
    @classmethod
    def create(
        cls,
        name: str = "Effect",
        effect_type: EffectType = EffectType.CUSTOM
    ) -> 'Effect':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.EFFECT),
            created_at=now,
            updated_at=now,
            name=name,
            effect_type=effect_type
        )


@dataclass(frozen=True)
class Generator(Entity):
    """
    A generator creates synthetic content (solids, gradients, patterns).
    
    Generators are like clips but don't reference external assets.
    """
    name: str = "Generator"
    generator_type: str = "solid"  # solid, gradient, checkerboard, noise, etc.
    duration_ms: int = 5000
    width: int = 1920
    height: int = 1080
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.GENERATOR
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "generator_type": self.generator_type,
            "duration_ms": self.duration_ms,
            "width": self.width,
            "height": self.height,
            "parameters": self.parameters
        }
    
    @classmethod
    def create(
        cls,
        name: str = "Generator",
        generator_type: str = "solid",
        duration_ms: int = 5000
    ) -> 'Generator':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.GENERATOR),
            created_at=now,
            updated_at=now,
            name=name,
            generator_type=generator_type,
            duration_ms=duration_ms
        )


@dataclass(frozen=True)
class Keyframe(Entity):
    """
    A keyframe for animating effect parameters over time.
    
    Keyframes enable smooth animations and dynamic changes.
    """
    name: str = "Keyframe"
    effect_id: Optional[EntityId] = None
    parameter_name: str = ""
    time_ms: int = 0
    value: Any = None
    interpolation: str = "linear"  # linear, ease-in, ease-out, bezier, hold
    bezier_in: Optional[tuple[float, float]] = None
    bezier_out: Optional[tuple[float, float]] = None
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.KEYFRAME
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "effect_id": self.effect_id.to_dict() if self.effect_id else None,
            "parameter_name": self.parameter_name,
            "time_ms": self.time_ms,
            "value": self.value,
            "interpolation": self.interpolation,
            "bezier_in": list(self.bezier_in) if self.bezier_in else None,
            "bezier_out": list(self.bezier_out) if self.bezier_out else None
        }
    
    @classmethod
    def create(
        cls,
        parameter_name: str,
        time_ms: int,
        value: Any
    ) -> 'Keyframe':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.KEYFRAME),
            created_at=now,
            updated_at=now,
            parameter_name=parameter_name,
            time_ms=time_ms,
            value=value
        )


@dataclass(frozen=True)
class Sequence(Entity):
    """
    A sequence represents an editable arrangement of clips.
    
    Sequences can be nested (compound clips) and contain timelines.
    This enables unlimited nesting and complex project structures.
    """
    name: str = "Sequence"
    timeline_id: Optional[EntityId] = None
    project_id: Optional[EntityId] = None
    parent_sequence_id: Optional[EntityId] = None  # For nested sequences
    child_sequence_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.SEQUENCE
    
    def with_timeline(self, timeline_id: EntityId) -> 'Sequence':
        return self._replace(timeline_id=timeline_id, updated_at=datetime.now())
    
    def add_child_sequence(self, sequence_id: EntityId) -> 'Sequence':
        if sequence_id in self.child_sequence_ids:
            return self
        return self._replace(
            child_sequence_ids=self.child_sequence_ids + (sequence_id,),
            updated_at=datetime.now()
        )
    
    def remove_child_sequence(self, sequence_id: EntityId) -> 'Sequence':
        return self._replace(
            child_sequence_ids=tuple(s for s in self.child_sequence_ids if s != sequence_id),
            updated_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "timeline_id": self.timeline_id.to_dict() if self.timeline_id else None,
            "project_id": self.project_id.to_dict() if self.project_id else None,
            "parent_sequence_id": self.parent_sequence_id.to_dict() if self.parent_sequence_id else None,
            "child_sequence_ids": [sid.to_dict() for sid in self.child_sequence_ids]
        }
    
    @classmethod
    def create(cls, name: str = "Sequence") -> 'Sequence':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.SEQUENCE),
            created_at=now,
            updated_at=now,
            name=name
        )


@dataclass(frozen=True)
class Relationship(Entity):
    """
    A relationship between two entities in the graph.
    
    Relationships enable semantic connections beyond simple parent-child hierarchies.
    """
    # Note: Parent Entity class has: id, created_at, updated_at (no defaults), metadata (has default)
    # So we need to put our required fields BEFORE metadata in the MRO, but since we inherit,
    # we must have all our required fields with defaults OR use field(init=True) trick
    
    # Override to reorder - put required fields first using __post_init__ approach
    source_id: EntityId = field(default=None, init=True)
    target_id: EntityId = field(default=None, init=True)
    relationship_type: str = field(default="", init=True)
    name: str = "Relationship"
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.source_id is None:
            raise ValueError("source_id is required")
        if self.target_id is None:
            raise ValueError("target_id is required")
        if not self.relationship_type:
            raise ValueError("relationship_type is required")
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.RELATIONSHIP
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "source_id": self.source_id.to_dict(),
            "target_id": self.target_id.to_dict(),
            "relationship_type": self.relationship_type,
            "properties": self.properties
        }
    
    @classmethod
    def create(
        cls,
        source_id: EntityId,
        target_id: EntityId,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> 'Relationship':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.RELATIONSHIP),
            created_at=now,
            updated_at=now,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {}
        )


@dataclass(frozen=True)
class AIContext(Entity):
    """
    Context information for AI operations.
    
    Stores prompts, model configurations, generation parameters, and results.
    """
    name: str = "AI Context"
    operation_type: str  # e.g., "generate_video", "edit_timeline", "analyze_content"
    prompt: Optional[str] = None
    model_config: Dict[str, Any] = field(default_factory=dict)
    input_entity_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    output_entity_ids: tuple[EntityId, ...] = field(default_factory=tuple)
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    
    @property
    def entity_type(self) -> EntityType:
        return EntityType.AI_CONTEXT
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.to_base_dict(),
            "name": self.name,
            "operation_type": self.operation_type,
            "prompt": self.prompt,
            "model_config": self.model_config,
            "input_entity_ids": [eid.to_dict() for eid in self.input_entity_ids],
            "output_entity_ids": [eid.to_dict() for eid in self.output_entity_ids],
            "result_data": self.result_data,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms
        }
    
    @classmethod
    def create(
        cls,
        operation_type: str,
        prompt: Optional[str] = None
    ) -> 'AIContext':
        now = datetime.now()
        return cls(
            id=EntityId.new(EntityType.AI_CONTEXT),
            created_at=now,
            updated_at=now,
            operation_type=operation_type,
            prompt=prompt
        )


# =============================================================================
# EXPORT FOR BACKWARD COMPATIBILITY
# =============================================================================

def export_for_backward_compatibility(project: Project, entities: Dict[str, Entity]) -> Dict[str, Any]:
    """
    Export project in a format compatible with legacy simple hierarchy.
    
    This enables reading old project files while using the new graph structure.
    """
    return {
        "version": "1.0-graph",
        "legacy_compatible": True,
        "project": project.to_dict(),
        "entities": {k: v.to_dict() for k, v in entities.items()}
    }


__all__ = [
    # Primitives
    'TimeRange',
    'SpatialRect',
    'EntityType',
    'EntityId',
    'MetadataEntry',
    'Entity',
    
    # Core entities
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
    
    # Utilities
    'export_for_backward_compatibility'
]
