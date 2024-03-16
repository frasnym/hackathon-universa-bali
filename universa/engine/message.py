import time
import json
from typing import Any, Dict

from ..utils.registry import generate_id


class BaseMessage:
    """
    Base message class.
    """

    def __init__(self, content: str) -> None:
        self.content = content
        self.timestamp = int(time.time())
        self.message_id = generate_id()
        self._type = str

    @property
    def content_type(self) -> type:
        return self._type
    
    @content_type.setter
    def content_type(self, _type: type) -> None:
        self._type = _type

    @classmethod
    def from_dict(cls, content: Dict[str, Any]) -> "BaseMessage":
        """
        Create a message from a dictionary.
        """
        content = json.dumps(content)
        message = cls(content)
        message.content_type = dict

        return message
    
    def to_original_type(self) -> Any:
        """
        Convert the content to its original type.
        """
        if self.content_type == dict:
            return json.loads(self.content)
        else:
            return self.content
        
    def __getattr__(self, key: str):
        try:
            return self.__getattribute__(key)
        except AttributeError:
            return None

    def __repr__(self) -> str:
        """
        Create a string representation of the agent message.
        """
        _msg = f"ID: {self.message_id}\n"
        _msg += f"Time: {self.timestamp}"
        _msg += f"Message: {self.content}"
        return _msg
    

class AgentMessage(BaseMessage):
    """
    Agent messages are communicated between agents.
    """

    def set_communicators(
            self,
            sender_id: str,
            receiver_id: str,
            expect_reply: bool
    ) -> None:
        """
        Update the message with sender and receiver.
        """
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.expect_reply = expect_reply

    def __repr__(self) -> str:
        """
        Create a string representation of the agent message.
        """
        _msg = super().__repr__()
        _msg += f"Sender ID: {self.sender_id}\n" if self.sender_id else ""
        _msg += f"Receiver ID: {self.receiver_id}\n" if self.receiver_id else ""
        _msg += f"Expect Reply: {self.expect_reply}" if self.expect_reply else ""
        return _msg

    
class NodeMessage(BaseMessage):
    """
    Node messages are passed within the graph.
    """

    def set_node(self, node_id: str) -> None:
        """
        Set the node id for the message.
        """
        self.node_id = node_id

    def __repr__(self) -> str:
        """
        Create a string representation of the node message.
        """
        _msg = super().__repr__()
        _msg += f"Node ID: {self.node_id}" if self.node_id else ""
        return _msg