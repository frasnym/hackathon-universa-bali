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
    return parsed_data


def GetAPI(req: dict) -> dict:
    print("==GetAPI Called==")
    matcher_agent = MatcherAgent()
    api = matcher_agent.invoke(req["task"])
    print("Recommended API:", api)

    req["api"] = {
        "name": api.name,
        "description": api.description,
        "request": api.request,
        "response": api.response,
    }

    generator_agent = GeneratorAgent()
    key = generator_agent.invoke(json.dumps({"request": req["api"]["request"]}))
    print("Required input:", key.required)

    req["secret"] = key.required

    return req


def replace_api_key(data: dict, key_name: str, new_key: str) -> dict:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                replace_api_key(value, key_name, new_key)
            elif isinstance(value, list):
                for item in value:
                    replace_api_key(item, key_name, new_key)
            elif value == key_name:
                data[key] = new_key

    print("data", data)


def GetResult(req: dict) -> dict:
    print("==GetResult Called==")

    api = req["api"]

    for key, value in req["secret_provided"].items():
        print("key", key)
        print("value", value)
        replace_api_key(api, key, value)

    req["api"] = api

    action_agent = ActionAgent()
    action = action_agent.invoke(
        f"I have this API specification: {req} and the secret value included."
    )
    print("action", action)
    req["result"] = action.response
    return req


def main():

    # task = gather_information()

    matcher_agent = MatcherAgent()
    api = matcher_agent.invoke("hearthstone")
    print("Recommended API:", api)

    generator_agent = GeneratorAgent()
    key = generator_agent.invoke(json.dumps({"request": api.request}))
    print("Required input:", key.required)

    updated_key = parse_data(key.required)
    print("updated_key", type(updated_key), updated_key)
    print("api.result", type(api), api)

    updated_key.update(
        {
            "request": api.request,
            "response": api.response,
        }
    )
    print("combined", type(updated_key), updated_key)

    action_agent = ActionAgent()
    action = action_agent.invoke(
        f"I have this API specification: {updated_key} and the secret value included."
    )
    print(action)


if __name__ == "__main__":
    main()
