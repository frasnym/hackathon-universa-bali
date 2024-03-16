import inspect
import json
from typing import (
    Callable,
    Any,
    Dict,
    ForwardRef,
    List,
    Optional,
    Tuple,
    TypeVar,
)

from pydantic import ValidationError
from pydantic_core import PydanticUndefined
from pydantic.fields import FieldInfo
from pydantic.json_schema import JsonSchemaValue
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from ..engine.schema import Schema
from ..utils.registry import Registry
from ..utils.logs import get_logger


logger = get_logger(__name__)


class MissingAnnotationError(Exception):
    """Raised when the function is missing annotations for required parameters."""

    __name__ = "MissingAnnotationError"
    __desc__ = "The parameter `{}` is missing annotations. "

    def __init__(self, missing: List[str], **kwargs) -> None:
        self.message = self.__desc__.format(missing)
        super().__init__(self.message, **kwargs)


class BaseTool:
    """
    Base class for methods and functions.
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        input_schema: Schema,
        output_schema: Schema,
    ) -> None:
        """Initialize function."""
        self.name = name
        self.description = description
        self.func = func
        self.input_schema = input_schema
        self.output_schema = output_schema

    @staticmethod
    def get_verified_annotation(annotation: Any) -> Any:
        """Handle the forward references of a parameter and avoid taking Callable types.

        Args:
            annotation (Any): The annotation of the parameter.

        Returns:
            Any: The type annotation of the parameter.
        """
        if isinstance(annotation, str):
            return ForwardRef(annotation)
        if annotation.__name__ == "Callable":
            raise ValueError(
                "Callable type annotations are not supported. Please use a more specific type."
            )
        else:
            return annotation

    @staticmethod
    def extract_parameter_description(docstring: str, param_name: str) -> str:
        """
        Extract the description of a parameter from the docstring.

        Args:
            docstring: The docstring of the function

        Returns:
            The description of the parameter
        """

        if len(docstring) == 0:
            return f"Parameter `{param_name}`"
        lines = docstring.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith(":param"):
                return line.split(":param")[1].strip()
        return f"Parameter `{param_name}`"

    @staticmethod
    def get_field_info_from_param(
        param: inspect.Parameter,
        docstring: str,
    ) -> Tuple[Any, FieldInfo]:

        # Get the verified annotation. Checks for Callable type and Forward References
        param_annotation = BaseTool.get_verified_annotation(param.annotation)
        default = (
            PydanticUndefined
            if param.default is inspect.Parameter.empty
            else param.default
        )

        # Get the description of the parameter
        if hasattr(param_annotation, "__metadata__"):
            if not isinstance(param_annotation.__metadata__[0], str):
                raise ValueError(
                    f"Description of parameter:'{param.name}' must be a string."
                )
            description = param_annotation.__metadata__[0]
        else:
            # If the description is not provided in the annotation, extract it from the docstring
            description = (
                BaseTool.extract_parameter_description(docstring, param.name)
                if docstring
                else f"Parameter `{param.name}`"
            )
        return param_annotation, FieldInfo(default=default, description=description)

    @classmethod
    def from_function(
        cls,
        func: Callable,
        description: Optional[str] = None,
    ) -> "BaseTool":
        """
        This method creates a BaseTool object with Pydantic model of input, output schemas.
        The instance of this BaseTool class is later used to create the JSON representation of
        the containing function in the format required by OpenAI, and its variants, from the input schema.

        Args:
            func (Callable): The Python method to wrap.
            description (Optional[str]): Optional description for the tool.

        Returns:
            BaseTool: An instance of the BaseTool class.

        Raises:
            ValueError: If the input is not a callable.
            MissingAnnotationError: If a parameter is missing annotations.
        """
        if not isinstance(func, Callable):
            raise ValueError("Input must be a callable.")

        func_args = {}
        func_spec = inspect.signature(func)
        for _, v in func_spec.parameters.items():

            # Through an error if the parameter is missing annotations
            if v.annotation is inspect.Parameter.empty:
                raise MissingAnnotationError([v.name])

            annotation, field_info = BaseTool.get_field_info_from_param(
                v,
                description if description else func.__doc__,
            )
            func_args[v.name] = (annotation, field_info)

        input_schema = Schema.create_schema(
            func.__name__ + "_input_schema", **func_args
        )

        return_type = func_spec.return_annotation
        if return_type is inspect.Signature.empty:
            logger.warning(
                f"Function {func.__name__} is missing a return type annotation. Although it is not required, it is recommended to add an appropriate one."
            )
            return_type = Any

        output_schema = Schema.create_schema(
            func.__name__ + "_output_schema", output=(return_type, ...)
        )

        return cls(
            name=func.__name__,
            description=description if description else func.__doc__,
            func=func,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    def get_function_schema(self) -> JsonSchemaValue:
        """
        Creates the JSON schema representation of the function, the type of format required by OpenAI and its variants.

        Returns:
            JsonSchemaValue: The JSON schema representation of the function.

        Examples:

        ```python
        def f(a: Annotated[str, "Parameter a"], b: int = 2, c: Annotated[float, "Parameter c"] = 0.1) -> None:
            pass

        base_tool = BaseTool.from_function(f, description="function f")
        schema = base_tool.get_function_schema()

        >>>  {'type': 'function',
           'function': {'description': 'function f',
               'name': 'f',
               'parameters': {'type': 'object',
                  'properties': {'a': {'type': 'str', 'description': 'Parameter a'},
                      'b': {'type': 'int', 'description': 'b'},
                      'c': {'type': 'float', 'description': 'Parameter c'}},
                  'required': ['a']}}}
        ```
        """

        function_json_schema = {
            "type": "function",
            "function": {
                "description": self.description,
                "name": self.name,
                "parameters": self.input_schema.to_schema(),
            },
        }

        return function_json_schema

    @staticmethod
    def execute_tool(
        tool_calls: ChatCompletionMessage,
        tool_registry: "ToolRegistry",
    ) -> List[Dict[str, Any]]:
        """
        executes the function with the given arguments and keyword arguments.
        input type has to satisfy the input_schema.
        The return type is output_schema.
        """

        tool_call_messages = []

        for tool_call in tool_calls:
            # prepare function data from tool call
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # Get the function from the tool registry
            function: BaseTool = tool_registry.get_tool(function_name)

            # Create input schema to validate whether input format is correct
            try:
                input: Schema = function.input_schema(**function_args)
            except ValidationError as e:
                raise e

            execution_result = function.func(**input.model_dump())

            # create a chat message for the tool call
            message = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": execution_result,
            }
            tool_call_messages.append(message)

        return tool_call_messages

    def __str__(cls) -> str:
        """
        Return a string representation of the object.

        This method returns a string that represents the object. It includes the name of the function,
        its description, and arguments.

        Returns:
            str: A string representation of the object.
        """
        _doc = getattr(cls, "_doc", cls.__doc__)
        _name = getattr(cls, "_name", cls.__class__.__name__)
        _json_schema = getattr(cls, "input_schema", None)
        _str = f"{_name}"
        if _doc:
            _str += f"\n\t{_doc.strip()}"
        if _json_schema:
            _str += f"\n{_json_schema.to_str()}"  # requires schema to by of type Schema, not BaseModel

        return _str


class ToolRegistry(Registry):
    """
    Registry for tools mainly and possibly other things.

    This class also represents a registry for tools. It allows for storing import paths to methods and their names & descriptions,
    so that we could simply choose the methods from here.
    """

    T = TypeVar("T")

    def __init__(self) -> None:
        self.registry = {"tools": {}}

    def register_tool(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Registers a tool function in the tool registry.

        Args:
            func: The tool function to be registered.

        Returns:
            The registered tool function.
        """

        func_obj = BaseTool.from_function(func)
        self.registry["tools"][func_obj.name] = func_obj

        return func

    def add_tool(self, func: Callable[..., Any], description: str = None) -> None:
        """
        Method for adding tool using this method instead of the register_tool decorator.

        Parameters:
        - func: The function to be added as a tool.
        - description: Optional description for the tool.

        Returns:
        None
        """

        func_obj = BaseTool.from_function(func, description=description)
        self.registry["tools"][func_obj.name] = func_obj

    def list_tools(self) -> List[JsonSchemaValue]:
        """
        List all available methods in the registry

        Returns:
            A list of JsonSchemaValue objects representing the available tools in the registry.
        """

        return self.registry["tools"]

    def get_tool(self, tool_name) -> BaseTool:
        """
        Retrieve a tool from the registry. It returns the BaseTool instance of the tool.

        Args:
            tool_name (str): The name of the tool to retrieve.

        Returns:
            JsonSchemaValue: The tool object from the registry.
        """

        return self.registry["tools"].get(tool_name)

    def get_tools_as_schema(self) -> List[JsonSchemaValue]:
        """
        Fetch all available tools in the registry as JSON schema.

        Returns:
            A list of JsonSchemaValue objects representing the available tools in the registry.
        """

        return [tool.get_function_schema() for tool in self.registry["tools"].values()]

    def remove_tool(self, tool_name) -> JsonSchemaValue:
        """
        Remove a tool from the registry.

        Args:
            tool_name (str): The name of the tool to be removed.

        Returns:
            JsonSchemaValue: The removed tool.
        """

        return self.registry["tools"].pop(tool_name)
