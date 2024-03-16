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

SYSTEM_PROMPT = f"""
Imagine that you are a api assistant.
you have a database of fires in the world. 
You will help to find the right api according to user needs.

Here is your api database to search api:
{db}

*** Important Notice ***
1. Make careful analysis of the task before choosing the api.
2. Just return the json object. Nothing else, no description, nothing but json.
3. Don't write anything except json.
"""


class MatcherAgent(BaseAgent):
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
            schema_name="MatcherAgentInput",
            input=(str, ...),
        )
        self.output_schema: Schema = Schema.create_schema(
            schema_name="MatcherAgentOutput",
            # result=(str, FieldInfo(description="The result api.")),
            name=(
                str,
                FieldInfo(description="The name of the api."),
            ),
            description=(
                str,
                FieldInfo(description="The description of the api."),
            ),
            request=(
                dict,
                FieldInfo(description="The request of the api."),
            ),
            response=(
                dict,
                FieldInfo(description="The response of the api."),
            ),
        )

        # Set up the LLM
        self.llm = llm or BaseLLM.from_json(use_provided="mixtral")

        # Initialize
        super().__init__(
            name="Matcher Agent",
            description="It is a api assistant agent that will help user decide what api needed.",
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
