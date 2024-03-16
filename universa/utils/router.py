import re
from functools import partial
from typing import List, Any, Callable, Dict, Optional, Union, Tuple

from semantic_router import Route
from semantic_router.layer import RouteLayer
from semantic_router.utils.function_call import get_schema
from semantic_router.encoders import HuggingFaceEncoder, BaseEncoder

from ..models.llms import BaseLLM

from ..utils.logs import get_logger


RouterOutput = Union[None, str, Any, Tuple[Callable, Dict[str, Any]]]


class RouterLLM:
    """
    Simple wrapper allowing us to use our BaseLLM class in the
    Semantic Router.
    """

    def __init__(self, llm: BaseLLM) -> None:
        """
        Initialize the RouterLLM.
        """
        self.llm = llm

    def __call__(self, messages: Any) -> str:
        """
        Call the LLM specific method to generate responses.
        """
        return self.llm.query(
            query=messages,
            parse_response="content"
        )

class SemanticRouter:
    """
    Route given content to the correct callback or option.
    """

    def __init__(self, llm: Union[BaseLLM, RouterLLM]) -> None:
        """
        Initialize the operation router.
        """
        # TODO: Add support for many other encoders from semantic_routing
        self.encoder: BaseEncoder = HuggingFaceEncoder()
        self.routes: List[Route] = []
        self.call_functions: Dict[str, Callable] = []
        self.router: RouteLayer = None
        self.logger = get_logger(__name__)

        # Handle LLM
        if not isinstance(llm, RouterLLM):
            llm = RouterLLM(llm)
        self.llm = llm

    def add_route(
            self, name: str, utterances: List[str], callback: Optional[Callable] = None
    ) -> None:
        """
        Add route for given name. Optionally you can pass a callback to execute when
        this specific option is routed to.
        """
        route = Route(
            name=name,
            utterances=utterances,
            function_schema=get_schema(callback) if callback else None,
        )
        self.routes.append(route)
        if callable(callback):
            self.call_functions[name] = callback

    def compile(self) -> None:
        """
        Compile the operation router. Required step before using routing.
        """
        # Compile the router
        self.router = RouteLayer(
            encoder=self.encoder,
            routes=self.routes,
            llm=self.llm,
        )

    def __call__(self, content: str, auto_execute: bool = False) -> RouterOutput:
        """
        Route the operation based on the content.

        Args:
            * `content` (`str`): Content to choose operation based on.
            * `auto_execute` (`bool`): Whether to auto execute the function or
                return the function and its arguments.

        Returns:
            * `RouterOutput`: Depending on the `auto_execute` value, it will return
                the result of the function or the function and its arguments.

                If no function call is chosen by the router, it simply returns `None`.
        """
        # Check if router was compiled
        if self.router is None:
            raise RuntimeError("Router not compiled - please run `compile` method first.")
        
        # Perform routing
        out = self.router(content)
        self.logger.info(f"Router chose: {out}")
        if out.function_call:
            if auto_execute:
                return self.call_functions[out.function_call.name](
                    **out.function_call
                )
            else:
                return (
                    self.call_functions[out.function_call.name],
                    out.function_call
                )
        return out.name
    

class SimpleRouter:
    """
    Simple lexical router.
    """

    def __init__(self) -> None:
        """
        Initialize the simple router.
        """
        self.routes: Dict[str, Callable] = {}

    def add_route(self, name: str) -> None:
        """
        Add route for given name.
        """
        # create regex to look for name in string
        reg = re.compile(rf"\b{name}\b")
        self.routes[name] = partial(re.search, pattern=reg)

    def __call__(self, content: str, **kwargs) -> Any:
        """
        Route the operation based on the content. If operation name is in
        the given content, it will return the name of the operation.

        Args:
            * `content` (`str`): Content to choose operation based on.
            * `kwargs` (`Any`): Additional arguments - currently none are used.

        Returns:
            The name of the route that was found in the content.
        """
        for name, route in self.routes.items():
            if route(content):
                return name
        return None