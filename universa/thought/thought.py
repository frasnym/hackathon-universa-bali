from typing import List, Any, Dict

from ..graph import Node, Graph


class Thought:
    """
    Basic unit of information.
    """

    def __init__(self, task: str) -> None:
        """
        Construct a thought with initial task.
        """
        # Reasoning & solution
        self.task: str = task
        self.reasoning: List[str] = [task]
        self.solution: str = ""

        # Operational attributes
        self.scores: List[float] = [0.0]
        self.overall_score: float = 0.0
        self._solved: bool = False

    @property
    def solved(self) -> bool:
        return self._solved

    @solved.setter
    def solved(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("The value must be a boolean.")
        self._solved = value

    def solve(self, solution: str) -> None:
        """
        Solve the thought.
        """
        self.solution = solution
        self.solved = True
        self.remember(solution)

    def remember(self, content: str) -> None:
        """
        Add latest content to the thought's stack.
        """
        self.reasoning.insert(0, content)
        self.scores.insert(0, 0.0)

    def get_content(self, stack_size: int = 1) -> str:
        """
        Retrieve either solution or task, if solution is not present.
        """
        return self.solution if self.solved else self.task

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(task={self.task}, solved={self.solved})"


class ThoughtNode(Node):
    """
    Simple special Node implementation for Thought based nodes.
    """

    def __init__(self, node_id: str, graph: Graph, thought: Thought) -> None:
        super().__init__(node_id, graph)

        # Activate the node with Thought
        self.activate(base=thought)

        # Add special node_callback for ThoughtNode
        self.add_callback(name="node_callback", func=self._is_unsolved)

    def get_thought(self) -> Thought:
        """
        Retrieve the thought from the node.
        """
        return self.base

    def get_task(self) -> str:
        """
        Retrieve the task from the thought.
        """
        return self.base.task

    def get_solution(self) -> str:
        """
        Retrieve the solution from the thought.
        """
        return self.base.solution

    def create_planner_context(self) -> str:
        """
        Create a context about previous nodes for this ThoughtNode.
        """
        # Get the root node
        root_node: ThoughtNode = self.graph.get_root()

        # Initialize arrays
        context_array: List[str] = []
        task_number_array: List[str] = []

        # Prepare the root task info
        current_node = root_node
        root_task_info = f"Our main task at the top of the tree-like graph is this:\nTask 1: {root_node.get_task()}\n"
        context_array.append(root_task_info)
        task_number_array.append("1")

        # Traverse the graph and collect the context
        task_to_return: str = f"Task 1: {root_node.get_task()}"
        while current_node != self:
            unsolved_node = None
            task_number = ".".join(task_number_array)
            context_array.append(
                f"In order to solve Task {task_number} we first have to solve the following subtasks: "
            )
            solved_nodes: Dict[str, ThoughtNode] = {}

            # Check children and note contexts
            children = current_node.get_successors()
            for nr, child in enumerate(children):
                context_array.append(f"Task {task_number}.{nr+1}: {child.get_task()}")
                if not child.solved:
                    if unsolved_node is None:
                        unsolved_node = child
                        task_number_array.append(f"{nr+1}")
                        current_node = unsolved_node
                        task_to_return = context_array[-1]
                else:
                    solved_nodes[f"{task_number}.{nr+1}"] = child
            done_task_info = " ".join([f"Task {nr}" for nr, _ in solved_nodes.items()])
            if len(done_task_info) > 0:
                context_array.append(
                    f"\nThe solved subtasks of Task {task_number} are: {done_task_info}.\n"
                )

        return task_to_return, "\n".join(context_array)

    @property
    def solved(self) -> bool:
        """
        Check if the base Thought is solved.
        """
        return self.base.solved

    @staticmethod
    def _is_unsolved(node: "ThoughtNode") -> bool:
        """
        Static callback for the ThoughtNode context creation.
        """
        return not node.base.solved

    def __repr__(self) -> str:
        return f"ThoughtNode[{self.node_id}] with {self.base}"
