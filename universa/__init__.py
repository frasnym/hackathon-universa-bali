import sys
from typing import TYPE_CHECKING

from .utils.imports import LazyModule


_import_structure = {
    "agents": {
        "agent": ["BaseAgent"],
        "planner": ["Planner"]
    },
    "engine": {
        "message": ["AgentMessage", "NodeMessage"],
        "schema": ["Schema"],
        "machine": ["StateMachine"]
    },
    "graph": {
        "graph": ["Graph", "Node", "Edge"]
    },
    "models": {
        "api": ["API"],
        "llms": {
            "llm": ["BaseLLM"]
        },
        "model": ["AbstractModel", "ModelConfig"]
    },
    "thought": {
        "thought": ["Thought", "ThoughtNode"]
    },
    "tools": {
        "tool": ["BaseTool", "ToolRegistry"]
    },
    "utils": {
        "router": ["SemanticRouter"]
    }
}


if TYPE_CHECKING:
    
    # Agents
    from .agents.agent import BaseAgent
    from .agents.planner import Planner

    # Models
    from .models.api import API
    from .models.llms.llm import BaseLLM
    from .models.model import AbstractModel, ModelConfig

    # Engine
    from .engine.machine import StateMachine
    from .engine.message import AgentMessage, NodeMessage
    from .engine.schema import Schema
    
    # Graph
    from .graph.graph import Graph, Node, Edge

    # Thought
    from .thought.thought import Thought, ThoughtNode

    # Tools
    from .tools.tool import BaseTool, ToolRegistry

    # Utilities
    from .utils.router import SemanticRouter

else:
    
    sys.modules[__name__] = LazyModule(
        __name__,
        globals()["__file__"],
        _import_structure,
        module_spec=__spec__
    )