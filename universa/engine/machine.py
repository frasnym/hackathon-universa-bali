from typing import List, Callable, Optional

from .status import MachineStatus
from ..thought import ThoughtNode
from ..agents.planner import Planner
from ..engine.message import NodeMessage

from ..graph import Graph, Node, NodeContext
from ..graph.operation import OperationRouter, OperationError

from ..utils.logs import get_logger
from ..utils.execution import retry
from ..utils.registry import object_id_generator


class StateMachine:
    """
    State Machine is a simple executive engine running on a graph of nodes.
    """

    def __init__(self) -> "StateMachine":
        """
        Initialize the state machine with default values.
        """
        # ID & Logger
        self.machine_id: str = object_id_generator.register(self)  # State Machine ID
        self.logger = get_logger(f"State Machine (ID: {self.machine_id})")

        # Core mechanisms & objects
        self.node_ctx: NodeContext = None
        self.status: MachineStatus = MachineStatus.CONTEXT_0
        self.memory: List[NodeMessage] = []

        # Set up retries on methods
        self.run_planner = self.set_retry(func=self.run_planner, num_retries=3)

    def update_state(self, node: Node) -> None:
        """
        Update State Machine's node context and status.
        """
        self.node_ctx = node.create_context()
        self.status = MachineStatus.from_status(self.node_ctx.status)
        self.logger.debug(f"Context is now: {repr(self.status)} - {str(self.status)}")

    def run_planner(
        self, planner: Planner, router: OperationRouter, node: ThoughtNode
    ) -> None:
        """
        Run Planner on the given Thought Node and execute the Operation
        chosen based on the content of Thought.

        Args:
            * `planner` (`Planner`): The Planner to run on the node.
            * `router` (`OperationRouter`): The router to choose the operation from Planner's output.
            * `node` (`ThoughtNode`): The node to run the planner on.
        """
        # Retrieve content of the Thought
        thought = node.get_thought()

        # Create context for the planner
        task_at_hand, planner_context = node.create_planner_context()

        # Invoke Planner
        query = (
            planner_context
            + f"\n\nBased on the information above, what would be your decision for the following task:\n<task>\n{task_at_hand}\n</task>"
        )
        self.logger.info(
            f"\n\n\t\t\t=================== PLANNER QUERY =====================\n\n {query}"
        )
        planner_result = planner.invoke(query)
        self.logger.info(
            f"\n\n\t\t\t=================== PLANNER REPLY =====================\n\n {planner_result}"
        )

        # Retrieve Planner's outputs
        operation, op_args = router.from_planner(planner_result=planner_result)
        self.logger.debug(
            f"Planner result: {planner_result} - operation: {operation} - args: {op_args}"
        )

        # Execute chosen operation
        _, operation_status, _status_info = operation.execute(node=node, **op_args)
        self.logger.debug(f"Operation: {operation} with status: {operation_status}")

        # If operation failed, raise an error
        if not bool(operation_status):
            raise OperationError(operation, _status_info)

    def get_first_unsolved(self, node_list: List[ThoughtNode]) -> Optional[ThoughtNode]:
        """
        Get the first unsolved node from the list. In order to do that, sort
        the list by the node order and return the first unsolved node.

        Args:
            * `node_list` (`List[Node]`): List of nodes to check.

        Returns:
            * `Node` | `None`: The first unsolved node from the list. If no unsolved
                nodes are found, return `None`.
        """
        self.logger.debug(f"Checking for unsolved nodes in the list: {node_list}")
        node_list = sorted(node_list, key=lambda x: x.node_order)
        for node in node_list:
            if not node.solved:
                self.logger.debug(f"Found unsolved node: {node} - moving to it!")
                return node
        return None

    def backtrack(self, node: ThoughtNode) -> ThoughtNode:
        """
        Backtrack to the parent node. Currently it uses current NodeContext
        to find the parent to move on to.

        At the moment we assume there is only one parent to each Node. In the
        future we will adjust this method to handle multiple parents.

        Args:
            * `node` (`ThoughtNode`): The node to backtrack from - passed only for
                cases in which no parent is found (we return itself).

        Returns:
            * `ThoughtNode`: The parent node to move on to.
        """
        parents = self.node_ctx.active_predecessors
        if len(parents) == 0:
            # No parents - stop the machine
            self.logger.warning(
                f"No parents found for node ID: {self.node_ctx.node_id} - stopping the machine."
            )
            self.status = MachineStatus.STOP
            return node

        return parents[0]

    def run(self, graph: Graph, planner: Planner = None) -> None:
        """
        Run the state machine on the given graph.

        Args:
            * `graph` (`Graph`): The graph to run the state machine on.
            * `planner` (`Planner` | None): The planner to use for the state machine.
                If None, the default Planner is used. This option is currently used for
                debugging, however custom planners are welcome as long as they implement
                the `BaseAgent` interface and follow the same logic as `Planner`.
        """

        # Initialize a planner & semantic router
        planner = planner or Planner()
        operation_router = OperationRouter()

        # Set the current node & create context
        current_node: ThoughtNode = graph.get(0)
        self.update_state(current_node)

        # Run the graph
        while self.status != MachineStatus.STOP:

            if self.status == MachineStatus.CONTEXT_0:

                # Check if we are solved
                if current_node.solved:
                    self.logger.info("We have solved the graph - stopping the machine.")
                    self.status = MachineStatus.STOP
                    continue

                # If not, invoke planner
                self.run_planner(
                    planner=planner, router=operation_router, node=current_node
                )

                # Update state
                self.update_state(current_node)

            if self.status == MachineStatus.CONTEXT_1:

                # Check if we have any children to solve
                children = self.node_ctx.active_successors
                next_node = self.get_first_unsolved(children)

                # If we returned no node, we are done
                if next_node is None:
                    self.logger.info("We have solved the graph - stopping the machine.")
                    self.status = MachineStatus.STOP
                    continue

                # If we have a node, update the state
                current_node = next_node
                self.update_state(current_node)

            if self.status == MachineStatus.CONTEXT_2:

                children = self.node_ctx.active_successors
                next_node = self.get_first_unsolved(children)
                if next_node is None:
                    # No children to solve - move to parent
                    next_node = self.backtrack(current_node)

                # Update after both cases
                current_node = next_node
                self.update_state(current_node)

            if self.status == MachineStatus.CONTEXT_3:

                # If we are solved, go to parent
                if current_node.solved:
                    next_node = self.backtrack(current_node)
                    current_node = next_node
                else:
                    # If not, invoke planner
                    self.run_planner(
                        planner=planner, router=operation_router, node=current_node
                    )

                # Update state
                self.update_state(current_node)

        # Log the solutions
        for _, node in graph.nodes.items():
            self.logger.info(f"Node {node.node_id} solved: {node.get_solution()}")

    @staticmethod
    def set_retry(func: Callable, num_retries: int = 3) -> Callable:
        """
        Set the number of retries for the state machine.

        The reason for setting it up this way instead of using
        retry as decorator is that we want to have the ability
        to adjust the number or retries per instance of the machine.

        Args:
            * `num_retries` (`int`): Number of retries.
        """
        return retry(num_retries)(func)
