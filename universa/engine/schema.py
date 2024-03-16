from typing import Any, Dict, List
from pydantic import BaseModel, create_model, TypeAdapter
from pydantic.json_schema import JsonSchemaValue

from .message import BaseMessage


class SchemaValidationError(Exception):
    """
    Raised when the schema validation fails.
    """

    __name__ = "SchemaValidationError"
    __desc__ = (
        "The schema validation failed. The following properties are missing:\n`{}`"
    )

    def __init__(self, missing_properties: List[str], **kwargs) -> None:
        self.message = self.__desc__.format(
            "\n".join([f"- {mp}" for mp in missing_properties])
        )
        super().__init__(self.message, **kwargs)


class Schema(BaseModel):
    """
    Simplified pydantic BaseModel schema with custom string representation.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize Schema."""
        super().__init__(*args, **kwargs)

    @classmethod
    def to_schema(cls) -> JsonSchemaValue:
        """Create a JSON Schema for all the parameters of the function.

        Returns:
            Dict[str, Any]: The  schema representation.
        """
        schema = {
            "properties": {
                k: TypeAdapter(v.annotation).json_schema()
                for k, v in cls.model_fields.items()
            },
        }

        return schema

    @classmethod
    def to_str(cls) -> str:
        """Return a human-readable representation of the simplified BaseModel schema.

        Args:
            cls: The class representing the schema.

        Returns:
            A string containing the human-readable representation of the schema.

        """
        schema = cls.model_json_schema()
        _str = f"{schema['title']}:"
        for k, v in schema["properties"].items():
            try:
                _str += f"\n- {k}: {v['type']}"
            except KeyError:
                _str += f"\n- {k}: Multiple Types"
            if "default" in v:  # because it can be None
                _str += f" (default: {v['default']})"
        return _str

    @staticmethod
    def create_schema(schema_name: str, **schema_kwargs) -> "Schema":
        """
        Create a validation schema based on keyword arguments. Used to create schemas
        for input and output of BaseAgent methods. In order to provide a methodology
        to pass generalized inputs between BaseAgents in Nodes, we will use schemas
        as our primary method of validation.

        Args:
            * schema_name (str): Name of the schema
            * schema_kwargs (dict): Keyword arguments for the schema. These should be
            passed as `property_name=property_type` pairs.

        Returns:
            * BaseModel: A pydantic BaseModel class that can be used to validate given arguments.

        Examples:
        1. Creating schema with types only (no default values)

            `create_schema("AgentInput", prompt=str, max_tokens=int)`

        2. Creating schema with optional values (`None` is optional too)

            `create_schema("AgentInput", prompt=str, max_tokens=(int, None))`

        """

        # Prepare kwargs
        for k, v in schema_kwargs.items():
            if isinstance(v, type):
                schema_kwargs[k] = (v, ...)
            elif isinstance(v, tuple):
                schema_kwargs[k] = v

        # Create schema
        return create_model(schema_name, **schema_kwargs, __base__=Schema)

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the agent output by the schema.
        """

        # Iterate over schema
        missing_properties = []
        for k, v in self.model_fields.items():
            if v.annotation.__name__.lower() != type(output[k]).__name__.lower():
                raise TypeError(f"{k} is not of type {v.annotation.__name__}")

            is_required = v.is_required()
            if is_required and k not in output.keys():
                missing_properties.append(k)

        # Raise if any required attributes are missing
        if len(missing_properties) > 0:
            raise SchemaValidationError(missing_properties)

        return True

    def _process_message_for_schema(
        self, message: BaseMessage, kwargs: Dict[str, Any]
    ) -> None:
        for k, v in message.items():
            kwargs[k] = v

    @classmethod
    def get_kwarg(cls, order: int) -> Any:
        """
        Get the keyword arguments of the schema.
        """
        items = cls.model_fields.items()
        return list(items)[order][0]