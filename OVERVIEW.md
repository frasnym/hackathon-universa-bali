# Universa - Technical Overview

This document contains a short introduction into the current state of the Universa framework. It will take a look at the most basic objects currently implemented and show some code examples on how to use them.

## Bug reports and feature requests

Since it is work in progress, you can expect some rough edges and incomplete sections - please let us know about anything you find missing or unclear, as well as record any bugs that you encounter. This will help a lot!

If you find that some features would benefit the framework and its users, please let us know as well. We are always open to suggestions and improvements.

## Core classes

In the current version, Universa is built around the following core classes:

- [`BaseLLM`](#basellm)
- [`BaseAgent`](#baseagent)
- [`Thought`](#thought)
- [`Graph`, `Node` & `Edge`](#graph-node--edge)
- [`StateMachine`](#statemachine)
- [`BaseTool`](#basetool)

### `BaseLLM`

The `BaseLLM` class is the main class of the framework that handles creating and managing the LLM (Language Model) instances. Currently, it utilizes API connection using OpenAI client (which currently support a wide array of different API services, such as together.ai), but it is designed to be easily extendable to other services.

You can either construct an LLM instance yourself, or use provided default configuration. The following is an example of setting it up manually:

```python
from universa.models import BaseLLM, API

# Create API connection
api = API(
    model="gpt-3.5-turbo",
    api_key="your-api-key",
    base_url="url-to-your-api",  # only required if it's not OpenAI
)

# Define
llm = BaseLLM(
    llm=api,
    generate_arguments={
        "max_tokens": 100,
        "temperature": 0.5,
    }
)
```

In the above scenario, we firstly create an API connection, and then pass it to the `BaseLLM` class. We also define the default generation arguments, which will be used for all `query()` calls, unless they are overridden. You can use your LLM in the following manner now:

```python
response = llm.query("What is the meaning of life?")
```

or if you would like to adjust some of the generation arguments:

```python
response = llm.query("What is the meaning of life?", max_tokens=50)
```

**Important note**: The `BaseLLM` class is currently designed only to work with OpenAI client. Thus, it's `query()` method is designed to follow its protocol for message structure.

However, if you just want to run the default configuration, you can use the following code:

```python
llm = BaseLLM.from_json(use_provided="mixtral")
```

To see the JSON configuration for this model, you can [check this file out](./universa/models/llms/configs/mixtral.json).

**Important note**: This class will require passing your API key to the environment - the recommended way is to use `load_dotenv()` method from `python-dotenv` package - is reads your API keys from a `.env` file.

### `BaseAgent`

The `BaseAgent` class is the main class of the framework that handles creating agents. It provides basic methods for all agents, such as `invoke()` for performing inference and `send()` and `receive()` for communication.

To initialize an agent, you need to provide several important objects:

- `name` - the name of the agent
- `description` - a short description of the agent
- `system_prompt` - a prompt that will be used to initialize the conversation
- `is_tool_calling_agent` - a boolean value that indicates whether the agent has the ability to choose a tool & call it
- `llm` - an instance of `BaseLLM` class
- `input_schema` - a pydantic schema that will be used to validate the input
- `output_schema` - a pydantic schema that will be used to validate the output
- `max_retries` - an integer value that indicates how many times the agent will retry to perform inference
- `parse_to_json` - a boolean value that indicates whether the agent should parse the output to JSON when using its `invoke()` function

Here is an example of how to initialize an agent:

```python
from universa.engine import Schema
from universa.models import BaseLLM
from universa.agents import BaseAgent

# Create schemas
input_schema = Schema.create_schema(
    schema_name="AgentInput",
    context=(str, ...)
)
output_schema = Schema.create_schema(
    schema_name="AgentOutput",
    response=(str, ...),
)

# Set up the LLM
llm = BaseLLM.from_json(use_provided="mixtral")

# Initialize an agent
my_agent = BaseAgent(
    name="Assistant",
    description="An Autonomous AI Agent to solve problems.",
    system_prompt="You are a helpful AI assistant.",
    is_tool_calling_agent=False,
    llm=llm_instance,
    input_schema=input_schema,
    output_schema=output_schema,
    max_retries=2,
    parse_to_json=False,
)
```

Now here's a short description of what happened above:

1. We created two schemas - one for input and one for output. These will be used to validate the input and output of the agent.
2. We set up the LLM instance.
3. We initialized the agent with the provided parameters:
   - Since your schemas show that it's a simple agent - take some content and reply based on it - we set `is_tool_calling_agent` to `False`, as we do not want it to call any tools
   - We set the `parse_to_json` to `False`, as our system prompt does not contain any restrictions about responding in a JSON format.

This way, your agent is ready to work:

```python
response = my_agent.invoke("Hello, I need some help.")
```

You can take a look at the [`Planner`](./universa/agents/planner.py) and [`GenericSolver`](./universa/agents/generic_solver.py) agents to see a more complex example of how to create a specialized instance of `BaseAgent` class.

### `Thought`

The `Thought` class is a simple class that represents a thought. It is used as a basic piece of information used in the framework to represent tasks.

Your `Thought` can be created in the following way:

```python
from universa.thought import Thought

# Create a thought
my_thought = Thought(
    task="Create a plan for a new project."
)
```

This way, you create a thought with a task "Creates a plan for a new project.". You can solve this thought as follows:

```python
solution = my_agent.invoke(my_thought.get_content())
my_thought.solve(solution)
```

In the following code, we `invoke()` our agent on the thought's content and when it's done, we call `solve()` on the thought, passing the solution as an argument. This way, the thought will be considered solved.

### `Graph`, `Node` & `Edge`

At the heart of this framework lays a core concept of a Graph. Graphs are used to represent the structure of the problem and the relationships between different elements. The `Graph` class is a simple implementation of a directed graph, with `Node` and `Edge` classes representing the elements of the graph.

Creating an empty graph is really easy:

```python
from universa.graph import Graph, Node, Edge

# Create an empty graph
my_graph = Graph()

# Add some nodes
node_a = Node("A")
node_b = Node("B")
my_graph.add_node(node_a)
my_graph.add_node(node_b)

# Add an edge
my_graph.add_edge(node_a, node_b)
```

This way we create a graph with nodes `A` and `B`, and an edge between them. But this graph does not do much. Thus, we introduce an idea of `ThoughtNode` - a special type of `Node` that contains a `Thought` at it's base. We can create such a graph in the following way:

```python
from universa.graph import Graph
from universa.thought import Thought, ThoughtNode

# Create a graph
graph = Graph(
    name="ThoughtGraph",
    base_node_cls=ThoughtNode
)

# Add thoughts
thoughts = [
    Thought(content="I am a thought."),
    Thought(content="I am another thought.")
]
for thought in thoughts:
    graph.add_node(
        thought=thought
    )
```

By passing the class to our `Graph` constructor, we declare that each created node will be of type `ThoughtNode`.

Now that we have created a graph with thoughts, we can move to actually solving it.

### `StateMachine`

From all the classes described, the `StateMachine` is the most complex one. It aims to implement a state machine that traverses a graph of nodes with thoughts and solves them with the help of agents.

The basic idea behind the `StateMachine` is to start at the root node of the graph (i.e. the first node created) and perform a specific set of instructions on that node, to either `Solve` it or to `Decompose` it into new nodes, that will contain subtasks of the original thought.

In order to run the state machine on our graph, we simply do the following:

```python
from universa.engine import StateMachine

# Create state machine
state_machine = StateMachine()

# Run state machine
state_machine.run(graph=graph)
```

It's that simple! Of course, what happens under the hood is a bit more complex (we encourage you to check out the [`StateMachine`](./universa/engine/machine.py) implementation), but at the end it boils down to performing several instructions and changing the state of the graph. That's how we aim to solve the complex problems.

### `BaseTool`

Last but not least, the `BaseTool` class is a simple class that represents a tool. It is used as a way to port Python methods into the framework, so agents can use them to solve problems.

In order to add a method to an array of available tools, you have to remember to do the followings:

- Add all the type hints for both input arguments and output
- Create a clear docstring explaining the method

To see an example of how to create a tool, take a look at the [`core_tools.py`](./universa/tools/core_tools.py) class.

In a nutshell, first thing you need is creating a function of your own. Then, you can add it to the `tool_registry` by passing a decorator on top of that method.

```python
from universa.tools import ToolRegistry

tool_registry = ToolRegistry()

@tool_registry.register_tool
def web_search(query: str) -> str:
    """
    Search the web for a given query.

    Args:
        query: A string with a query to search for.

    Returns:
        A string with the search results.
    """
    # Your code here
    ...
```

This way when you pass this tool registry to the agent, it will be able to use it to solve problems.
