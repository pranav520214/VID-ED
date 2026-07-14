"""
Tests for the core domain models and knowledge graph.
"""

import pytest
from datetime import datetime
from uuid import UUID

# Import all entities and graph components
from src.models.entities import (
    TimeRange, SpatialRect, EntityType, EntityId, MetadataEntry,
    Workspace, Project, Library, Asset, AssetType, AssetSource, AssetMetadata,
    Sequence, Timeline, TimelineSettings, Track, TrackType, Clip, ClipType,
    ClipSource, Transform, Effect, EffectType, EffectParameters,
    Generator, Keyframe, Relationship, AIContext
)
from src.graph.knowledge_graph import KnowledgeGraph, GraphQuery, GraphTraversal
from src.commands.command import (
    CommandHistory, AddEntityCommand, UpdateEntityCommand,
    RemoveEntityCommand, AddRelationshipCommand
)
from src.events.event import EventBus, EventType, Event
from src.serialization.serializer import GraphSerializer, SerializationFormat, SerializationOptions


class TestTimeRange:
    """Tests for TimeRange primitive."""
    
    def test_create_time_range(self):
        tr = TimeRange(start_ms=0, end_ms=5000)
        assert tr.duration_ms == 5000
        assert tr.duration_seconds == 5.0
    
    def test_invalid_time_range(self):
        with pytest.raises(ValueError):
            TimeRange(start_ms=5000, end_ms=0)
    
    def test_overlaps(self):
        tr1 = TimeRange(start_ms=0, end_ms=5000)
        tr2 = TimeRange(start_ms=3000, end_ms=7000)
        tr3 = TimeRange(start_ms=6000, end_ms=9000)
        
        assert tr1.overlaps(tr2)
        assert not tr1.overlaps(tr3)
    
    def test_contains(self):
        tr = TimeRange(start_ms=0, end_ms=5000)
        assert tr.contains(2500)
        assert not tr.contains(6000)
    
    def test_serialization(self):
        tr = TimeRange(start_ms=1000, end_ms=4000)
        data = tr.to_dict()
        tr2 = TimeRange.from_dict(data)
        assert tr == tr2


class TestEntityId:
    """Tests for EntityId."""
    
    def test_create_entity_id(self):
        eid = EntityId.new(EntityType.PROJECT)
        assert eid.entity_type == EntityType.PROJECT
        assert isinstance(eid.value, UUID)
    
    def test_string_representation(self):
        eid = EntityId.new(EntityType.CLIP)
        s = str(eid)
        assert "CLIP:" in s
    
    def test_serialization(self):
        eid = EntityId.new(EntityType.ASSET)
        data = eid.to_dict()
        eid2 = EntityId.from_dict(data)
        assert eid == eid2


class TestWorkspace:
    """Tests for Workspace entity."""
    
    def test_create_workspace(self):
        ws = Workspace.create("My Workspace")
        assert ws.name == "My Workspace"
        assert ws.entity_type == EntityType.WORKSPACE
        assert len(ws.project_ids) == 0
    
    def test_add_project(self):
        ws = Workspace.create()
        project_id = EntityId.new(EntityType.PROJECT)
        ws2 = ws.add_project(project_id)
        assert project_id in ws2.project_ids
        assert ws2.updated_at > ws.created_at
    
    def test_remove_project(self):
        ws = Workspace.create()
        project_id = EntityId.new(EntityType.PROJECT)
        ws2 = ws.add_project(project_id)
        ws3 = ws2.remove_project(project_id)
        assert project_id not in ws3.project_ids
    
    def test_metadata(self):
        ws = Workspace.create()
        entry = MetadataEntry(key="theme", value="dark", namespace="ui")
        ws2 = ws.with_metadata(entry)
        assert ws2.get_metadata("theme", "ui") == "dark"


