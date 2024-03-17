from flask import Flask, jsonify, request, abort

import matcher
from universa.agents.matcher_agent import MatcherAgent

app = Flask(__name__)


@app.route("/api/matchers", methods=["POST"])
def add_book():
    data = request.get_json()

    if "secret_provided" in data:
        print("secret_provided", data["secret_provided"])
        data = matcher.GetResult(data)
    elif "task" in data:
        print("task", data["task"])
        data = matcher.GetAPI(data)

    return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=True)