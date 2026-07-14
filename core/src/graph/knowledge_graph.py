"""
EditFlow AI - Knowledge Graph

The knowledge graph stores all entities and their relationships,
enabling semantic queries and AI reasoning over the project structure.
"""

from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from uuid import UUID

from ..models.entities import (
    Entity, EntityId, EntityType, Relationship,
    Workspace, Project, Library, Asset, Sequence, Timeline, Track, Clip, Effect
)


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    entity_id: EntityId
    entity: Entity
    incoming_edges: Set[EntityId] = field(default_factory=set)
    outgoing_edges: Set[EntityId] = field(default_factory=set)
    metadata_index: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def add_incoming(self, entity_id: EntityId) -> None:
        self.incoming_edges.add(entity_id)
    
    def add_outgoing(self, entity_id: EntityId) -> None:
        self.outgoing_edges.add(entity_id)
    
    def remove_incoming(self, entity_id: EntityId) -> None:
        self.incoming_edges.discard(entity_id)
    
    def remove_outgoing(self, entity_id: EntityId) -> None:
        self.outgoing_edges.discard(entity_id)
    
    def index_metadata(self) -> None:
        """Build an index of metadata for fast querying."""
        self.metadata_index.clear()
        for entry in self.entity.metadata:
            if entry.namespace not in self.metadata_index:
                self.metadata_index[entry.namespace] = {}
            self.metadata_index[entry.namespace][entry.key] = entry.value


@dataclass
class GraphEdge:
    """An edge representing a relationship between two entities."""
    source_id: EntityId
    target_id: EntityId
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphQuery:
    """
    A query object for filtering and traversing the graph.
    
    Supports fluent interface for building complex queries.
    """
    entity_types: Optional[Set[EntityType]] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    id_filter: Optional[EntityId] = None
    relationship_filter: Optional[str] = None
    limit: Optional[int] = None
    offset: int = 0
    
    def where_type(self, *types: EntityType) -> 'GraphQuery':
        """Filter by entity types."""
        self.entity_types = set(types)
        return self
    
    def where_metadata(self, key: str, value: Any, namespace: str = "default") -> 'GraphQuery':
        """Filter by metadata key-value pair."""
        self.metadata_filters[f"{namespace}:{key}"] = value
        return self
    
    def where_id(self, entity_id: EntityId) -> 'GraphQuery':
        """Filter by specific entity ID."""
        self.id_filter = entity_id
        return self
    
    def where_relationship(self, relationship_type: str) -> 'GraphQuery':
        """Filter by relationship type."""
        self.relationship_filter = relationship_type
        return self
    
    def with_limit(self, limit: int) -> 'GraphQuery':
        """Limit the number of results."""
        self.limit = limit
        return self
    
    def with_offset(self, offset: int) -> 'GraphQuery':
        """Skip results for pagination."""
        self.offset = offset
        return self
    
    def matches(self, node: GraphNode) -> bool:
        """Check if a node matches this query's filters."""
        # Check ID filter
        if self.id_filter and node.entity_id != self.id_filter:
            return False
        
        # Check type filter
        if self.entity_types and node.entity.entity_type not in self.entity_types:
            return False
        
        # Check metadata filters
        for filter_key, expected_value in self.metadata_filters.items():
            namespace, key = filter_key.split(":", 1)
            actual_value = node.entity.get_metadata(key, namespace)
            if actual_value != expected_value:
                return False
        
        return True


@dataclass
class GraphTraversal:
    """
    Result of a graph traversal operation.
    
    Contains the visited nodes and path information.
    """
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    start_id: Optional[EntityId] = None
    end_id: Optional[EntityId] = None
    path: List[EntityId] = field(default_factory=list)
    
    def get_entities(self) -> List[Entity]:
        """Extract entities from traversal result."""
        return [node.entity for node in self.nodes]
    
    def get_entity_ids(self) -> List[EntityId]:
        """Extract entity IDs from traversal result."""
        return [node.entity_id for node in self.nodes]
    
    def first(self) -> Optional[Entity]:
        """Get the first entity or None."""
        return self.nodes[0].entity if self.nodes else None
    
    def first_id(self) -> Optional[EntityId]:
        """Get the first entity ID or None."""
        return self.nodes[0].entity_id if self.nodes else None


