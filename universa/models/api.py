import os
from typing import Optional, List, Any, List, Dict, Union

from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai._types import NOT_GIVEN

from ..utils.logs import get_logger, general_logger

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    general_logger.info(
        "dotenv is not installed - loading keys from .env is recommended!"
    )


APIMessage = List[Dict[str, str]]


class API:
    """
    Basic connector class for APIs. As of now it utilizes OpenAI base client.
    """

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 2,
    ) -> None:
        """
        Initialize the API instance with given and base URL. If no API key is provided
        it will be looked for in the environment variables.

        Args:
            * `model` (`str`): Model to use for the API.
            * `base_url` (`str`): Base URL for the API. If using OpenAI token, it is not required.
            * `api_key` (`str`): API key for the given OpenAI protocol supporting API.
            * `max_retries` (`int`): Maximum number of retries for the API.
        """

        # Retrieve API & URL
        if not api_key:
            api_key = os.environ.get("API_KEY", None)
            if not api_key:
                raise ValueError("API key is required to initialize the API instance.")

        # Initialize the OpenAI client
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            max_retries=max_retries,
        )
        self.model = model
        self.logger = get_logger(__name__)

    def change_model(self, new_model: str) -> None:
        """
        Change the model used by the API.

        Args:
            * `new_model` (`str`): New model to use.
        """
        self.logger.info(f"Changed model fro `{self.model}` to `{new_model}`.")
        self.model = new_model

    def prepare_messages(self, query: str, history: Optional[Any] = None) -> APIMessage:
        """
        Prepare the query for the API.

        Args:
            * `query` (`str`): Query to prepare.
            * `history` (`Optional[Any]`): History to use for the query.

        Returns:
            * `List[MessageType]`: Prepared queries in API form.
        """
        api_query = [{"role": "user", "content": query}]
        if history is not None:
            return [*history, *api_query]
        return api_query

    def parse_response(
        self,
        response: ChatCompletion,
        parsing_type: Optional[str] = None,
    ) -> Any:
        """
        Parse the response from the API.

        Args:
            * `response` (`Any`): Response to parse.
            * `parsing_type` (`Optional[str]`): Type of parsing to use.

        Returns:
            * `Any`: Parsed response.
        """
        if response.choices:
            if parsing_type == "choice":
                return response.choices
            elif parsing_type == "message":
                return response.choices[0].message
            elif parsing_type == "content":
                return response.choices[0].message.content
        return response

    def get_response(
        self,
        messages: Union[APIMessage, str],
        tools: Optional[Dict[str, Any]] = None,
        tool_choice: Optional[str] = None,
        parse_response: Optional[str] = None,
        **optional_kwargs: Any,
    ) -> Union[ChatCompletion, str]:
        """
        Get the response from the API for a given prompt.

        Args:
            * `messages` (`Union[APIMessage, str]`): Messages to send to the API.
                If passed as a string (a single prompt), it will be converted to API message.
                Recommended to use `prepare_messages` before using this function.
            * `tools` (`Optional[Dict[str, Any]]`): Tools to choose from.
            * `tool_choice` (`Optional[str]`): Controls which (if any) function is called by the model.
                `None` means the model will not call the function, `auto` means it will.
            * `parse_response` (`Optional[str]`): Method of parsing the response (see `parse_response` method).
            * `**optional_kwargs`: Additional keyword arguments to pass to the API.

        Returns:
            * `str`: Generated response.
        """

        # Get the response through the API
        # self.logger.debug(f"Response format: {optional_kwargs.get('response_format', None)}.")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or NOT_GIVEN,
            tool_choice=tool_choice or NOT_GIVEN,
            **optional_kwargs,  # will raise TypeError if kwarg does not fit - we want this
        )

        # Parse and return the response
        if parse_response:
            return self.parse_response(response)
        return response

    def serialize(self, pass_api_key: bool = False) -> Dict[str, Any]:
        """
        Serialize the API instance.

        Args:
            * `pass_api_key` (`bool`): Whether to pass the API key or not.

        Returns:
            * `Dict[str, Any]`: Serialized API instance.
        """
        _serialized = {
            "model": self.model,
            "base_url": self.client.base_url,
            "max_retries": self.client.max_retries,
        }
        if pass_api_key:
            self.logger.warning(
                "API key is being passed in the serialized API instance."
            )
            _serialized["api_key"] = self.client.api_key

        return _serialized
