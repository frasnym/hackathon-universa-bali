import json
from typing import Any, Callable, List, Optional, Union

from openai.types.chat.chat_completion import ChatCompletion
from pydantic import ValidationError


from .agent import BaseAgent
from ..models.llms import BaseLLM

from ..engine.schema import Schema, TypeAdapter

from .prompts.advanced import PLANNER_PROMPT


class Planner(BaseAgent):
    """
    Planner is a special type of Agent that resides in the StateMachine. It is used
    to analyze thoughts in the Graph and make decisions on where to move next.
    """

    def __init__(self, llm: Optional[BaseLLM] = None) -> None:
        """
        Initialize the Planner.
        """

        # Create schemas
        self.input_schema: Schema = Schema.create_schema(
            schema_name="PlannerInput", context=(str, ...)
        )
        self.output_schema: Schema = Schema.create_schema(
            schema_name="PlannerOutput",
            is_decompose=(bool, ...),
            reason=(str, ...),
            subtasks=(List[str], ...),
        )

        # Set up the LLM
        self.llm = llm or BaseLLM.from_json(use_provided="mixtral")

        # Initialize
        super().__init__(
            name="Planner",
            description="Planner is a special type of Agent that resides in the StateMachine. It is used to analyze a thought from the Graph and make decisions on what operation to perform.",
            system_prompt=PLANNER_PROMPT,
            llm=self.llm,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            parse_to_json=True,
        )
        self.use_response_format(
            {
                "type": "json_object",
                "schema": TypeAdapter(self.output_schema).json_schema(),
            }
        )

    def invoke(
        self,
        query: Any,
    ) -> Union[ChatCompletion, str]:
        """
        Invoke the agent with a query.
        """

        # Validate the input
        try:
            kwarg_name = self.input_schema.get_kwarg(order=0)
            self.input_schema(**{kwarg_name: query})
        except ValidationError as e:
            self.logger.error(f"Error validating input: {e}")
            raise e

        if len(self.chat_history) > 1:
            self.chat_history.pop()

        # Query the LLM
        query, response = self.llm.query(
            query,
            history=self.chat_history,
            tools=self.tools,
            tool_choice=self.tool_choice,
            response_format=self.response_format,
        )

        # Parse & validate the response
        parsed_response = response[0].choices[0].message.content
        try:
            if self.parse_to_json:
                parsed_response = json.loads(parsed_response)
                output = self.output_schema(**parsed_response)
            else:
                # output = self.output_schema(**parsed_response)
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
