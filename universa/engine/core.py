from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from .schema import Schema
from .message import AgentMessage

from ..utils.registry import object_id_generator
from ..utils.logs import get_logger


class Executable(ABC):
    """
    Interface for executable objects such as Agents.
    """

    input_schema: Schema
    output_schema: Schema

    def register(self) -> None:
        """
        Register the model in the registry.
        """
        self.object_id = object_id_generator.register(self)
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def invoke(
        self,
        prompt: str,
        tool_choice: Optional[str] = "auto",
        configs: Optional[Any] = None,
    ) -> Schema:
        """
        Invoke the llm with the given prompt and optional tool choice and configurations.

        Args:
            prompt (str): The prompt for the llm.
            tool_choice (str, optional): The choice of tool. Defaults to "auto".
            configs (Any, optional): Additional configurations. Defaults to None.

        Returns:
            Schema: The response from the llm parsed into an executable schema.
        """
        ...

    @abstractmethod
    def send(
        self,
        query: Any,
        recipient: "Executable",
        expect_reply: bool,
    ) -> Union[AgentMessage, str]:
        """
        A method to send a query or a message to another agent and handle the response or error.

        Args:
            query (Query): The query or message to be sent.
            recipient (Executable): The recipient of the query or message.
            expect_reply (bool): A flag indicating whether a reply is expected.

        Returns:
            Union[AgentMessage, str]: The response message or an error message.
        """
        ...

    @abstractmethod
    def receive(self, message: AgentMessage) -> Union[AgentMessage, str]:
        """
        A method for receiving a message from an agent and returning a message or string.

        Args:
            message (Message): The message to be received.

        Returns:
            Union[AgentMessage, str]: The received message or a string.
        """
        ...