class TestProject:
    """Tests for Project entity."""
    
    def test_create_project(self):
        proj = Project.create("My Project")
        assert proj.name == "My Project"
        assert len(proj.sequence_ids) == 0
    
    def test_add_sequence(self):
        proj = Project.create()
        seq_id = EntityId.new(EntityType.SEQUENCE)
        proj2 = proj.add_sequence(seq_id)
        assert seq_id in proj2.sequence_ids
        assert proj2.active_sequence_id == seq_id


class TestAsset:
    """Tests for Asset entity."""
    
    def test_create_asset(self):
        source = AssetSource(uri="/path/to/video.mp4", source_type="file")
        asset = Asset.create("My Video", source)
        assert asset.name == "My Video"
        assert asset.source.uri == "/path/to/video.mp4"
    
    def test_asset_with_metadata(self):
        source = AssetSource(uri="/path/to/video.mp4")
        meta = AssetMetadata(
            asset_type=AssetType.VIDEO,
            duration_ms=30000,
            width=1920,
            height=1080,
            frame_rate=24.0
        )
        asset = Asset.create("Video", source, meta)
        assert asset.asset_metadata.duration_ms == 30000


class TestTimeline:
    """Tests for Timeline entity."""
    
    def test_create_timeline(self):
        timeline = Timeline.create("Main Timeline")
        assert timeline.name == "Main Timeline"
        assert timeline.settings.frame_rate == 24.0
        assert timeline.settings.width == 1920
    
    def test_add_track(self):
        timeline = Timeline.create()
        track_id = EntityId.new(EntityType.TRACK)
        timeline2 = timeline.add_track(track_id)
        assert track_id in timeline2.track_ids


class TestClip:
    """Tests for Clip entity."""
    
    def test_create_clip(self):
        clip = Clip.create("My Clip", duration_ms=5000)
        assert clip.duration_ms == 5000
        assert clip.timeline_position_ms == 0
    
    def test_move_clip(self):
        clip = Clip.create("Clip", duration_ms=5000)
        clip2 = clip.move_to(10000)
        assert clip2.timeline_position_ms == 10000
        assert clip.timeline_position_ms == 0  # Original unchanged
    
    def test_trim_clip(self):
        clip = Clip.create("Clip", duration_ms=5000)
        clip2 = clip.trim_end(-1000)
        assert clip2.duration_ms == 4000
    
    def test_clip_time_range(self):
        clip = Clip.create("Clip", duration_ms=5000)
        clip2 = clip.move_to(10000)
        tr = clip2.time_range
        assert tr.start_ms == 10000
        assert tr.end_ms == 15000


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""
    
    def test_add_entity(self):
        graph = KnowledgeGraph()
        ws = Workspace.create("Test")
        graph.add_entity(ws)
        
        retrieved = graph.get_entity(ws.id)
        assert retrieved is not None
        assert retrieved.name == "Test"
    
    def test_update_entity(self):
        graph = KnowledgeGraph()
        ws = Workspace.create("Original")
        graph.add_entity(ws)
        
        ws2 = ws.with_metadata(MetadataEntry(key="test", value="value"))
        graph.update_entity(ws2)
        
        retrieved = graph.get_entity(ws.id)
        assert retrieved.get_metadata("test") == "value"
    
    def test_remove_entity(self):
        graph = KnowledgeGraph()
        ws = Workspace.create()
        graph.add_entity(ws)
        graph.remove_entity(ws.id)
        
        assert graph.get_entity(ws.id) is None
    
    def test_query_by_type(self):
        graph = KnowledgeGraph()
        ws = Workspace.create()
        proj = Project.create()
        graph.add_entity(ws)
        graph.add_entity(proj)
        
        projects = graph.get_entities_by_type(EntityType.PROJECT)
        assert len(projects) == 1
        assert projects[0].id == proj.id
    
    def test_add_relationship(self):
        graph = KnowledgeGraph()
        ws = Workspace.create()
        proj = Project.create()
        graph.add_entity(ws)
        graph.add_entity(proj)
        
        rel = graph.add_relationship(ws.id, proj.id, "contains")
        assert rel is not None
        
        connected = graph.get_connected_entities(ws.id, "outgoing")
        assert len(connected) == 1
    
    def test_traverse(self):
        graph = KnowledgeGraph()
        ws = Workspace.create()
        proj = Project.create()
        seq = Sequence.create()
        
        graph.add_entity(ws)
        graph.add_entity(proj)
        graph.add_entity(seq)
        
        graph.add_relationship(ws.id, proj.id, "contains")
        graph.add_relationship(proj.id, seq.id, "contains")
        
        traversal = graph.traverse_from(ws.id, max_depth=5)
        assert len(traversal.nodes) >= 1


