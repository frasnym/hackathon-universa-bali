import json
from typing import Dict, Any, List, Optional, Tuple

from ..model import AbstractModel
from ..api import API
from .configs import default_configs

from ...utils.imports import import_class


class BaseLLM(AbstractModel):
    """
    Base for LLMs used by Agents. This class acts as a wrapper around
    an LLM model class or API client - it provides a common interface
    for querying the model and handling responses.
    """

    def __init__(
        self,
        llm: Any,
        generate_arguments: Dict[str, Any],
    ) -> None:
        """
        Create the BaseLLM instance.

        Args:
            * `llm` (`Any`): Local LLM model or API client.
            * `generate_arguments` (`ModelConfig` or `str`): Configuration of arguments
                used when performing inference on given model.
        """
        # Base logger & ID
        self.register()

        # LLM
        self.llm = llm
        self.generate_arguments = generate_arguments

    def query(
        self,
        query: Any,
        history: Optional[Any] = None,
        num_responses: int = 1,
        tools: Any = None,
        tool_choice: Optional[str] = None,
        parse_response: Optional[str] = None,
        **generate_arguments,
    ) -> Tuple[Any, List[Any]]:
        """
        Query the API model for responses.

        Args:
            * `query` (`Any`): Query to send to the model.
            * `history` (`Any`): History to use for the query.
            * `num_responses` (`int`): Number of responses to generate.
            * `tools` (`Any`): Tools to use for the query.
            * `tool_choice` (`str`): Choice of tool to use.
            * `parse_response` (`Optional[str]`): Type of parsing to use.
            * `**generate_arguments`: Additional arguments to use when generating responses.
                Will be merged with the `generate_arguments` provided at initialization.

        Returns:
            * `Tuple[Any, List[Any]]`: Query and list of responses. We return query as
                depending on the used LLM it might be parsed differently.
        """
        if not isinstance(self.llm, API):
            raise NotImplementedError(
                "This method is right now only for API-based models."
            )

        # Merge the generate_arguments
        for key, value in self.generate_arguments.items():
            if key not in generate_arguments:
                generate_arguments[key] = value

        # Prepare query
        if isinstance(query, str):
            query = self.llm.prepare_messages(query, history=history)

        # Gather responses
        responses = []
        for _ in range(num_responses):
            response = self.llm.get_response(
                messages=query,
                tools=tools,
                tool_choice=tool_choice,
                parse_response=parse_response,
                **generate_arguments,
            )
            responses.append(response)

        return query, responses

    @classmethod
    def from_json(
        cls, config_path: Optional[str] = None, use_provided: Optional[str] = "mixtral"
    ) -> "BaseLLM":
        """
        Initialize the BaseLLM instance from a serialized JSON file.

        Args:
            * `config_path` (`str`): Path to the configuration file.
            * `use_provided` (`str`): Name of the configuration provided
                within the framework.
        """

        # Check if we should use default configuration
        if config_path is None:
            if use_provided is None:
                raise ValueError(
                    "Either `config_path` or `from_default` should be provided."
                )
            config_path = default_configs.get(use_provided, None)
            if config_path is None:
                raise ValueError(
                    f"Configuration `{use_provided}` not found in default configurations."
                )

        # Load the ModelConfig
        config = cls.load_config(config_path)

        # Create LLM instance
        model_class = import_class(config.get("model_class"))
        llm = model_class(
            **config.get("model_arguments", {}),
        )

        return cls(
            llm=llm,
            generate_arguments=config.get("generate_arguments", {}),
        )

    def to_json(self, path: str) -> None:
        """
        Save the BaseLLM instance to a JSON file.

        Args:
            * `path` (`str`): Path to save the JSON file.
        """
        _serialized = {
            "model_class": self.llm.__class__.__name__,
            "model_arguments": self.llm.serialize(),
            "generate_arguments": self.generate_arguments,
        }
        with open(path, "w") as f:
            json.dump(_serialized, f, indent=4)
