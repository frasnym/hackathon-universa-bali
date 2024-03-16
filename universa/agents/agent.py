import json
from typing import Any, List, Union, Dict, Any, Optional, Callable

from pydantic import ValidationError
from openai.types.chat.chat_completion import ChatCompletion

from ..models.llms import BaseLLM
from ..tools import BaseTool, ToolRegistry
from ..tools.core_tools import tool_registry

from ..engine.core import Executable
from ..engine.message import AgentMessage
from ..engine.schema import Schema

from ..utils.execution import retry
from .prompts.basic import HELLO


class BaseAgent(Executable):
    """
    Base class used for creating Agents.
    """

    def __init__(
        self,
        name: str = "Assistant",
        description: str = "An Autonomous AI Agent to solve problems.",
        system_prompt: str = "You are a helpful AI assistant.",
        is_tool_calling_agent: bool = False,
        llm: Optional[BaseLLM] = None,
        input_schema: Optional[Schema] = None,
        output_schema: Optional[Schema] = None,
        max_retries: int = 2,
        parse_to_json: bool = False,
    ) -> None:
        """
        Initialize BaseAgent.
        """
        # Basic agent information
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.register()  # create ID & logger

        # LLM and schemas
        self.llm = llm
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.parse_to_json = parse_to_json
        self.response_format = None

        # Tools
        if is_tool_calling_agent:
            self.tool_registry = tool_registry
            self.tools = self.tool_registry.get_tools_as_schema()
            self.tool_choice = "auto"
        else:
            self.tool_registry = None
            self.tools = None
            self.tool_choice = None

        # Create agent's history
        self.chat_history = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]
        self.memory_window = 5

        # Setup retrying for invoke
        self.max_retries = max_retries
        self.invoke = retry(max_retries)(self.invoke)

    def use_response_format(self, response_format: Dict[str, Any]) -> None:
        """
        Set specific response format to use with given LLM.
        """
        self.response_format = response_format
        self.logger.debug(f"Set response format to {response_format}.")
        self.logger.info("Remember - not all models can utilize this method.")

    def prepare_tools(
        self, tools: List[Callable] = [], replace_tool: bool = False
    ) -> None:
        """
        Prepare the tools for the agent.

        ARgs:
            * `tools` (`Optional[Dict[str, Any]]`): List of methods to use as tools -
                will automatically register them in the ToolRegistry.
            * `replace_tool` (`bool`): Whether to replace the tool if it already exists.
        """
        if not hasattr(self, "tool_registry"):
            self.tool_registry = ToolRegistry()
            self.tool_choice = "auto"

        # Register tools passed into the method
        for tool in tools:
            self.tool_registry.register_tool(tool)

        # Get tools as schema
        new_tools = self.tool_registry.get_tools_as_schema()
        for tool, schema in new_tools.items():
            if tool in self.tools and replace_tool is False:
                self.logger.warning(
                    f"Tool {tool} already exists in the agent's tools - set `replace_tool` to `True` to replace it."
                )
                continue
            self.tools[tool] = schema

    def get_id(self) -> str:
        """
        Return the ID of the agent.
        """
        return self.object_id

    def invoke(
        self,
        query: Any,
    ) -> Union[ChatCompletion, str]:
        """
        Invoke the agent with a query.
        """

        # Validate the input
        try:
            if isinstance(query, str):
                kwarg_name = self.input_schema.get_kwarg(order=0)
                self.input_schema(**{kwarg_name: query})
            elif isinstance(query, dict):
                self.input_schema(**query)
        except ValidationError as e:
            self.logger.error(f"Error validating input: {e}")
            raise e

        # Query the LLM
        query, response = self.llm.query(
            query,
            history=self.chat_history,
            tools=self.tools,
            tool_choice=self.tool_choice,
            response_format=self.response_format,
        )
        self.chat_history = query  # we are returning the query as a message type

        # Handle tool calls
        tool_calls = response[0].choices[0].message.tool_calls
        if tool_calls:
            # Get function execution result
            tool_messages = BaseTool.execute_tool(tool_calls, self.tool_registry)

            # Run query with updated history
            self.chat_history.append(*tool_messages)
            query, response = self.llm.query(
                query=self.chat_history,
                num_responses=1,
            )

        # Parse & validate the response
        parsed_response = response[0].choices[0].message.content
        try:
            if self.parse_to_json:
                parsed_response = json.loads(parsed_response)
                output = self.output_schema(**parsed_response)
            else:
                kwarg_name = self.output_schema.get_kwarg(order=0)
                output = self.output_schema(**{kwarg_name: parsed_response})
            self.chat_history.append({"role": self.name, "content": parsed_response})
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing response: {e}")
            self.logger.error(f"Response: {parsed_response}")
            raise e
        except ValidationError as e:
            self.logger.error(f"Error validating response: {e}")
            self.logger.error(f"Response: {parsed_response}")
            raise e

        return output

    def send(
        self,
        content: Dict[str, Any],
        recipient: "BaseAgent",
        expect_reply: bool,
    ) -> Optional[AgentMessage]:
        """
        Send a message to another agent and handle the response or error.
        """

        # Prepare the message
        message = AgentMessage(content=content["task"])
        message.set_communicators(
            sender_id=self.get_id(),
            receiver_id=recipient.get_id(),
            expect_reply=expect_reply,
        )

        # Send the message to the agent
        if expect_reply:
            return recipient.receive(message)
        else:
            recipient.receive(message)

    def receive(self, message: AgentMessage) -> Union[AgentMessage, str]:
        """
        Receive message from another agent.
        """

        # Invoke the agent on message's contet
        response = self.invoke(
            query=message.content,
        )
        if message.expect_reply:
            return self.send(response, recipient=message.sender, expect_reply=False)
        else:
            return response

    def ping(self) -> str:
        """
        Simple method to check if LLM underlying the agent is working.
        """
        self.logger.info(
            self.llm.query(
                query=HELLO,
                parse_response="content",
            )
        )

    def __repr__(self) -> str:
        """
        Return a string representation of the BaseAgent.
        """
        _doc = self.__class__.__doc__ or "BaseAgent instance"
        _class_name = self.__class__.__name__
        input_schema = self.input_schema.to_schema()
        output_schema = self.output_schema.to_schema()

        _str = f"{_class_name}\n{_doc}\ninput_schema: {input_schema}\noutput_schema: {output_schema}"

        return _str
