import os

from dataclasses import dataclass, field


@dataclass
class Config:
    """
        TODO: Populate description
    """
    elastic_password: str = "changeme"
    elastic_host: str = "localhost"
    elastic_port: int = 9200
    elastic_username: str = "elastic"
    elastic_scheme: str = "http"

    @classmethod
    def from_env(cls):
        env_vars = {
            "elastic_host": "ELASTIC_API_HOST",
            "elastic_port": "ELASTIC_API_PORT",
            "elastic_username": "ELASTIC_USERNAME",
            "elastic_password": "ELASTIC_PASSWORD",
            "redis_host": "REDIS_HOST",
            "redis_port": "REDIS_PORT",
            "redis_password": "REDIS_PASSWORD",
            "nboost_host": "NBOOST_API_HOST",
            "nboost_port": "NBOOST_API_PORT"
        }

        kwargs = {}

        for kwarg, env_var in env_vars.items():
            env_value = os.environ.get(env_var)
            if env_value:
                kwargs[kwarg] = env_value

        return cls(**kwargs)
