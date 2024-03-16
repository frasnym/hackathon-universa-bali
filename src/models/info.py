import json


class Info:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer

    def to_dict(self):
        return {"question": self.question, "answer": self.answer}


# Custom encoder for Info objects
class InfoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Info):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)
