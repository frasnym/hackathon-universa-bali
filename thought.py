from universa.thought import Thought
from universa.agents.generic_solver import GenericSolver

# Create a thought
my_thought = Thought(
    task="I want travel from indonesia. I want to see mountain and eat delicious noodle"
)

print(my_thought)

agent_generic_solver = GenericSolver()

solution = agent_generic_solver.invoke(my_thought.get_content())
my_thought.solve(solution)

print(solution)
print(my_thought)
