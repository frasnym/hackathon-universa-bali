from flask import Flask, jsonify, request

import matcher

from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.config["CORS_HEADERS"] = "application/json"


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
