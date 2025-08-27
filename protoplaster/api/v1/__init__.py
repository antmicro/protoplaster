from flask import Blueprint

import protoplaster.api.v1.configs


def create_routes() -> Blueprint:
    api_routes: Blueprint = Blueprint("protoplaster-api-v1", __name__)
    api_routes.register_blueprint(
        protoplaster.api.v1.configs.configs_blueprint)
    return api_routes
