import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    vertex_model: str
    gcp_project: str
    gcp_region: str


def get_settings() -> AppSettings:
    vertex_model = os.getenv("VERTEX_MODEL", "").strip()
    gcp_project = os.getenv("GCP_PROJECT", "").strip()
    gcp_region = os.getenv("GCP_REGION", "").strip()

    if not vertex_model or not gcp_project or not gcp_region:
        raise ValueError("Missing required configuration.")

    return AppSettings(
        vertex_model=vertex_model,
        gcp_project=gcp_project,
        gcp_region=gcp_region,
    )


def get_survey_path() -> str:
    path = os.getenv("SURVEY_PATH", "/survey").strip()
    if not path:
        return "/survey"
    if not path.startswith("/"):
        path = f"/{path}"
    return path
