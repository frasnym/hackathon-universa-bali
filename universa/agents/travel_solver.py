from typing import List, Optional
from pydantic.fields import FieldInfo

from .agent import BaseAgent
from ..models.llms import BaseLLM

from ..engine.schema import Schema, TypeAdapter

TRAVEL_SYSTEM_PROMPT = """
Imagine that you are a travel assistant.
I want you to give option to travel overseas.

Your response will be in the following format:
{
    "destination": str # The recommended destination, city with country name.
    "reason": str # Reason why visit that destination.
    "date": str # Exact date of when should user go dd-mm-yyyy.
}

*** Important Notice ***
1. Make careful analysis of the task before choosing the right agent.
"""


class TravelSolver(BaseAgent):
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
            schema_name="TravelSolverInput",
            input=(str, ...),
        )
        self.output_schema: Schema = Schema.create_schema(
            schema_name="TravelSolverOutput",
            destination=(
                str,
                FieldInfo(
                    description="The recommended destination, city with country name."
                ),
            ),
            reason=(
                str,
                FieldInfo(description="Reason why visit that destination."),
            ),
            date=(
                str,
                FieldInfo(description="Exact date of when should user go dd-mm-yyyy."),
            ),
        )

        # Set up the LLM
        self.llm = llm or BaseLLM.from_json(use_provided="mixtral")

        # Initialize
        super().__init__(
            name="Travel Agent",
            description="It is a generic solver agent specialized in solving travel type of task.",
            system_prompt=TRAVEL_SYSTEM_PROMPT,
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
