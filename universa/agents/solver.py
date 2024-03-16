from typing import List, Optional

from .agent import BaseAgent
from ..models.llms import BaseLLM

from ..engine.schema import Schema, TypeAdapter
from pydantic.fields import FieldInfo

from .prompts.solver_prompt import SOLVER_PROMPT
from .prompts.generic_solver_prompt import GENERIC_SOLVER_PROMPT


class Solver(BaseAgent):
    """
    Simple Solver helper used to choose the proper Agent in `Solve` operation.
    """

    def __init__(self, llm: Optional[BaseLLM] = None) -> None:
        """
        Initialize the Solver Agent.
        """

        # Create schemas
        self.input_schema: Schema = Schema.create_schema(
            schema_name="SolverInput", context=(str, ...)
        )
        self.output_schema: Schema = Schema.create_schema(
            schema_name="SolverOutput",
            agent_name=(str, ...),
        )

        # Set up the LLM
        self.llm = llm or BaseLLM.from_json(use_provided="mixtral")

        # Initialize
        super().__init__(
            name="Solver",
            description="Solver helps solve a problem.",
            system_prompt=SOLVER_PROMPT,
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

    def choose_specialist(cls, content: str) -> BaseAgent:
        """
        Choose the proper Solver for given content.
        """
        ...

        # Initialize an agent
        return BaseAgent(
            name=content,
            description=f"An Autonomous AI Agent to solve problems about {content}.",
            system_prompt=GENERIC_SOLVER_PROMPT,
            is_tool_calling_agent=False,
            llm=cls.llm,
            input_schema=Schema.create_schema(
                schema_name=f"{content}Input",
                input=(str, ...),
            ),
            output_schema=Schema.create_schema(
                schema_name=f"{content}Output",
                solution=(
                    str,
                    FieldInfo(description="The solution of the task."),
                ),
            ),
            max_retries=2,
            parse_to_json=False,
        )
        # based on the content, create class for specific agent and
        # return it
