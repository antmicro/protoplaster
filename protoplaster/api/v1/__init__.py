from flask import Blueprint

import protoplaster.api.v1.configs
import protoplaster.api.v1.test_runs


def create_routes() -> Blueprint:
    api_routes: Blueprint = Blueprint("protoplaster-api-v1", __name__)
    api_routes.register_blueprint(
        protoplaster.api.v1.configs.configs_blueprint)
    api_routes.register_blueprint(
        protoplaster.api.v1.test_runs.test_runs_blueprint)
    return api_routes
