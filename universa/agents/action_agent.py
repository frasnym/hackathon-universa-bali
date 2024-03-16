import json
from typing import List, Optional
from pydantic.fields import FieldInfo

from .agent import BaseAgent
from ..models.llms import BaseLLM

from ..engine.schema import Schema, TypeAdapter


# Reading from JSON file
def ReadFromJson(custom: str):
    if custom != "":
        file_path = custom
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
        return data


db = ReadFromJson("rapid-api.json")

SYSTEM_PROMPT = """
Imagine that you are a api action assistant.
You will be provided:
1. API specification
2. Secret key

Based on that, you can make a call to that API.

*** Important Notice ***
1. Make careful analysis of the task before define the requirement.
"""


class ActionAgent(BaseAgent):
    """
    Simple Solver helper used to choose the proper Agent in `Solve` operation.
    TODO:
    1.
    """

    def __init__(self, llm: Optional[BaseLLM] = None) -> None:
        """
        Initialize the Solver Agent.
        """

        # Create schemas
        self.input_schema: Schema = Schema.create_schema(
            schema_name="ActionAgentInput",
            input=(str, ...),
        )
        self.output_schema: Schema = Schema.create_schema(
            schema_name="ActionAgentOutput",
            response=(
                str,
                FieldInfo(description="The response of the api."),
            ),  # TODO: Make dynamic response
            # description=(
            #     str,
            #     FieldInfo(description="The description of the api."),
            # ),
            # request=(
            #     str,
            #     FieldInfo(description="The request of the api."),
            # ),
            # response=(
            #     str,
            #     FieldInfo(description="The response of the api."),
            # ),
        )

        # Set up the LLM
        self.llm = llm or BaseLLM.from_json(use_provided="mixtral")

        # Initialize
        super().__init__(
            name="Action Agent",
            description="It is a api assistant agent that will help user to make api call.",
            system_prompt=SYSTEM_PROMPT,
            llm=self.llm,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            parse_to_json=False,
            is_tool_calling_agent=True,
        )
        # self.use_response_format(
        #     {
        #         "type": "json_object",
        #         "schema": TypeAdapter(self.output_schema).json_schema(),
        #     }
        # )
