from enum import Enum
from functools import partial


from typing import List, Tuple, Any, Callable, Optional, Dict
from collections import OrderedDict

from ..utils.registry import object_id_generator
from ..utils.logs import get_logger, BaseLogger


AdjacencyMatrix = List[List[int | None]]


class NodeException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class NodeAlreadyActive(NodeException):
    """
    Exception raised when trying to activate a node that is already active.
    """

    pass


class NodeContextStatus(Enum):
    """
    Status of the Node Context.
    """

    INACTIVE: int = -1
    NO_S_OR_P: int = 0
    ONLY_S: int = 1
    P_AND_S: int = 2
    ONLY_P: int = 3


class NodeContext:
    """
    Context of a node which is created from its predecessors and successors.
    """

    def __init__(
        self,
        node: "Node",
        only_active: bool = True,
        node_callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the node context.

        Args:
            * `node` (`Node`): the node for which the context is created
            * `only_active` (`bool`): if `True`, only active nodes are considered
            * `node_callback` (`Callable`): (optional) callback function that can be called on
                nodes in the context in order to eliminate them from the list
        """

        # Core node lists & information
        self.node_id: str = node.node_id
        self.predecessors: List["Node"] = node.get_predecessors()
        self.successors: List["Node"] = node.get_successors()
        self.active_predecessors = self.predecessors.copy()
        self.active_successors = self.successors.copy()

        # Only use active nodes
        if only_active:
            self.active_predecessors = [n for n in self.active_predecessors if n.active]
            self.active_successors = [n for n in self.active_successors if n.active]

        # Use callback on nodes
        if node_callback is not None:
            # Check if the callback is valid first
            if not callable(node_callback):
                raise TypeError(
                    f"The node callback must be a callable, not {type(node_callback).__name__}."
                )
            self.active_predecessors = [
                n for n in self.active_predecessors if node_callback(n)
            ]
            self.active_successors = [
                n for n in self.active_successors if node_callback(n)
            ]

        # Set status after creating lists
        self.status: NodeContextStatus = self.set_status()

    def set_status(self) -> NodeContextStatus:
        """
        Set the status of the node context based on the predecessors and successors.
        """
        if len(self.predecessors) == 0 and len(self.successors) == 0:
            return NodeContextStatus.NO_S_OR_P
        elif len(self.predecessors) == 0 and len(self.successors) > 0:
            return NodeContextStatus.ONLY_S
        elif len(self.predecessors) > 0 and len(self.successors) > 0:
            return NodeContextStatus.P_AND_S
        elif len(self.predecessors) > 0 and len(self.successors) == 0:
            return NodeContextStatus.ONLY_P
        else:
            return NodeContextStatus.INACTIVE

    def __repr__(self) -> str:
        """
        Create a representation of the node context.
        """
        return f"NodeContext[{self.node_id}]({self.status.value})"


class Node:
    """
    Base implementation of a Node, core element of the graph.
    """

    def __init__(self, node_id: str, graph: "Graph"):
        """
        Initialize the node. Pass the reference of the graph to the node,
        in order to easily add neighbors form the node level and register
        them in the graph.
        """

        # Graph related & logging
        self.node_id: str = node_id
        self.node_order: int = len(graph)
        self.logger: BaseLogger = get_logger(
            f"{self.__class__.__name__} (ID: {self.node_id})"
        )
        self.graph: "Graph" = graph

        # Base object and callbacks
        self.base: Any = None
        self.active: bool = False  # flag of the node that it is ready to work
        self.callbacks: Dict[str, Callable] = {}

    def add_successor(self, **node_kwargs) -> "Node":
        """
        Add neighbor to the node.
        """
        node = self.graph.add_node(**node_kwargs)
        self.graph.add_edge(self, node)
        return node

    def add_predecessor(self, **node_kwargs) -> "Node":
        """
        Add neighbor to the node.
        """
        node = self.graph.add_node(**node_kwargs)
        self.graph.add_edge(node, self)
        return node

    def add_callback(self, name: str, func: Callable, **func_kwargs: Any) -> None:
        """
        Add callback to the node. Can create partially declared function call if
        `func_kwargs` are provided.

        Args:
            * `name` (`str`): name of the callback - it will be accessible by this name in the node
            * `func` (`Callable`): function to be called
            * `func_kwargs`: (optional) keyword arguments for the function
        """
        if len(func_kwargs) > 0:
            func = partial(func, **func_kwargs)
        self.callbacks[name] = func

    def get_predecessors(self) -> List["Node"]:
        """
        Return the nodes that are connected to the current node.
        """
        return [edge.node_from for edge in self.graph.edges if edge.node_to == self]

    def get_successors(self) -> List["Node"]:
        """
        Return the nodes that are connected from the current node.
        """
        return [edge.node_to for edge in self.graph.edges if edge.node_from == self]

    def get_preceding_node(self) -> "Node":
        """
        Return the node before that was added to the graph this node in the param. Meaning the preceding node.
        """

        # Get the order of the current node
        if len(self.graph) == 1:
            raise NodeException(
                "Graph has only one node. No preceding node available. "
            )

        return self.graph.get(self.node_order - 1)

    def activate(self, base: Any, replace: bool = False) -> None:
        """
        Activate the node by setting up the base object.
        """
        if self.base is not None and not replace:
            raise NodeAlreadyActive(self, f"Node already has a base object.")
        self.base = base
        self.active = True

    def deactivate(self) -> None:
        """
        Deactivate the node by removing the base object.
        """
        self.base = None
        self.active = False

    def get_callback(self, name: str) -> Callable:
        """
        Return the callback function by its name.
        """
        callback = self.callbacks.get(name, None)
        if callback is None:
            self.logger.info(
                f"Callback with name '{name}' does not exist - returning `None`."
            )
        return callback

    def create_context(self, callback_name: str = "node_callback") -> NodeContext:
        """
        Create Node context that contains Node status. If callback name is provided,
        it will be passed on to the context to be called upon nodes.
        """
        return NodeContext(node=self, node_callback=self.callbacks.get(callback_name))

    def __eq__(self, other: "Node"):
        """
        Check if two nodes are the same.
        """
        if not isinstance(other, Node):
            raise ValueError(
                f"Cannot compare Node with non-Node ({other.__class__.__name__}) object."
            )
        return self.node_id == other.node_id

    def __repr__(self):
        """
        Create a representation of the node.
        """
        return f"Node (ID: {self.node_id})"


class Edge:
    """
    Edge connects two nodes within a graph. Each edge is directed, meaning
    that it connects only from `node_from` to `node_to`.
    """

    def __init__(self, node_from: Node, node_to: Node):
        if not isinstance(node_from, Node) or not isinstance(node_to, Node):
            raise TypeError(
                f"Both `node_from` and `node_to` must be instances of Node, not {node_from.__class__.__name__}"
            )
        self.node_from: Node = node_from
        self.node_to: Node = node_to

    def __eq__(self, other: "Edge"):
        if not isinstance(other, Edge):
            raise TypeError(
                f"Cannot compare Edge with non-Edge ({other.__class__.__name__}) object."
            )
        return self.node_from == other.node_from and self.node_to == other.node_to


class Graph:
    """
    Graph is a collection of nodes and edges that connect them. It is the base object
    on which the StateMachine runs and performs operations.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        base_node_cls: Optional[Node] = Node,
        auto_update_am: bool = True,
    ):
        """
        Initialize the graph.

        Args:
            * `name` (`str`): (optional) name of the graph
            * `base_node_cls` (`Node`): (optional) base class for the nodes in the graph - it will
               replace basic `Node` class when adding nodes
            * `auto_update_am` (`bool`): if `True`, the adjacency matrix will be updated each time
               a new edge is added to the graph
        """

        # Graph related & logging
        self.name = name or "Graph"
        self.graph_id = object_id_generator.register(self)  # Graph ID
        self.logger: BaseLogger = get_logger(f"{self.name} (ID: {self.graph_id})")

        # Nodes and edges
        self.nodes: OrderedDict[str, Node] = OrderedDict()
        self.edges: List[Edge] = []
        self.Node: Node = base_node_cls

        # Adjacency matrix
        self.adjacency_matrix: AdjacencyMatrix = [[]]
        self.auto_update_am: bool = auto_update_am

    @classmethod
    def from_list(cls, nodes: List[int], edges: List[Tuple[int, int]]):
        """
        Create graph from list of nodes and edges.
        """
        graph = cls()
        nodes = [graph.add_node() for _ in nodes]
        for edge in edges:
            graph.add_edge(nodes[edge[0]], nodes[edge[1]])
        graph.update_adjacency_matrix()
        return graph

    def add_node(self, **node_kwargs) -> Node:
        """
        Add single node to the graph.
        """
        node_id = self.graph_id + "_N" + str(len(self))
        node_kwargs["node_id"] = node_id
        node_kwargs["graph"] = self
        self.nodes[node_id] = self.Node(**node_kwargs)
        return self.nodes[node_id]

    def add_edge(self, node_from: Node, node_to: Node) -> None:
        """
        Add edge between nodes and register them in the graph.

        Args:
            * `node_from` (`Node`): the node from which the edge starts
            * `node_to` (`Node`): the node to which the edge leads

        """
        edge = Edge(node_from, node_to)
        if edge not in self.edges:
            self.edges.append(edge)
            if self.auto_update_am:
                self.update_adjacency_matrix()

    def create_adjacency_matrix(self, undirected: bool = False) -> AdjacencyMatrix:
        """
        Return the adjacency matrix of the graph.
        """
        matrix = [[0 for _ in range(len(self))] for _ in range(len(self))]
        if len(matrix) < 1:
            self.logger.info("No nodes in the graph.")

        for edge in self.edges:
            from_idx = edge.node_from.node_order
            to_idx = edge.node_to.node_order
            matrix[from_idx][to_idx] = 1
            if undirected:
                matrix[to_idx][from_idx] = 1
        return matrix

    def update_adjacency_matrix(self) -> None:
        """
        Update the adjacency matrix of the graph.
        """
        self.adjacency_matrix = self.create_adjacency_matrix()

    def get(self, node_nr: int) -> Node | None:
        """
        Return the node by its order number. If the node does not exist,
        simply returns `None`.
        """
        node = self.nodes.get(self.graph_id + "_N" + str(node_nr), None)
        if node is None:
            self.logger.warning(f"Node with order number {node_nr} does not exist.")
        return node

    def get_root(self) -> Node | None:
        """
        Return the root node of the graph.
        """
        if len(self) > 0:
            return self.get(0)
        self.logger.info("Graph has no nodes.")
        return None

    def __len__(self):
        """
        Return the number of nodes currently in the graph.
        """
        return len(self.nodes)

    def bfs(self, start_node: Node, end_node: Node) -> List[Node | None]:
        """
        Perform Breadth-First Search in the graph to find the shortest path
        to given end node from the start node.
        """
        n = len(self.adjacency_matrix)
        visited = [False] * n
        predecessor = [-1] * n
        queue = [start_node]

        visited[start_node.node_order] = True

        while queue:
            node = queue.pop(0)
            for i in range(n):
                if self.adjacency_matrix[node.node_order][i] == 1 and not visited[i]:
                    queue.append(self.get(i))
                    visited[i] = True
                    predecessor[i] = node.node_order
                    if i == end_node.node_order:
                        path = []
                        current_node_order = end_node.node_order
                        while current_node_order != -1:
                            path.append(self.get(current_node_order))
                            current_node_order = predecessor[current_node_order]
                        path.reverse()
                        return path

        return []

    def __str__(self):
        """
        Return the string representation of the graph.

        Adapted from the `networkx` library.
            networkx/classes/graph.py - Graph.__str__
        """
        return "".join(
            [
                type(self).__name__,
                f" named {self.name!r}" if self.name else "",
                f" with {len(self.nodes)} nodes and {len(self.edges)} edges",
            ]
        )
