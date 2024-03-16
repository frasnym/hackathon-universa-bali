from pathlib import Path


config_path = Path(__file__).parent
default_configs = {
    'mixtral': str(config_path / 'mixtral.json'),
}