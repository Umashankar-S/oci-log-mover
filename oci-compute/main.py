import logging
import re

import oci

from config import Config
from mover import ObjectMover


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def build_client() -> oci.object_storage.ObjectStorageClient:
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    return oci.object_storage.ObjectStorageClient(config={}, signer=signer)


def detect_region(client: oci.object_storage.ObjectStorageClient) -> str:
    explicit = Config.DEST_REGION
    if explicit:
        return explicit

    endpoint = getattr(client.base_client, "endpoint", "") or ""
    match = re.search(r"objectstorage\.([a-z0-9-]+)\.oraclecloud\.com", endpoint)
    if match:
        return match.group(1)

    raise RuntimeError(
        "Unable to detect destination region from client endpoint. Set DEST_REGION explicitly."
    )


def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)

    client = build_client()
    namespace = client.get_namespace().data
    destination_region = detect_region(client)
    logger.info("Using destination region for copy: %s", destination_region)

    mover = ObjectMover(
        client=client,
        namespace=namespace,
        source_bucket=Config.SOURCE_BUCKET,
        dest_bucket=Config.DEST_BUCKET,
        source_prefix=Config.SOURCE_PREFIX,
        dest_root_prefix=Config.DEST_ROOT_PREFIX,
        destination_region=destination_region,
        dry_run=Config.DRY_RUN,
        delete_source=Config.DELETE_SOURCE,
        preserve_source_prefix=Config.PRESERVE_SOURCE_PREFIX,
        source_keep_object_name=Config.SOURCE_KEEP_OBJECT_NAME,
        max_objects_per_run=Config.MAX_OBJECTS_PER_RUN,
        verify_retries=Config.VERIFY_RETRIES,
        verify_delay_seconds=Config.VERIFY_DELAY_SECONDS,
    )

    stats = mover.run()
    logger.info(
        "Run complete. scanned=%d moved=%d skipped_existing=%d skipped_invalid_name=%d failed=%d dry_run=%s delete_source=%s",
        stats.scanned,
        stats.moved,
        stats.skipped_existing,
        stats.skipped_invalid_name,
        stats.failed,
        Config.DRY_RUN,
        Config.DELETE_SOURCE,
    )

    return 0 if stats.failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
