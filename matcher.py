import json
from datetime import datetime

from universa.agents.action_agent import ActionAgent
from universa.agents.generator_agent import GeneratorAgent
from universa.agents.matcher_agent import MatcherAgent


def gather_information() -> str:
    # Ask user
    print("What can I do for you?")

    # Catch answer
    answer = input("> ")

    return answer


def parse_data(data_string):
    data_list = data_string.split(",")  # Split the string by comma
    parsed_data = {
        # item.strip(): f"{item.strip()} data" for item in data_list
        item.strip(): "59a38afb45msh997d3e62cae8de4p15522djsn13a589fdd1aa"
        for item in data_list
    }  # Generate the JSON object
    return json.dumps(parsed_data)  # Convert the dictionary to JSON string


def main():

    # task = gather_information()

    matcher_agent = MatcherAgent()
    api = matcher_agent.invoke("hearthstone")
    print("Recommended API:", api.result)

    generator_agent = GeneratorAgent()
    key = generator_agent.invoke(api.result)
    print("Required input:", key.required)

    updated_key = parse_data(key.required)
    print("updated_key", type(updated_key), updated_key)
    # print("api.result", type(api.result), api.result)

    # updated_key = json.loads(updated_key)
    # print("updated_key", type(updated_key), updated_key)

    # # Extracting JSON data
    # start_index = api.result.find("{")
    # end_index = api.result.rfind("}") + 1
    # json_data = api.result[start_index:end_index]

    # # Parsing JSON
    # updated_api = json.loads(json_data)
    # print("updated_api", type(updated_api), updated_api)

    # action_agent = ActionAgent()
    # action = action_agent.invoke(
    #     f"I have this API specification: {api.result} and this is the key: {parse_data(key.required)}. Please help execute it."
    # )
    # print(action)


if __name__ == "__main__":
    main()
