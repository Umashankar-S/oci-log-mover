import os


class Config:
    """Runtime configuration from environment variables."""

    SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]
    DEST_BUCKET = os.environ["DEST_BUCKET"]

    # Prefix where service connector writes logs, e.g. default_ns/ocid1.serviceconnector...
    SOURCE_PREFIX = os.getenv("SOURCE_PREFIX", "").strip()

    # Destination root expected by requirement, e.g. default_ns
    DEST_ROOT_PREFIX = os.getenv("DEST_ROOT_PREFIX", "default_ns").strip("/")
    # Required by copy_object API in newer SDKs. If empty, code auto-detects client region.
    DEST_REGION = os.getenv("DEST_REGION", "").strip()

    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    DELETE_SOURCE = os.getenv("DELETE_SOURCE", "true").lower() == "true"
    MAX_OBJECTS_PER_RUN = int(os.getenv("MAX_OBJECTS_PER_RUN", "1000"))
    VERIFY_RETRIES = int(os.getenv("VERIFY_RETRIES", "20"))
    VERIFY_DELAY_SECONDS = float(os.getenv("VERIFY_DELAY_SECONDS", "1.0"))
    PRESERVE_SOURCE_PREFIX = os.getenv("PRESERVE_SOURCE_PREFIX", "true").lower() == "true"
    SOURCE_KEEP_OBJECT_NAME = os.getenv("SOURCE_KEEP_OBJECT_NAME", ".keep").strip()
