import uuid
import ctypes
from typing import Any


class ItemExists(Exception):
    __name__ = "ItemExists"
    __desc__ = "Item `{}` already exists in the registry with value `{}`."

    def __init__(self, key, value, **kwargs) -> None:
        desc = self.__desc__.format(key, value)
        super().__init__(*(desc, ), **kwargs)

class ItemNotFound(Exception):
    __name__ = "ItemNotFound"
    __desc__ = "Item `{}` does not exist in the registry."

    def __init__(self, key, **kwargs) -> None:
        desc = self.__desc__.format(key)
        super().__init__(*(desc, ), **kwargs)


def generate_id(id_step: int = 0) -> str:
    """
    Generate a unique ID.
    """
    return str(uuid.uuid4())[::id_step]

class Registry:

    def __init__(self):
        self.registry = {}

    def register(self, key, value):
        if key not in self:
            self[key] = value
        raise ItemExists(
            key, self[key]
        )
        
    def unregister(self, key):
        del self[key]
        
    def __getitem__(self, key):
        if key not in self.registry:
            raise ItemNotFound(key)
        return self.registry.get(key)
    
    def __setitem__(self, key, value):
        self.registry[key] = value
        
    def __len__(self):
        return len(self.registry)
    
    def __delitem__(self, key):
        del self.registry[key]
    
    def __iter__(self):
        return iter(self.registry)
    
    def __contains__(self, key):
        return key in self.registry
    
    def __str__(self):
        return str(self.registry)
    
    def __repr__(self):
        return repr(self.registry)
    

class IDGenerator(Registry):
    """ID generator creates registry based on memory reference of objects."""

    def __init__(self, id_step: int = 5):
        """
        Initialize the ID generator.

        Args:
            * id_step (int): Take only `id_step` of the characters in ID. Results in shorter IDs.
        """
        super().__init__()
        self.id_step = max(0, min(id_step, 36))

    def register(self, _object: Any) -> str:
        """
        Register an object by its memory reference # and return a unique ID.
        """
        _id = generate_id(self.id_step)
        self[_id] = id(_object)
        return _id
    
    def unregister(self, _id: str):
        return super().unregister(_id)
    
    def retrieve(self, _id: str) -> Any:
        """
        Retrieve an object by its unique ID.
        """
        return ctypes.cast(self[_id], ctypes.py_object).value
    
object_id_generator = IDGenerator(id_step=3)  # we want short IDs for objects