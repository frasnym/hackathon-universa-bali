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
Imagine that you are a api assistant.
Based on the input of the user, define on what is the user should define by him/her self.

Result must be in json format!!
{
    "required": str # comma separated required variable
}

*** Important Notice ***
1. Make careful analysis of the task before define the requirement.
2. Try to find all the param, header, body that need to be filled.
"""


class GeneratorAgent(BaseAgent):
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
            schema_name="GeneratorAgentInput",
            input=(str, ...),
        )
        self.output_schema: Schema = Schema.create_schema(
            schema_name="GeneratorAgentOutput",
            required=(
                str,
                FieldInfo(description="The required of the api."),
            ),
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
            name="Generator Agent",
            description="It is a api assistant agent that will help user what is the requirement to do the api call.",
            system_prompt=SYSTEM_PROMPT,
            llm=self.llm,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            parse_to_json=True,
            is_tool_calling_agent=False,
        )
        self.use_response_format(
            {
                "type": "json_object",
                "schema": TypeAdapter(self.output_schema).json_schema(),
            }
        )
