import json
from datetime import datetime

from src.models.info import Info
from src.prompts import destination, finance
from universa.agents.generic_solver import GenericSolver
from universa.agents.solver import Solver
from src.utils.data import WriteToJson, ReadFromJson
from universa.agents.travel_solver import TravelSolver


def gather_information() -> list[Info]:
    question = [
        "Where are you from?",
        "When you planning to travel?",
        "Do you have any hobby or desired activity?",
        "Do you okay with any climate?",
        "How much is your budget?",
    ]  # TODO: Ask AI to generate question
    infos = []

    # Shuffle the list of questions
    # random.shuffle(question)

    for q in question:
        # Ask user
        print(q)

        # Catch answer
        answer = input("> ")

        # Add to database
        infos.append(Info(q, answer))

    infos.append(Info("today is?", datetime.today().strftime("%Y-%m-%d")))

    return infos


def main():

    # infos = gather_information()
    # WriteToJson(infos)

    # user_information = [json.dumps(vars(item)) for item in infos]  # convert to string
    # print(user_information)

    solver_agent = Solver()
    travel_solver = TravelSolver()

    response = travel_solver.invoke(
        """{
            "question": "Where are you from?",
            "answer": "bali"
        },
        {
            "question": "When you planning to travel?",
            "answer": "from jun to dec"
        },
        {
            "question": "Do you have any hobby or desired activity?",
            "answer": "eat delicious food"
        },
        {
            "question": "Do you okay with any climate?",
            "answer": "prefer cold"
        },
        {
            "question": "How much is your budget?",
            "answer": "10000000"
        },
        {
            "question": "today is?",
            "answer": "2024-03-16"
        }"""
    )
    print(response)
    return

    # Destination
    agent_name = solver_agent.invoke("I want to travel somewhere")
    destination_agent = solver_agent.choose_specialist(agent_name)
    response = destination_agent.invoke(
        f"{destination.DESTINATION_PROMPT}{user_information}"
    )
    # print(response.solution)

    # Budget
    agent_name = solver_agent.invoke("I want prepare how much money for traveling")
    finance_agent = solver_agent.choose_specialist(agent_name)
    response = finance_agent.invoke(
        f"{finance.FINANCE_PROMPT}{user_information}{response.solution}"
    )
    print(response.solution)


if __name__ == "__main__":
    main()
