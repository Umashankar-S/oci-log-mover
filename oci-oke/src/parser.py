import os
import re


DATE_RE = re.compile(r"^(?P<date>\d{8})T")


def extract_yyyymmdd(filename: str) -> str:
    """Extract YYYYMMDD from file names like 20260408T102655Z_...log.gz."""
    match = DATE_RE.match(filename)
    if not match:
        raise ValueError(f"Unable to extract date from filename: {filename}")
    return match.group("date")


def date_to_path(yyyymmdd: str) -> str:
    return f"{yyyymmdd[0:4]}/{yyyymmdd[4:6]}/{yyyymmdd[6:8]}"


def filename_from_object_name(object_name: str) -> str:
    return os.path.basename(object_name.rstrip("/"))
