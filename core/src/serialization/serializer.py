"""
EditFlow AI - Serialization

Serialization and deserialization of the knowledge graph to various formats.
Supports backward compatibility with legacy project files.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from ..models.entities import (
    Entity, EntityId, EntityType,
    Workspace, Project, Library, Asset, Sequence, Timeline, Track, Clip, Effect,
    Generator, Keyframe, Relationship, AIContext,
    export_for_backward_compatibility
)
from ..graph.knowledge_graph import KnowledgeGraph


class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = auto()
    JSON_PRETTY = auto()
    BINARY = auto()  # Reserved for future use
    LEGACY = auto()  # Legacy simple hierarchy format


@dataclass
class SerializationOptions:
    """Options controlling serialization behavior."""
    format: SerializationFormat = SerializationFormat.JSON
    include_metadata: bool = True
    include_relationships: bool = True
    include_history: bool = False
    pretty_print: bool = False
    compression: bool = False
    version: str = "1.0-graph"


@dataclass
class DeserializationResult:
    """Result of deserializing a project file."""
    success: bool
    graph: Optional[KnowledgeGraph] = None
    workspace: Optional[Workspace] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    migrated_from_version: Optional[str] = None
    
    @classmethod
    def ok(
        cls,
        graph: KnowledgeGraph,
        workspace: Optional[Workspace] = None,
        migrated_from: Optional[str] = None
    ) -> 'DeserializationResult':
        return cls(
            success=True,
            graph=graph,
            workspace=workspace,
            migrated_from_version=migrated_from
        )
    
    @classmethod
    def fail(cls, errors: List[str]) -> 'DeserializationResult':
        return cls(success=False, errors=errors)


class GraphSerializer:
    """
    Serializes and deserializes the knowledge graph.
    
    Supports multiple formats and backward compatibility.
    """
    
    CURRENT_VERSION = "1.0-graph"
    LEGACY_VERSIONS = ["0.1.0", "0.2.0"]
    
    def __init__(self, options: Optional[SerializationOptions] = None):
        self.options = options or SerializationOptions()
    
    def serialize(self, graph: KnowledgeGraph, workspace: Optional[Workspace] = None) -> str:
        """Serialize the graph to a string."""
        if self.options.format == SerializationFormat.LEGACY:
            return self._serialize_legacy(graph, workspace)
        
        data = self._build_serialization_dict(graph, workspace)
        
        if self.options.format == SerializationFormat.JSON_PRETTY:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    def serialize_to_file(
        self,
        graph: KnowledgeGraph,
        workspace: Optional[Workspace],
        path: Union[str, Path]
    ) -> None:
        """Serialize the graph to a file."""
        content = self.serialize(graph, workspace)
        
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def deserialize(self, content: str) -> DeserializationResult:
        """Deserialize from a string."""
        try:
            data = json.loads(content)
            return self._deserialize_dict(data)
        except json.JSONDecodeError as e:
            return DeserializationResult.fail([f"Invalid JSON: {e}"])
        except Exception as e:
            return DeserializationResult.fail([f"Deserialization error: {e}"])
    
    def deserialize_from_file(self, path: Union[str, Path]) -> DeserializationResult:
        """Deserialize from a file."""
        try:
            with open(Path(path), 'r', encoding='utf-8') as f:
                content = f.read()
            return self.deserialize(content)
        except FileNotFoundError:
            return DeserializationResult.fail([f"File not found: {path}"])
        except Exception as e:
            return DeserializationResult.fail([f"File read error: {e}"])
    
    def _build_serialization_dict(
        self,
        graph: KnowledgeGraph,
        workspace: Optional[Workspace]
    ) -> Dict[str, Any]:
        """Build the serialization dictionary."""
        entities = {}
        
        for entity in graph.get_all_entities():
            key = str(entity.id)
            entities[key] = entity.to_dict()
        
        data = {
            "version": self.options.version,
            "format": "knowledge-graph",
            "serialized_at": datetime.now().isoformat(),
            "workspace": workspace.to_dict() if workspace else None,
            "entities": entities,
            "entity_count": graph.get_entity_count()
        }
        
        return data
    
    def _serialize_legacy(
        self,
        graph: KnowledgeGraph,
        workspace: Optional[Workspace]
    ) -> str:
        """Serialize in legacy format for backward compatibility."""
        # Find the main project
        projects = graph.get_entities_by_type(EntityType.PROJECT)
        project = projects[0] if projects else None
        
        if project:
            data = export_for_backward_compatibility(project, {
                str(e.id): e for e in graph.get_all_entities()
            })
        else:
            data = {
                "version": self.CURRENT_VERSION,
                "legacy_compatible": True,
                "project": None,
                "entities": {}
            }
        
        if self.options.pretty_print:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    
    def _deserialize_dict(self, data: Dict[str, Any]) -> DeserializationResult:
        """Deserialize from a dictionary."""
        version = data.get("version", "unknown")
        errors = []
        warnings = []
        
        # Check version and handle migration
        if version in self.LEGACY_VERSIONS:
            return self._migrate_legacy(data)
        
        if version != self.CURRENT_VERSION:
            warnings.append(f"Unknown version: {version}. Attempting to deserialize anyway.")
        
        # Create new graph
        graph = KnowledgeGraph()
        workspace = None
        
        # Deserialize workspace first
        workspace_data = data.get("workspace")
        if workspace_data:
            try:
                workspace = self._deserialize_workspace(workspace_data)
                graph.add_entity(workspace)
            except Exception as e:
                errors.append(f"Failed to deserialize workspace: {e}")
        
        # Deserialize entities
        entities_data = data.get("entities", {})
        entity_map: Dict[str, Entity] = {}
        
        # First pass: create all entities
        for key, entity_data in entities_data.items():
            try:
                entity = self._deserialize_entity(entity_data)
                if entity:
                    entity_map[key] = entity
            except Exception as e:
                errors.append(f"Failed to deserialize entity {key}: {e}")
        
        # Second pass: add to graph (relationships may reference other entities)
        for key, entity in entity_map.items():
            try:
                graph.add_entity(entity)
            except Exception as e:
                errors.append(f"Failed to add entity {key} to graph: {e}")
        
        if errors:
            return DeserializationResult.fail(errors)
        
        return DeserializationResult.ok(graph, workspace)
    
    def _migrate_legacy(self, data: Dict[str, Any]) -> DeserializationResult:
        """Migrate from legacy format to current graph format."""
        warnings = []
        errors = []
        
        version = data.get("version", "unknown")
        warnings.append(f"Migrating from legacy version: {version}")
        
        graph = KnowledgeGraph()
        
        # Try to extract project data
        project_data = data.get("project")
        if project_data:
            try:
                project = self._deserialize_project_legacy(project_data)
                if project:
                    graph.add_entity(project)
            except Exception as e:
                errors.append(f"Failed to migrate project: {e}")
        
        # Migrate entities
        entities_data = data.get("entities", {})
        for key, entity_data in entities_data.items():
            try:
                entity = self._deserialize_entity(entity_data)
                if entity:
                    graph.add_entity(entity)
            except Exception as e:
                errors.append(f"Failed to migrate entity {key}: {e}")
        
        if errors:
            return DeserializationResult.fail(errors)
        
        return DeserializationResult.ok(graph, migrated_from=version)
    
    def _deserialize_workspace(self, data: Dict[str, Any]) -> Workspace:
        """Deserialize a Workspace entity."""
        from ..models.entities import MetadataEntry
        
        now = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        updated = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else now
        
        metadata = tuple(
            MetadataEntry(
                key=m["key"],
                value=m["value"],
                schema_type=m.get("schema_type"),
                namespace=m.get("namespace", "default")
            )
            for m in data.get("metadata", [])
        )
        
        return Workspace(
            id=EntityId.from_dict(data["id"]),
            created_at=now,
            updated_at=updated,
            metadata=metadata,
            name=data.get("name", "Untitled Workspace"),
            description=data.get("description", ""),
            project_ids=tuple(
                EntityId.from_dict(pid) for pid in data.get("project_ids", [])
            ),
            library_ids=tuple(
                EntityId.from_dict(lid) for lid in data.get("library_ids", [])
            ),
            settings=data.get("settings", {})
        )
    
    def _deserialize_project_legacy(self, data: Dict[str, Any]) -> Optional[Project]:
        """Deserialize a Project from legacy format."""
        # Simple migration - create a basic project
        return Project.create(name=data.get("name", "Migrated Project"))
    
    def _deserialize_entity(self, data: Dict[str, Any]) -> Optional[Entity]:
        """Deserialize an entity based on its type."""
        from ..models.entities import MetadataEntry
        
        entity_type_name = data.get("entity_type")
        if not entity_type_name:
            return None
        
        try:
            entity_type = EntityType[entity_type_name]
        except KeyError:
            return None
        
        now = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        updated = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else now
        
        metadata = tuple(
            MetadataEntry(
                key=m["key"],
                value=m["value"],
                schema_type=m.get("schema_type"),
                namespace=m.get("namespace", "default")
            )
            for m in data.get("metadata", [])
        )
        
        base_kwargs = {
            "id": EntityId.from_dict(data["id"]),
            "created_at": now,
            "updated_at": updated,
            "metadata": metadata
        }
        
        # Dispatch to specific deserializer based on type
        deserializers = {
            EntityType.WORKSPACE: self._deserialize_workspace_full,
            EntityType.PROJECT: self._deserialize_project_full,
            EntityType.LIBRARY: self._deserialize_library,
            EntityType.ASSET: self._deserialize_asset,
            EntityType.SEQUENCE: self._deserialize_sequence,
            EntityType.TIMELINE: self._deserialize_timeline,
            EntityType.TRACK: self._deserialize_track,
            EntityType.CLIP: self._deserialize_clip,
            EntityType.EFFECT: self._deserialize_effect,
            EntityType.GENERATOR: self._deserialize_generator,
            EntityType.KEYFRAME: self._deserialize_keyframe,
            EntityType.RELATIONSHIP: self._deserialize_relationship,
            EntityType.AI_CONTEXT: self._deserialize_ai_context,
        }
        
        deserializer = deserializers.get(entity_type)
        if deserializer:
            return deserializer(data, base_kwargs)
        
        return None
    
    def _deserialize_workspace_full(self, data: Dict[str, Any], base: Dict[str, Any]) -> Workspace:
        return Workspace(**base, **{
            "name": data.get("name", "Untitled Workspace"),
            "description": data.get("description", ""),
            "project_ids": tuple(EntityId.from_dict(pid) for pid in data.get("project_ids", [])),
            "library_ids": tuple(EntityId.from_dict(lid) for lid in data.get("library_ids", [])),
            "settings": data.get("settings", {})
        })
    
    def _deserialize_project_full(self, data: Dict[str, Any], base: Dict[str, Any]) -> Project:
        return Project(**base, **{
            "name": data.get("name", "Untitled Project"),
            "description": data.get("description", ""),
            "sequence_ids": tuple(EntityId.from_dict(sid) for sid in data.get("sequence_ids", [])),
            "active_sequence_id": EntityId.from_dict(data["active_sequence_id"]) if data.get("active_sequence_id") else None,
            "workspace_id": EntityId.from_dict(data["workspace_id"]) if data.get("workspace_id") else None,
            "settings": data.get("settings", {})
        })
    
    def _deserialize_library(self, data: Dict[str, Any], base: Dict[str, Any]) -> Library:
        return Library(**base, **{
            "name": data.get("name", "Untitled Library"),
            "description": data.get("description", ""),
            "asset_ids": tuple(EntityId.from_dict(aid) for aid in data.get("asset_ids", [])),
            "tags": tuple(data.get("tags", []))
        })
    
    def _deserialize_asset(self, data: Dict[str, Any], base: Dict[str, Any]) -> Asset:
        from ..models.entities import AssetSource, AssetMetadata, AssetType
        
        source = None
        if data.get("source"):
            source_data = data["source"]
            source = AssetSource(
                uri=source_data["uri"],
                source_type=source_data.get("source_type", "file"),
                format=source_data.get("format"),
                codec=source_data.get("codec"),
                size_bytes=source_data.get("size_bytes"),
                checksum=source_data.get("checksum")
            )
        
        asset_meta = None
        if data.get("asset_metadata"):
            meta_data = data["asset_metadata"]
            asset_meta = AssetMetadata(
                asset_type=AssetType[meta_data["asset_type"]],
                duration_ms=meta_data.get("duration_ms"),
                width=meta_data.get("width"),
                height=meta_data.get("height"),
                frame_rate=meta_data.get("frame_rate"),
                sample_rate=meta_data.get("sample_rate"),
                channels=meta_data.get("channels"),
                color_space=meta_data.get("color_space"),
                has_alpha=meta_data.get("has_alpha", False)
            )
        
        return Asset(**base, **{
            "name": data.get("name", "Untitled Asset"),
            "source": source,
            "asset_metadata": asset_meta,
            "library_id": EntityId.from_dict(data["library_id"]) if data.get("library_id") else None,
            "tags": tuple(data.get("tags", [])),
            "thumbnail_uri": data.get("thumbnail_uri"),
            "ai_embeddings": data.get("ai_embeddings")
        })
    
    def _deserialize_sequence(self, data: Dict[str, Any], base: Dict[str, Any]) -> Sequence:
        return Sequence(**base, **{
            "name": data.get("name", "Sequence"),
            "timeline_id": EntityId.from_dict(data["timeline_id"]) if data.get("timeline_id") else None,
            "project_id": EntityId.from_dict(data["project_id"]) if data.get("project_id") else None,
            "parent_sequence_id": EntityId.from_dict(data["parent_sequence_id"]) if data.get("parent_sequence_id") else None,
            "child_sequence_ids": tuple(EntityId.from_dict(sid) for sid in data.get("child_sequence_ids", []))
        })
    
    def _deserialize_timeline(self, data: Dict[str, Any], base: Dict[str, Any]) -> Timeline:
        from ..models.entities import TimelineSettings
        
        settings = TimelineSettings()
        if data.get("settings"):
            s = data["settings"]
            settings = TimelineSettings(
                frame_rate=s.get("frame_rate", 24.0),
                width=s.get("width", 1920),
                height=s.get("height", 1080),
                pixel_aspect_ratio=s.get("pixel_aspect_ratio", 1.0),
                display_format=s.get("display_format", "timecode"),
                start_timecode=s.get("start_timecode", "00:00:00:00"),
                drop_frame=s.get("drop_frame", False)
            )
        
        return Timeline(**base, **{
            "name": data.get("name", "Timeline"),
            "settings": settings,
            "track_ids": tuple(EntityId.from_dict(tid) for tid in data.get("track_ids", [])),
            "duration_ms": data.get("duration_ms", 0),
            "sequence_id": EntityId.from_dict(data["sequence_id"]) if data.get("sequence_id") else None
        })
    
    def _deserialize_track(self, data: Dict[str, Any], base: Dict[str, Any]) -> Track:
        from ..models.entities import TrackType
        
        return Track(**base, **{
            "name": data.get("name", "Track"),
            "track_type": TrackType[data.get("track_type", "VIDEO")],
            "timeline_id": EntityId.from_dict(data["timeline_id"]) if data.get("timeline_id") else None,
            "clip_ids": tuple(EntityId.from_dict(cid) for cid in data.get("clip_ids", [])),
            "is_locked": data.get("is_locked", False),
            "is_muted": data.get("is_muted", False),
            "is_visible": data.get("is_visible", True),
            "volume": data.get("volume", 1.0),
            "pan": data.get("pan", 0.0),
            "height": data.get("height", 100)
        })
    
    def _deserialize_clip(self, data: Dict[str, Any], base: Dict[str, Any]) -> Clip:
        from ..models.entities import ClipType, ClipSource, Transform, TimeRange
        
        clip_type = ClipType[data.get("clip_type", "PRIMARY")]
        
        source = None
        if data.get("source"):
            s = data["source"]
            time_range = None
            if s.get("time_range"):
                tr = s["time_range"]
                time_range = TimeRange(start_ms=tr["start_ms"], end_ms=tr["end_ms"])
            
            source = ClipSource(
                asset_id=EntityId.from_dict(s["asset_id"]) if s.get("asset_id") else None,
                time_range=time_range,
                speed_multiplier=s.get("speed_multiplier", 1.0),
                is_frozen=s.get("is_frozen", False),
                freeze_frame_time_ms=s.get("freeze_frame_time_ms")
            )
        
        transform = Transform()
        if data.get("transform"):
            t = data["transform"]
            transform = Transform(
                position_x=t.get("position_x", 0.0),
                position_y=t.get("position_y", 0.0),
                scale_x=t.get("scale_x", 1.0),
                scale_y=t.get("scale_y", 1.0),
                rotation=t.get("rotation", 0.0),
                anchor_x=t.get("anchor_x", 0.5),
                anchor_y=t.get("anchor_y", 0.5),
                opacity=t.get("opacity", 1.0),
                blend_mode=t.get("blend_mode", "normal")
            )
        
        return Clip(**base, **{
            "name": data.get("name", "Clip"),
            "clip_type": clip_type,
            "track_id": EntityId.from_dict(data["track_id"]) if data.get("track_id") else None,
            "timeline_position_ms": data.get("timeline_position_ms", 0),
            "duration_ms": data.get("duration_ms", 0),
            "source": source,
            "transform": transform,
            "effect_ids": tuple(EntityId.from_dict(eid) for eid in data.get("effect_ids", [])),
            "is_selected": data.get("is_selected", False),
            "compound_sequence_id": EntityId.from_dict(data["compound_sequence_id"]) if data.get("compound_sequence_id") else None
        })
    
    def _deserialize_effect(self, data: Dict[str, Any], base: Dict[str, Any]) -> Effect:
        from ..models.entities import EffectType, EffectParameters
        
        return Effect(**base, **{
            "name": data.get("name", "Effect"),
            "effect_type": EffectType[data.get("effect_type", "CUSTOM")],
            "clip_id": EntityId.from_dict(data["clip_id"]) if data.get("clip_id") else None,
            "track_id": EntityId.from_dict(data["track_id"]) if data.get("track_id") else None,
            "parameters": EffectParameters(params=data.get("parameters", {}).get("params", {})),
            "is_enabled": data.get("is_enabled", True),
            "order": data.get("order", 0)
        })
    
    def _deserialize_generator(self, data: Dict[str, Any], base: Dict[str, Any]) -> Generator:
        return Generator(**base, **{
            "name": data.get("name", "Generator"),
            "generator_type": data.get("generator_type", "solid"),
            "duration_ms": data.get("duration_ms", 5000),
            "width": data.get("width", 1920),
            "height": data.get("height", 1080),
            "parameters": data.get("parameters", {})
        })
    
    def _deserialize_keyframe(self, data: Dict[str, Any], base: Dict[str, Any]) -> Keyframe:
        return Keyframe(**base, **{
            "name": data.get("name", "Keyframe"),
            "effect_id": EntityId.from_dict(data["effect_id"]) if data.get("effect_id") else None,
            "parameter_name": data.get("parameter_name", ""),
            "time_ms": data.get("time_ms", 0),
            "value": data.get("value"),
            "interpolation": data.get("interpolation", "linear"),
            "bezier_in": tuple(data["bezier_in"]) if data.get("bezier_in") else None,
            "bezier_out": tuple(data["bezier_out"]) if data.get("bezier_out") else None
        })
    
    def _deserialize_relationship(self, data: Dict[str, Any], base: Dict[str, Any]) -> Relationship:
        return Relationship(**base, **{
            "name": data.get("name", "Relationship"),
            "source_id": EntityId.from_dict(data["source_id"]),
            "target_id": EntityId.from_dict(data["target_id"]),
            "relationship_type": data.get("relationship_type", "references"),
            "properties": data.get("properties", {})
        })
    
    def _deserialize_ai_context(self, data: Dict[str, Any], base: Dict[str, Any]) -> AIContext:
        return AIContext(**base, **{
            "name": data.get("name", "AI Context"),
            "operation_type": data.get("operation_type", "unknown"),
            "prompt": data.get("prompt"),
            "model_config": data.get("model_config", {}),
            "input_entity_ids": tuple(EntityId.from_dict(eid) for eid in data.get("input_entity_ids", [])),
            "output_entity_ids": tuple(EntityId.from_dict(eid) for eid in data.get("output_entity_ids", [])),
            "result_data": data.get("result_data"),
            "error_message": data.get("error_message"),
            "execution_time_ms": data.get("execution_time_ms")
        })


__all__ = [
    'SerializationFormat',
    'SerializationOptions',
    'DeserializationResult',
    'GraphSerializer'
]
