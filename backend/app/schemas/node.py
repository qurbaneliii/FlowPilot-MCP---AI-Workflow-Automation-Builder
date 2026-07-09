from pydantic import BaseModel, ConfigDict


class RegisteredNodeTypesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_types: list[str]
