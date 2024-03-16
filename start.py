from universa.models.api import API
from universa.models.llms.llm import BaseLLM

# Define
from universa.engine import Schema
from universa.models.llms import BaseLLM
from universa.agents.agent import BaseAgent
from universa.agents.generic_solver import GenericSolver
from universa.agents.planner import Planner
from universa.agents.solver import Solver


# Create API connection
# api = API(
#     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
#     api_key="a5d70b237295e0aac49d0597e91783ff4355d03c6e5b7067c96cee5abc725aa1",
#     base_url="https://api.together.xyz/v1",  # only required if it's not OpenAI
# )


# Create schemas


# Set up the LLM
# llm = BaseLLM(
#     llm=api,
#     generate_arguments={"max_tokens": 50},
# )

# Initialize an agent
# new_agent = BaseAgent(
#     name="Assistant",
#     description="An Autonomous AI Agent to solve problems.",
#     system_prompt="You are a helpful AI assistant.",
#     is_tool_calling_agent=False,
#     llm=llm,
#     input_schema=input_schema,
#     output_schema=output_schema,
#     max_retries=2,
#     parse_to_json=False,
# )


agent_solver = Solver()
agent_planner = Planner()
agent_generic_solver = GenericSolver()

# response = llm.query("What is the meaning of life?", max_tokens=50)

PROMPT = """
I want to travel somewhere.
I want to see snow.
I'm available to fly on June to December.
"""
# response = agent_solver.invoke("I want to fly somewhere")
# print(f"Agent Solver: {response}")
# response = agent_planner.invoke(PROMPT)
# print(f"Agent Planner: {response}")
response = agent_generic_solver.invoke(PROMPT)
print(f"Agent Generic Solver: {response}")


# response = agent_planner.invoke(PLANNER_PROMPT)
# print(response)

# response = agent_generic_solver.invoke('Solve my problem.')
# print(response)


# class Task:
#     def __init__(self, query):
#         self.query = query
#         self.subtask = []

#     def add_sub_task(self, task):
#         self.subtask.append(Task(task))

# class TaskGraph:
#     def __init__(self):
#         self.root = None


# def main():
#     print("Hello, what can I help you?")

#     task = Task()


#     while True:
#         # catch input
#         user_input = input("> ")
#         task.query = user_input

#         # Ask planner
#         planner_response = agent_planner.invoke(task.query)
#         if planner_response.is_decompose:
#             task.add_sub_task()


#         # exit
#         if user_input.lower() == "exit":
#             print("Goodbye!")
#             break

#         #

#         print("Bot: I don't understand. Can you please clarify?")


# if __name__ == "__main__":
#     main()
