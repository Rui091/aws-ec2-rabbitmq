import logging
import os
import importlib
from functools import lru_cache

logger = logging.getLogger(__name__)

try:
    boto3 = importlib.import_module("boto3")
    botocore_exceptions = importlib.import_module("botocore.exceptions")
    BotoCoreError = botocore_exceptions.BotoCoreError
    ClientError = botocore_exceptions.ClientError
    NoCredentialsError = botocore_exceptions.NoCredentialsError
except Exception:  # pragma: no cover
    boto3 = None
    BotoCoreError = Exception
    ClientError = Exception
    NoCredentialsError = Exception


def _aws_region() -> str:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


@lru_cache(maxsize=1)
def _ssm_client():
    if boto3 is None:
        return None
    return boto3.client("ssm", region_name=_aws_region())


def get_ssm_parameter(name: str, default: str) -> str:
    if not name:
        return default

    client = _ssm_client()
    if client is None:
        logger.debug("boto3 not available, using default for %s", name)
        return default

    try:
        response = client.get_parameter(Name=name, WithDecryption=True)
        value = response.get("Parameter", {}).get("Value")
        return value or default
    except (ClientError, BotoCoreError, NoCredentialsError) as exc:
        logger.warning("Could not resolve SSM parameter %s: %s", name, exc)
        return default


def _resolve_host(explicit_host_env: str, ssm_param_env: str, default_host: str) -> str:
    explicit_host = os.getenv(explicit_host_env)
    if explicit_host:
        return explicit_host

    ssm_param_name = os.getenv(ssm_param_env, "")
    return get_ssm_parameter(ssm_param_name, default_host)


def build_rabbitmq_url(default_host: str = "rabbitmq") -> str:
    full_url = os.getenv("RABBITMQ_URL")
    if full_url:
        return full_url

    host = _resolve_host("RABBITMQ_HOST", "SSM_RABBITMQ_HOST_PARAM", default_host)
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASS", "guest")
    return f"amqp://{user}:{password}@{host}:5672/"


def build_database_url(default_host: str = "postgres") -> str:
    full_url = os.getenv("DATABASE_URL")
    if full_url:
        return full_url

    host = _resolve_host("DATABASE_HOST", "SSM_DATABASE_HOST_PARAM", default_host)
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_name = os.getenv("POSTGRES_DB", "appdb")
    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{db_name}"


def build_api_url(default_url: str = "http://api:8000") -> str:
    api_url = os.getenv("API_URL")
    if api_url:
        return api_url

    lb_host = get_ssm_parameter(os.getenv("SSM_API_URL_PARAM", ""), "")
    if lb_host:
        return f"http://{lb_host}"

    return default_url
