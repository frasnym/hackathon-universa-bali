import os
import json
from abc import ABC
from typing import Optional, Any, Dict, Union

from ..utils.registry import object_id_generator
from ..utils.logs import get_logger


ConfigType = Union[str, Dict[str, Any]]


class ModelConfig:
    """
    Configuration for all AbstractModel.
    """

    def __init__(self, config: ConfigType, use_defaults: bool = True) -> None:
        """
        Initialize the ModelConfig instance.
        """
        self._config: Dict[str, Any] = config
        self.use_defaults = use_defaults

    @classmethod
    def from_config(cls, path_or_dict: ConfigType) -> "ModelConfig":
        """
        Create configuration instance from a specified path or dictionary.
        """
        if isinstance(path_or_dict, str):
            if not os.path.exists(path_or_dict):
                raise FileNotFoundError(f"Config file not found at {path_or_dict}")
            with open(path_or_dict, "r") as f:
                try:
                    _config = json.load(f)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON file at {path_or_dict}")
        elif isinstance(path_or_dict, dict):
            _config = path_or_dict
        else:
            raise ValueError("Path should be a string or dictionary.")
        
        return cls(config=_config)

    def enable_defaults(self, enable: bool) -> None:
        """
        Return the default configuration for the model when using `get()` method.
        If set to `False`, the `get()` method will always return `None`.
        """
        self.use_defaults = enable

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get the value of a parameter. If ModelConfig was set not to use defaults
        will always return `None`. Else, will return provided default.
        """
        try:
            return getattr(self, key)
        except AttributeError:
            return default if self.use_defaults else None
        
    def __getattr__(self, key: str) -> Any:
        """
        Get the value of a parameter - allows for config.attr notation.
        """
        try:
            return self._config[key]
        except KeyError:
            raise AttributeError(f"Attribute {key} not found in the configuration.")
        
    def get_dict(self) -> Dict[str, Any]:
        """
        Return the configuration as a dictionary.
        """
        return self._config


class AbstractModel(ABC):
    """
    Abstract representations of models. Currently it is implemented only by
    BaseLLM, but in the future it can be extended to different types of models.
    """

    def register(self) -> None:
        """
        Register the model in the registry.
        """
        self.model_id = object_id_generator.register(self)
        self.logger = get_logger(self.__class__.__name__)
    
    @staticmethod
    def load_config(path: str) -> ModelConfig:
        """
        Load configuration from a specified path.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at {path}")
        
        if path.endswith('.json'):
            return ModelConfig.from_config(path)
        else:
            raise NotImplementedError(f"Config file format not supported: {path.split('.')[-1]}")