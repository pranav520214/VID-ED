"""
EditFlow AI - Command Pattern

The command pattern enables undoable operations, essential for professional editing.
All modifications to the graph go through commands.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union
from copy import deepcopy

from ..models.entities import Entity, EntityId


@dataclass
class CommandResult:
    """Result of executing a command."""
    success: bool
    entity_id: Optional[EntityId] = None
    old_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def ok(
        cls,
        entity_id: Optional[EntityId] = None,
        old_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'CommandResult':
        return cls(
            success=True,
            entity_id=entity_id,
            old_state=old_state,
            new_state=new_state,
            metadata=metadata or {}
        )
    
    @classmethod
    def fail(cls, error_message: str) -> 'CommandResult':
        return cls(success=False, error_message=error_message)


class Command(ABC):
    """
    Base class for all commands.
    
    Commands encapsulate a single editing action and support undo/redo.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for the command."""
        pass
    
    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command and return the result."""
        pass
    
    @abstractmethod
    def undo(self) -> CommandResult:
        """Undo the command and return the result."""
        pass
    
    @abstractmethod
    def redo(self) -> CommandResult:
        """Redo the command (same as execute but after undo)."""
        pass
    
    def can_undo(self) -> bool:
        """Check if this command can be undone."""
        return True
    
    def can_redo(self) -> bool:
        """Check if this command can be redone."""
        return True


@dataclass
class CommandHistoryEntry:
    """An entry in the command history."""
    command: Command
    executed_at: datetime
    result: CommandResult
    is_undone: bool = False


class CommandHistory:
    """
    Manages the history of executed commands.
    
    Supports undo, redo, and history navigation.
    """
    
    def __init__(self, max_size: int = 1000):
        self._history: List[CommandHistoryEntry] = []
        self._redo_stack: List[CommandHistoryEntry] = []
        self._max_size = max_size
        self._is_recording = True
        self._change_listeners: List[Callable[[str, Command], None]] = []
    
    def execute(self, command: Command) -> CommandResult:
        """Execute a command and record it in history."""
        if not self._is_recording:
            return command.execute()
        
        # Clear redo stack when new command is executed
        self._redo_stack.clear()
        
        result = command.execute()
        
        if result.success:
            entry = CommandHistoryEntry(
                command=command,
                executed_at=datetime.now(),
                result=result
            )
            self._history.append(entry)
            
            # Trim history if needed
            while len(self._history) > self._max_size:
                self._history.pop(0)
            
            self._notify_change("executed", command)
        
        return result
    
    def undo(self) -> Optional[CommandResult]:
        """Undo the last executed command."""
        if not self._history:
            return None
        
        entry = self._history[-1]
        
        if not entry.command.can_undo():
            return CommandResult.fail(f"Command {entry.command.name} cannot be undone")
        
        self._is_recording = False
        try:
            result = entry.command.undo()
        finally:
            self._is_recording = True
        
        if result.success:
            entry.is_undone = True
            self._redo_stack.append(self._history.pop())
            self._notify_change("undone", entry.command)
        
        return result
    
    def redo(self) -> Optional[CommandResult]:
        """Redo the last undone command."""
        if not self._redo_stack:
            return None
        
        entry = self._redo_stack[-1]
        
        if not entry.command.can_redo():
            return CommandResult.fail(f"Command {entry.command.name} cannot be redone")
        
        self._is_recording = False
        try:
            result = entry.command.redo()
        finally:
            self._is_recording = True
        
        if result.success:
            entry.is_undone = False
            self._history.append(self._redo_stack.pop())
            self._notify_change("redone", entry.command)
        
        return result
    
    def can_undo(self) -> bool:
        """Check if there's something to undo."""
        return len(self._history) > 0
    
    def can_redo(self) -> bool:
        """Check if there's something to redo."""
        return len(self._redo_stack) > 0
    
    def get_history(self, limit: int = 50) -> List[CommandHistoryEntry]:
        """Get recent history entries."""
        return self._history[-limit:]
    
    def get_redo_stack_size(self) -> int:
        """Get the number of commands available for redo."""
        return len(self._redo_stack)
    
    def get_history_size(self) -> int:
        """Get the number of commands in history."""
        return len(self._history)
    
    def clear(self) -> None:
        """Clear all history and redo stacks."""
        self._history.clear()
        self._redo_stack.clear()
    
    def add_change_listener(self, listener: Callable[[str, Command], None]) -> None:
        """Add a listener for history changes."""
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[str, Command], None]) -> None:
        """Remove a change listener."""
        self._change_listeners.remove(listener)
    
    def _notify_change(self, event_type: str, command: Command) -> None:
        """Notify all listeners of a history change."""
        for listener in self._change_listeners:
            try:
                listener(event_type, command)
            except Exception:
                pass