class KnowledgeGraph:
    """
    The central knowledge graph storing all entities and relationships.
    
    Provides:
    - CRUD operations for entities
    - Relationship management
    - Query and traversal APIs
    - Event notifications for changes
    - Thread-safe access
    """
    
    def __init__(self):
        self._nodes: Dict[EntityId, GraphNode] = {}
        self._edges: Dict[Tuple[EntityId, EntityId], List[GraphEdge]] = defaultdict(list)
        self._type_index: Dict[EntityType, Set[EntityId]] = defaultdict(set)
        self._metadata_index: Dict[str, Dict[str, Set[EntityId]]] = defaultdict(lambda: defaultdict(set))
        self._lock = False  # Simple lock flag for thread safety
        self._change_listeners: List[Callable[[str, EntityId], None]] = []
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the graph."""
        if self._lock:
            raise RuntimeError("Graph is locked for modifications")
        
        node = GraphNode(entity_id=entity.id, entity=entity)
        node.index_metadata()
        
        self._nodes[entity.id] = node
        self._type_index[entity.entity_type].add(entity.id)
        
        # Index metadata
        for entry in entity.metadata:
            self._metadata_index[entry.namespace][entry.key].add(entity.id)
        
        self._notify_change("entity_added", entity.id)
    
    def update_entity(self, entity: Entity) -> None:
        """Update an existing entity."""
        if self._lock:
            raise RuntimeError("Graph is locked for modifications")
        
        if entity.id not in self._nodes:
            raise KeyError(f"Entity {entity.id} not found")
        
        old_node = self._nodes[entity.id]
        
        # Remove old metadata index
        for entry in old_node.entity.metadata:
            self._metadata_index[entry.namespace][entry.key].discard(entity.id)
        
        # Create new node
        node = GraphNode(entity_id=entity.id, entity=entity)
        node.index_metadata()
        
        self._nodes[entity.id] = node
        
        # Add new metadata index
        for entry in entity.metadata:
            self._metadata_index[entry.namespace][entry.key].add(entity.id)
        
        self._notify_change("entity_updated", entity.id)
    
    def remove_entity(self, entity_id: EntityId) -> Entity:
        """Remove an entity from the graph."""
        if self._lock:
            raise RuntimeError("Graph is locked for modifications")
        
        if entity_id not in self._nodes:
            raise KeyError(f"Entity {entity_id} not found")
        
        node = self._nodes[entity_id]
        entity = node.entity
        
        # Remove from type index
        self._type_index[entity.entity_type].discard(entity_id)
        
        # Remove from metadata index
        for entry in entity.metadata:
            self._metadata_index[entry.namespace][entry.key].discard(entity_id)
        
        # Remove edges
        edges_to_remove = list(node.incoming_edges) + list(node.outgoing_edges)
        for other_id in edges_to_remove:
            self.remove_relationship(entity_id, other_id)
        
        del self._nodes[entity_id]
        
        self._notify_change("entity_removed", entity_id)
        
        return entity
    
    def get_entity(self, entity_id: EntityId) -> Optional[Entity]:
        """Get an entity by ID."""
        node = self._nodes.get(entity_id)
        return node.entity if node else None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type."""
        ids = self._type_index.get(entity_type, set())
        return [self._nodes[eid].entity for eid in ids if eid in self._nodes]
    
    def query(self, query: GraphQuery) -> List[Entity]:
        """Execute a query and return matching entities."""
        results = []
        
        for node in self._nodes.values():
            if query.matches(node):
                results.append(node.entity)
                if len(results) >= (query.limit or float('inf')):
                    break
        
        return results[query.offset:]
    
    def add_relationship(
        self,
        source_id: EntityId,
        target_id: EntityId,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Relationship:
        """Create a relationship between two entities."""
        if self._lock:
            raise RuntimeError("Graph is locked for modifications")
        
        if source_id not in self._nodes:
            raise KeyError(f"Source entity {source_id} not found")
        if target_id not in self._nodes:
            raise KeyError(f"Target entity {target_id} not found")
        
        # Create relationship entity
        relationship = Relationship.create(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties
        )
        
        # Add edge
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {}
        )
        
        self._edges[(source_id, target_id)].append(edge)
        self._nodes[source_id].add_outgoing(target_id)
        self._nodes[target_id].add_incoming(source_id)
        
        # Also add the relationship as an entity
        self.add_entity(relationship)
        
        self._notify_change("relationship_added", relationship.id)
        
        return relationship
    
    def remove_relationship(self, source_id: EntityId, target_id: EntityId) -> List[GraphEdge]:
        """Remove all relationships between two entities."""
        if self._lock:
            raise RuntimeError("Graph is locked for modifications")
        
        edges = self._edges.pop((source_id, target_id), [])
        
        if source_id in self._nodes:
            self._nodes[source_id].remove_outgoing(target_id)
        if target_id in self._nodes:
            self._nodes[target_id].remove_incoming(source_id)
        
        return edges
    
    def get_relationships(
        self,
        source_id: Optional[EntityId] = None,
        target_id: Optional[EntityId] = None,
        relationship_type: Optional[str] = None
    ) -> List[GraphEdge]:
        """Get relationships matching the given criteria."""
        results = []
        
        for (src, tgt), edges in self._edges.items():
            if source_id and src != source_id:
                continue
            if target_id and tgt != target_id:
                continue
            
            for edge in edges:
                if relationship_type and edge.relationship_type != relationship_type:
                    continue
                results.append(edge)
        
        return results
    
    def traverse_from(
        self,
        start_id: EntityId,
        max_depth: int = 10,
        relationship_filter: Optional[str] = None
    ) -> GraphTraversal:
        """
        Traverse the graph starting from a given entity.
        
        Uses BFS to explore connected entities.
        """
        if start_id not in self._nodes:
            raise KeyError(f"Entity {start_id} not found")
        
        traversal = GraphTraversal(start_id=start_id)
        visited: Set[EntityId] = {start_id}
        queue: List[Tuple[EntityId, int]] = [(start_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            if current_id in self._nodes:
                node = self._nodes[current_id]
                traversal.nodes.append(node)
                
                if current_id != start_id:
                    traversal.path.append(current_id)
            
            # Get outgoing edges
            for edge in self._edges.get((current_id, None), []):
                pass  # Handle edges properly below
            
            # Explore neighbors
            if current_id in self._nodes:
                current_node = self._nodes[current_id]
                for neighbor_id in current_node.outgoing_edges:
                    if neighbor_id not in visited:
                        # Check relationship filter
                        if relationship_filter:
                            edges = self._edges.get((current_id, neighbor_id), [])
                            if not any(e.relationship_type == relationship_filter for e in edges):
                                continue
                        
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, depth + 1))
        
        return traversal
    
    def find_path(
        self,
        start_id: EntityId,
        end_id: EntityId,
        max_depth: int = 20
    ) -> Optional[GraphTraversal]:
        """Find a path between two entities using BFS."""
        if start_id not in self._nodes or end_id not in self._nodes:
            return None
        
        if start_id == end_id:
            return GraphTraversal(
                nodes=[self._nodes[start_id]],
                start_id=start_id,
                end_id=end_id,
                path=[start_id]
            )
        
        visited: Set[EntityId] = {start_id}
        queue: List[Tuple[EntityId, List[EntityId]]] = [(start_id, [start_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            if current_id in self._nodes:
                current_node = self._nodes[current_id]
                
                for neighbor_id in current_node.outgoing_edges:
                    if neighbor_id == end_id:
                        final_path = path + [neighbor_id]
                        nodes = [self._nodes[eid] for eid in final_path if eid in self._nodes]
                        return GraphTraversal(
                            nodes=nodes,
                            start_id=start_id,
                            end_id=end_id,
                            path=final_path
                        )
                    
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, path + [neighbor_id]))
        
        return None
    
    def get_connected_entities(
        self,
        entity_id: EntityId,
        direction: str = "both"  # "incoming", "outgoing", "both"
    ) -> List[Entity]:
        """Get all entities connected to the given entity."""
        if entity_id not in self._nodes:
            return []
        
        node = self._nodes[entity_id]
        connected_ids: Set[EntityId] = set()
        
        if direction in ("outgoing", "both"):
            connected_ids.update(node.outgoing_edges)
        if direction in ("incoming", "both"):
            connected_ids.update(node.incoming_edges)
        
        return [self._nodes[eid].entity for eid in connected_ids if eid in self._nodes]
    
    def search_by_metadata(
        self,
        key: str,
        value: Optional[Any] = None,
        namespace: str = "default"
    ) -> List[Entity]:
        """Search for entities by metadata."""
        entity_ids = self._metadata_index.get(namespace, {}).get(key, set())
        results = []
        
        for eid in entity_ids:
            if eid in self._nodes:
                node = self._nodes[eid]
                if value is None or node.entity.get_metadata(key, namespace) == value:
                    results.append(node.entity)
        
        return results
    
    def lock(self) -> None:
        """Lock the graph to prevent modifications."""
        self._lock = True
    
    def unlock(self) -> None:
        """Unlock the graph to allow modifications."""
        self._lock = False
    
    def add_change_listener(self, listener: Callable[[str, EntityId], None]) -> None:
        """Add a listener for graph changes."""
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[str, EntityId], None]) -> None:
        """Remove a change listener."""
        self._change_listeners.remove(listener)
    
    def _notify_change(self, event_type: str, entity_id: EntityId) -> None:
        """Notify all listeners of a graph change."""
        for listener in self._change_listeners:
            try:
                listener(event_type, entity_id)
            except Exception:
                pass  # Don't let listener errors break the graph
    
    def get_all_entities(self) -> List[Entity]:
        """Get all entities in the graph."""
        return [node.entity for node in self._nodes.values()]
    
    def get_entity_count(self) -> int:
        """Get the total number of entities."""
        return len(self._nodes)
    
    def clear(self) -> None:
        """Remove all entities from the graph."""
        if self._lock:
            raise RuntimeError("Graph is locked for modifications")
        
        self._nodes.clear()
        self._edges.clear()
        self._type_index.clear()
        self._metadata_index.clear()


__all__ = ['KnowledgeGraph', 'GraphQuery', 'GraphTraversal', 'GraphNode', 'GraphEdge']
