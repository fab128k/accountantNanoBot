# tests/test_swarm_foundation.py
# TDD tests for swarm module foundation: ProcessingContext + BaseSwarmAgent
# ============================================================================

import pytest
from pathlib import Path


class TestProcessingContextFields:
    """ProcessingContext dataclass field tests."""

    def test_instantiate_with_client_folder_only(self):
        from swarm import ProcessingContext
        ctx = ProcessingContext(client_folder=Path("/tmp"))
        assert ctx.client_folder == Path("/tmp")

    def test_default_errors_is_empty_list(self):
        from swarm import ProcessingContext
        ctx = ProcessingContext(client_folder=Path("/tmp"))
        assert ctx.errors == []

    def test_default_metadata_is_empty_dict(self):
        from swarm import ProcessingContext
        ctx = ProcessingContext(client_folder=Path("/tmp"))
        assert ctx.metadata == {}

    def test_default_current_file_is_none(self):
        from swarm import ProcessingContext
        ctx = ProcessingContext(client_folder=Path("/tmp"))
        assert ctx.current_file is None

    def test_instantiate_with_current_file(self):
        from swarm import ProcessingContext
        ctx = ProcessingContext(client_folder=Path("/tmp"), current_file=Path("/tmp/a.xml"))
        assert ctx.current_file == Path("/tmp/a.xml")
        assert ctx.client_folder == Path("/tmp")

    def test_errors_list_is_mutable(self):
        from swarm import ProcessingContext
        ctx = ProcessingContext(client_folder=Path("/tmp"))
        ctx.errors.append("err1")
        assert len(ctx.errors) == 1
        assert ctx.errors[0] == "err1"

    def test_metadata_dict_is_mutable(self):
        from swarm import ProcessingContext
        ctx = ProcessingContext(client_folder=Path("/tmp"))
        ctx.metadata["key"] = "val"
        assert ctx.metadata["key"] == "val"

    def test_errors_not_shared_between_instances(self):
        """Mutable defaults must use field(default_factory=list) — not shared."""
        from swarm import ProcessingContext
        ctx1 = ProcessingContext(client_folder=Path("/tmp"))
        ctx2 = ProcessingContext(client_folder=Path("/tmp"))
        ctx1.errors.append("only in ctx1")
        assert ctx2.errors == []

    def test_metadata_not_shared_between_instances(self):
        """Mutable defaults must use field(default_factory=dict) — not shared."""
        from swarm import ProcessingContext
        ctx1 = ProcessingContext(client_folder=Path("/tmp"))
        ctx2 = ProcessingContext(client_folder=Path("/tmp"))
        ctx1.metadata["k"] = "v"
        assert "k" not in ctx2.metadata


class TestBaseSwarmAgentAbstract:
    """BaseSwarmAgent abstract class tests."""

    def test_cannot_instantiate_directly(self):
        from swarm import BaseSwarmAgent
        with pytest.raises(TypeError):
            BaseSwarmAgent(name="test", model="m", system_prompt="p")

    def test_concrete_subclass_can_be_instantiated(self):
        from swarm import BaseSwarmAgent, ProcessingContext

        class ConcreteAgent(BaseSwarmAgent):
            def process(self, context: ProcessingContext) -> ProcessingContext:
                return context

        agent = ConcreteAgent(name="test", model="llama3.2:3b", system_prompt="system")
        assert agent is not None

    def test_concrete_subclass_inherits_name(self):
        from swarm import BaseSwarmAgent, ProcessingContext

        class ConcreteAgent(BaseSwarmAgent):
            def process(self, context: ProcessingContext) -> ProcessingContext:
                return context

        agent = ConcreteAgent(name="myagent", model="m", system_prompt="p")
        assert agent.name == "myagent"

    def test_concrete_subclass_inherits_model(self):
        from swarm import BaseSwarmAgent, ProcessingContext

        class ConcreteAgent(BaseSwarmAgent):
            def process(self, context: ProcessingContext) -> ProcessingContext:
                return context

        agent = ConcreteAgent(name="a", model="llama3.2:3b", system_prompt="p")
        assert agent.model == "llama3.2:3b"

    def test_concrete_subclass_has_ask_method(self):
        from swarm import BaseSwarmAgent, ProcessingContext

        class ConcreteAgent(BaseSwarmAgent):
            def process(self, context: ProcessingContext) -> ProcessingContext:
                return context

        agent = ConcreteAgent(name="a", model="m", system_prompt="p")
        assert hasattr(agent, "ask")
        assert callable(agent.ask)

    def test_concrete_subclass_has_stream_ask_method(self):
        from swarm import BaseSwarmAgent, ProcessingContext

        class ConcreteAgent(BaseSwarmAgent):
            def process(self, context: ProcessingContext) -> ProcessingContext:
                return context

        agent = ConcreteAgent(name="a", model="m", system_prompt="p")
        assert hasattr(agent, "stream_ask")
        assert callable(agent.stream_ask)

    def test_process_returns_context(self):
        from swarm import BaseSwarmAgent, ProcessingContext

        class ConcreteAgent(BaseSwarmAgent):
            def process(self, context: ProcessingContext) -> ProcessingContext:
                context.metadata["processed"] = True
                return context

        agent = ConcreteAgent(name="a", model="m", system_prompt="p")
        ctx = ProcessingContext(client_folder=Path("/tmp"))
        result = agent.process(ctx)
        assert result is ctx
        assert result.metadata.get("processed") is True

    def test_subclass_without_process_cannot_instantiate(self):
        from swarm import BaseSwarmAgent

        class IncompleteAgent(BaseSwarmAgent):
            pass  # no process() implementation

        with pytest.raises(TypeError):
            IncompleteAgent(name="a", model="m", system_prompt="p")


class TestSwarmImports:
    """Public API import tests."""

    def test_import_processing_context_from_swarm(self):
        from swarm import ProcessingContext
        assert ProcessingContext is not None

    def test_import_base_swarm_agent_from_swarm(self):
        from swarm import BaseSwarmAgent
        assert BaseSwarmAgent is not None

    def test_import_from_swarm_context_directly(self):
        from swarm.context import ProcessingContext
        assert ProcessingContext is not None

    def test_import_from_swarm_base_directly(self):
        from swarm.base import BaseSwarmAgent
        assert BaseSwarmAgent is not None

    def test_no_circular_import_with_agents(self):
        """Importing swarm alongside agents should not raise ImportError."""
        import importlib
        swarm = importlib.import_module("swarm")
        agents_base = importlib.import_module("agents.base_agent")
        assert swarm is not None
        assert agents_base is not None

    def test_all_exports_defined(self):
        import swarm
        assert hasattr(swarm, "__all__")
        assert "ProcessingContext" in swarm.__all__
        assert "BaseSwarmAgent" in swarm.__all__