# =============================================================================
# CONCRETE COMMANDS FOR ENTITY OPERATIONS
# =============================================================================

from ..graph.knowledge_graph import KnowledgeGraph


@dataclass
class AddEntityCommand(Command):
    """Command to add an entity to the graph."""
    graph: KnowledgeGraph
    entity: Entity
    
    @property
    def name(self) -> str:
        return f"Add {self.entity.entity_type.name}"
    
    def execute(self) -> CommandResult:
        try:
            old_state = None
            self.graph.add_entity(self.entity)
            new_state = self.entity.to_dict()
            return CommandResult.ok(
                entity_id=self.entity.id,
                old_state=old_state,
                new_state=new_state
            )
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def undo(self) -> CommandResult:
        try:
            old_state = self.entity.to_dict()
            self.graph.remove_entity(self.entity.id)
            return CommandResult.ok(
                entity_id=self.entity.id,
                old_state=old_state,
                new_state=None
            )
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def redo(self) -> CommandResult:
        return self.execute()


@dataclass
class UpdateEntityCommand(Command):
    """Command to update an entity in the graph."""
    graph: KnowledgeGraph
    old_entity: Entity
    new_entity: Entity
    
    @property
    def name(self) -> str:
        return f"Update {self.new_entity.entity_type.name}"
    
    def execute(self) -> CommandResult:
        try:
            old_state = self.old_entity.to_dict()
            self.graph.update_entity(self.new_entity)
            new_state = self.new_entity.to_dict()
            return CommandResult.ok(
                entity_id=self.new_entity.id,
                old_state=old_state,
                new_state=new_state
            )
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def undo(self) -> CommandResult:
        try:
            self.graph.update_entity(self.old_entity)
            return CommandResult.ok(
                entity_id=self.old_entity.id,
                old_state=self.new_entity.to_dict(),
                new_state=self.old_entity.to_dict()
            )
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def redo(self) -> CommandResult:
        return self.execute()


@dataclass
class RemoveEntityCommand(Command):
    """Command to remove an entity from the graph."""
    graph: KnowledgeGraph
    entity_id: EntityId
    removed_entity: Optional[Entity] = field(default=None, init=False)
    
    @property
    def name(self) -> str:
        return f"Remove {self.entity_id.entity_type.name}"
    
    def execute(self) -> CommandResult:
        try:
            self.removed_entity = self.graph.get_entity(self.entity_id)
            if self.removed_entity is None:
                return CommandResult.fail(f"Entity {self.entity_id} not found")
            
            old_state = self.removed_entity.to_dict()
            self.graph.remove_entity(self.entity_id)
            return CommandResult.ok(
                entity_id=self.entity_id,
                old_state=old_state,
                new_state=None
            )
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def undo(self) -> CommandResult:
        try:
            if self.removed_entity is None:
                return CommandResult.fail("No entity to restore")
            
            self.graph.add_entity(self.removed_entity)
            return CommandResult.ok(
                entity_id=self.entity_id,
                old_state=None,
                new_state=self.removed_entity.to_dict()
            )
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def redo(self) -> CommandResult:
        return self.execute()


@dataclass
class AddRelationshipCommand(Command):
    """Command to add a relationship between entities."""
    graph: KnowledgeGraph
    source_id: EntityId
    target_id: EntityId
    relationship_type: str
    properties: Optional[Dict[str, Any]] = None
    created_relationship: Optional[EntityId] = field(default=None, init=False)
    
    @property
    def name(self) -> str:
        return f"Add Relationship ({self.relationship_type})"
    
    def execute(self) -> CommandResult:
        try:
            relationship = self.graph.add_relationship(
                source_id=self.source_id,
                target_id=self.target_id,
                relationship_type=self.relationship_type,
                properties=self.properties
            )
            self.created_relationship = relationship.id
            return CommandResult.ok(
                entity_id=relationship.id,
                new_state=relationship.to_dict()
            )
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def undo(self) -> CommandResult:
        try:
            self.graph.remove_relationship(self.source_id, self.target_id)
            return CommandResult.ok(entity_id=self.created_relationship)
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def redo(self) -> CommandResult:
        return self.execute()


__all__ = [
    'Command',
    'CommandResult',
    'CommandHistory',
    'CommandHistoryEntry',
    'AddEntityCommand',
    'UpdateEntityCommand',
    'RemoveEntityCommand',
    'AddRelationshipCommand'
]
