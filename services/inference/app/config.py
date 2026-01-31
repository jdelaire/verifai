"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Inference service settings.

    All values without defaults are required and must be provided via
    environment variables (or a .env file when running locally).
    """

    # Shared secret used to authenticate inbound requests from the API gateway.
    shared_secret: str

    # Bearer token sent back to the callback URL so the API gateway can
    # verify the response actually came from this service.
    callback_auth_secret: str

    # HuggingFace model identifier for the AI-image detector.
    model_name: str = "umm-maybe/AI-image-detector"

    # Local directory where downloaded model weights are cached.
    model_cache_dir: str = "./model_cache"

    # Safety cap -- images larger than this on either axis are rejected.
    max_image_dimension: int = 4096

    # httpx timeout when downloading the source image from object storage.
    download_timeout_seconds: int = 30

    # Maximum wall-clock time allowed for a single inference run.
    inference_timeout_seconds: int = 60

    model_config = {"env_prefix": ""}


settings = Settings()  # type: ignore[call-arg]
