from typing import List, Optional
from pydantic.fields import FieldInfo

from .agent import BaseAgent
from ..models.llms import BaseLLM

from ..engine.schema import Schema, TypeAdapter

from .prompts.generic_solver_prompt import GENERIC_SOLVER_PROMPT


class GenericSolver(BaseAgent):
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
            schema_name="GenericSolverInput",
            input=(str, ...),
        )
        self.output_schema: Schema = Schema.create_schema(
            schema_name="GenericSolverOutput",
            solution=(
                str,
                FieldInfo(description="The solution of the task."),
            ),
        )

        # Set up the LLM
        self.llm = llm or BaseLLM.from_json(use_provided="mixtral")

        # Initialize
        super().__init__(
            name="Solver Agent",
            description="It is a generic solver agent specialized in solving any type of task.",
            system_prompt=GENERIC_SOLVER_PROMPT,
            llm=self.llm,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            parse_to_json=False,
            is_tool_calling_agent=True,
        )