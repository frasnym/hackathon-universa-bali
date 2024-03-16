from abc import ABC, abstractmethod
from typing import Dict, List, Any, Union, Tuple

from ..engine.core import Executable
from ..engine.schema import Schema
from ..engine.status import OperationStatus

from ..thought import Thought, ThoughtNode

from ..models.llms import BaseLLM
from ..agents.generic_solver import GenericSolver
from ..agents.solver import Solver


from ..utils.logs import get_logger
from ..utils.router import SemanticRouter, SimpleRouter


NodeType = Union[ThoughtNode]  # extendable to other types
RouterType = Union[SemanticRouter, SimpleRouter, None]


class OperationError(Exception):
    """
    Raised when the operation fails.
    """

    __name__ = "OperationError"
    __desc__ = "Operation `{}` failed with message: `{}`"

    def __init__(self, operation: "Operation", message: str, **kwargs) -> None:
        desc = self.__desc__.format(operation.__class__.__name__, message)
        super().__init__(*(desc,), **kwargs)


class Operation(ABC):
    """
    Basic operation class implemented by all operations.
    """

    operation_logger = get_logger(__name__)

    @abstractmethod
    def execute(self) -> None:
        """
        Execute the operation.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class Solve(Operation):
    """
    Solve a node by choosing the proper executable and invoking
    it on its content.
    """

    def choose_executable(self, content: str) -> Executable:
        """
        Choose the proper Executable for given content.
        """
        # agent = Solver.choose_specialist(content)
        generic_solver = GenericSolver(llm=BaseLLM.from_json(use_provided="mixtral"))
        return generic_solver

    @OperationStatus.status
    def execute(self, node: ThoughtNode) -> Any:
        """
        Solve the thought.
        """

        # Retrieve thought's content
        thought = node.get_thought()
        content = thought.get_content(stack_size=1)

        # Choose the proper Executable & solve the thought
        executable = self.choose_executable(content)
        if node.node_order == 0:
            solution = executable.invoke(content)

        else:
            preceding_node: ThoughtNode = node.get_preceding_node()
            preceding_node_thought: Thought = preceding_node.get_thought()
            preceding_node_content: str = preceding_node_thought.get_content(
                stack_size=1
            )
            # Create proper query with proper context
            query = f"<context>\n{preceding_node_content}\n</context>\n\n<problem>\n{content}\n</problem>"
            solution = executable.invoke(query)

        thought.solve(solution)
        self.operation_logger.debug(
            f"Solved thought: {thought} with solution: {solution}"
        )

        return solution


class Decompose(Operation):
    """
    Decompose given node into multiple nodes.
    """

    @OperationStatus.status
    def execute(self, node: ThoughtNode, subtasks: List[str]) -> None:
        """
        Decompose the thought into smaller thoughts.
        """

        # Create new nodes
        for task in subtasks:
            node.add_successor(thought=Thought(task=task))
            self.operation_logger.debug(f"Graph now has {len(node.graph)} nodes.")


class OperationRouter:
    """
    Route given content to the correct operation handler.
    """

    def __init__(self) -> None:
        """
        Initialize an empty operation router. In order to use it, run one
        of the setup methods or route straight from Planner's result.
        """
        # Operations & logger
        self.operations: List[Operation] = [Solve(), Decompose()]
        self.logger = get_logger(self.__class__.__name__)

        # Router
        self.router: RouterType = None

    def setup_semantic_routing(self, llm: BaseLLM) -> SemanticRouter:
        """
        Setup semantic routing.
        """
        # Semantic routing
        if not llm:
            raise ValueError(
                "LLM is required for semantic routing. Please ensure the `llm` "
                "argument is passed."
            )
        router = SemanticRouter(llm)
        for operation in self.operations:
            router.add_route(
                name=operation.__class__.__name__,
                utterances=[],
                callback=operation.execute,
            )
        router.compile()

        return router

    def setup_simple_routing(self) -> SimpleRouter:
        """
        Setup simple routing.
        """
        router = SimpleRouter()
        for operation in self.operations:
            router.add_route(name=operation.__class__.__name__)

        return router

    def from_planner(self, planner_result: Schema) -> Tuple[Operation, Dict[str, Any]]:
        """
        Retrieve the operation from planner result.
        """
        operation = Decompose() if planner_result.is_decompose else Solve()
        operation_args = {}
        if isinstance(operation, Decompose):
            operation_args["subtasks"] = planner_result.subtasks

        self.logger.debug(f"Chosen operation: {operation} with args: {operation_args}")

        return operation, operation_args

    def __call__(self, content: str, **routing_kwargs) -> Any:
        """
        Based on the content, choose the proper operation for it.
        """
        return self.router(content, **routing_kwargs)