class TestCommandHistory:
    """Tests for Command pattern."""
    
    def test_execute_command(self):
        graph = KnowledgeGraph()
        history = CommandHistory()
        ws = Workspace.create("Test")
        
        cmd = AddEntityCommand(graph=graph, entity=ws)
        result = history.execute(cmd)
        
        assert result.success
        assert graph.get_entity(ws.id) is not None
    
    def test_undo_command(self):
        graph = KnowledgeGraph()
        history = CommandHistory()
        ws = Workspace.create("Test")
        
        cmd = AddEntityCommand(graph=graph, entity=ws)
        history.execute(cmd)
        
        undo_result = history.undo()
        assert undo_result.success
        assert graph.get_entity(ws.id) is None
    
    def test_redo_command(self):
        graph = KnowledgeGraph()
        history = CommandHistory()
        ws = Workspace.create("Test")
        
        cmd = AddEntityCommand(graph=graph, entity=ws)
        history.execute(cmd)
        history.undo()
        
        redo_result = history.redo()
        assert redo_result.success
        assert graph.get_entity(ws.id) is not None
    
    def test_can_undo_redo_flags(self):
        history = CommandHistory()
        assert not history.can_undo()
        assert not history.can_redo()


class TestEventBus:
    """Tests for Event system."""
    
    def test_publish_subscribe(self):
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(EventType.ENTITY_ADDED, handler)
        event = bus.emit(EventType.ENTITY_ADDED, "test", {"key": "value"})
        
        assert len(received) == 1
        assert received[0].payload["key"] == "value"
    
    def test_subscribe_once(self):
        bus = EventBus()
        count = [0]
        
        def handler(event):
            count[0] += 1
        
        bus.subscribe_once(EventType.CUSTOM, handler)
        bus.emit(EventType.CUSTOM, "test")
        bus.emit(EventType.CUSTOM, "test")
        
        assert count[0] == 1
    
    def test_pause_resume(self):
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe(EventType.CUSTOM, handler)
        bus.pause()
        bus.emit(EventType.CUSTOM, "test")
        assert len(received) == 0
        
        bus.resume()
        assert len(received) == 1


class TestSerialization:
    """Tests for serialization/deserialization."""
    
    def test_serialize_deserialize_graph(self):
        graph = KnowledgeGraph()
        ws = Workspace.create("Test Workspace")
        proj = Project.create("Test Project")
        
        graph.add_entity(ws)
        graph.add_entity(proj)
        
        serializer = GraphSerializer(SerializationOptions(
            format=SerializationFormat.JSON_PRETTY
        ))
        
        content = serializer.serialize(graph, ws)
        result = serializer.deserialize(content)
        
        assert result.success
        assert result.graph is not None
        assert result.graph.get_entity_count() == 2
    
    def test_backward_compatibility_export(self):
        graph = KnowledgeGraph()
        proj = Project.create("Legacy Project")
        graph.add_entity(proj)
        
        from src.models.entities import export_for_backward_compatibility
        data = export_for_backward_compatibility(proj, {str(proj.id): proj})
        
        assert data["version"] == "1.0-graph"
        assert data["legacy_compatible"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
