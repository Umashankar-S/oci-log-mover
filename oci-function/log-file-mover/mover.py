import logging
import time
from typing import Optional

from oci.object_storage import ObjectStorageClient
from oci.object_storage.models import CopyObjectDetails
from oci.exceptions import ServiceError

from parser import extract_yyyymmdd, date_to_path, filename_from_object_name


logger = logging.getLogger(__name__)


class MoveStats:
    def __init__(self):
        self.scanned = 0
        self.moved = 0
        self.skipped_existing = 0
        self.skipped_invalid_name = 0
        self.failed = 0


class ObjectMover:
    def __init__(
        self,
        client: ObjectStorageClient,
        namespace: str,
        source_bucket: str,
        dest_bucket: str,
        source_prefix: str,
        dest_root_prefix: str,
        destination_region: str,
        dry_run: bool,
        delete_source: bool,
        preserve_source_prefix: bool,
        source_keep_object_name: str,
        max_objects_per_run: int,
        verify_retries: int,
        verify_delay_seconds: float,
    ):
        self.client = client
        self.namespace = namespace
        self.source_bucket = source_bucket
        self.dest_bucket = dest_bucket
        self.source_prefix = source_prefix
        self.dest_root_prefix = dest_root_prefix
        self.destination_region = destination_region
        self.dry_run = dry_run
        self.delete_source = delete_source
        self.preserve_source_prefix = preserve_source_prefix
        self.source_keep_object_name = source_keep_object_name
        self.max_objects_per_run = max_objects_per_run
        self.verify_retries = verify_retries
        self.verify_delay_seconds = verify_delay_seconds
        self.source_keep_key = self._build_source_keep_key()

    def run(self) -> MoveStats:
        stats = MoveStats()
        next_start_with: Optional[str] = None
        self._ensure_source_keep_placeholder()

        while stats.scanned < self.max_objects_per_run:
            limit = min(1000, self.max_objects_per_run - stats.scanned)
            response = self.client.list_objects(
                namespace_name=self.namespace,
                bucket_name=self.source_bucket,
                prefix=self.source_prefix or None,
                start=next_start_with,
                limit=limit,
            )

            objects = response.data.objects or []
            if not objects:
                break

            for obj in objects:
                if stats.scanned >= self.max_objects_per_run:
                    break

                stats.scanned += 1
                source_name = obj.name

                if source_name.endswith("/"):
                    continue
                if self.source_keep_key and source_name == self.source_keep_key:
                    continue

                try:
                    self._move_one(source_name, stats)
                except Exception as exc:  # pylint: disable=broad-except
                    stats.failed += 1
                    logger.exception("Failed moving %s: %s", source_name, exc)

            next_start_with = response.data.next_start_with
            if not next_start_with:
                break

        return stats

    def _move_one(self, source_name: str, stats: MoveStats) -> None:
        filename = filename_from_object_name(source_name)

        try:
            yyyymmdd = extract_yyyymmdd(filename)
        except ValueError:
            stats.skipped_invalid_name += 1
            logger.warning("Skipping object with unsupported filename: %s", source_name)
            return

        date_path = date_to_path(yyyymmdd)
        dest_name = f"{self.dest_root_prefix}/{date_path}/{filename}"

        if self._exists(self.dest_bucket, dest_name):
            stats.skipped_existing += 1
            logger.info("Destination already exists, skipping: %s", dest_name)
            return

        logger.info("Moving %s -> %s", source_name, dest_name)

        if self.dry_run:
            stats.moved += 1
            return

        copy_details = CopyObjectDetails(
            source_object_name=source_name,
            destination_region=self.destination_region,
            destination_namespace=self.namespace,
            destination_bucket=self.dest_bucket,
            destination_object_name=dest_name,
        )

        self.client.copy_object(
            namespace_name=self.namespace,
            bucket_name=self.source_bucket,
            copy_object_details=copy_details,
        )

        if not self._wait_for_object(self.dest_bucket, dest_name):
            raise RuntimeError(f"Copy verification failed for destination object {dest_name}")

        if self.delete_source:
            self.client.delete_object(
                namespace_name=self.namespace,
                bucket_name=self.source_bucket,
                object_name=source_name,
            )

        stats.moved += 1

    def _exists(self, bucket_name: str, object_name: str) -> bool:
        try:
            self.client.head_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name,
            )
            return True
        except ServiceError as err:
            if err.status == 404:
                return False
            raise

    def _wait_for_object(self, bucket_name: str, object_name: str) -> bool:
        if self._exists(bucket_name, object_name):
            return True

        for attempt in range(1, self.verify_retries + 1):
            time.sleep(self.verify_delay_seconds)
            if self._exists(bucket_name, object_name):
                if attempt > 1:
                    logger.info(
                        "Destination became visible after %d retries: %s",
                        attempt,
                        object_name,
                    )
                return True

        return False

    def _build_source_keep_key(self) -> Optional[str]:
        if not self.source_keep_object_name:
            return None

        cleaned_prefix = self.source_prefix.strip("/")
        cleaned_keep_name = self.source_keep_object_name.lstrip("/")
        if not cleaned_prefix:
            return None

        return "{}/{}".format(cleaned_prefix, cleaned_keep_name)

    def _ensure_source_keep_placeholder(self) -> None:
        if not self.delete_source:
            return
        if self.dry_run:
            return
        if not self.preserve_source_prefix:
            return
        if not self.source_keep_key:
            return
        if self._exists(self.source_bucket, self.source_keep_key):
            return

        logger.info("Creating source placeholder object: %s", self.source_keep_key)
        self.client.put_object(
            namespace_name=self.namespace,
            bucket_name=self.source_bucket,
            object_name=self.source_keep_key,
            put_object_body=b"",
        )
