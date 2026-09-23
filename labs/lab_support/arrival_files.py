"""Publish the prepared files in a shared/local filesystem demonstration.

This helper belongs to the exercise harness, not to the Spark pipeline. A remote
classroom environment must provide an equivalent publisher for its shared storage.
Files are fully copied under an ignored dot-name, then exposed atomically without
replacing any existing input. A second publication of the same arrival fails.
"""

import os
import shutil
import tempfile
from pathlib import Path


def publish_arrival(data_root: Path, incoming: Path, number: int) -> str:
    """Publish one completed arrival atomically, refusing to overwrite an earlier delivery.

    Return the published basename. The destination filesystem must support hard
    links; temporary copies are removed on success and failure.
    """
    source = Path(data_root) / "arrivals" / f"{number:02d}"
    files = sorted(source.glob("*.parquet"))
    if len(files) != 1:
        raise ValueError(f"Expected exactly one prepared Parquet file in {source}")
    incoming = Path(incoming)
    incoming.mkdir(parents=True, exist_ok=True)
    target = incoming / f"arrival-{number:02d}.parquet"
    fd, staged = tempfile.mkstemp(prefix=".pending-", dir=incoming)
    os.close(fd)
    try:
        shutil.copyfile(files[0], staged)
        os.link(staged, target)
    finally:
        Path(staged).unlink(missing_ok=True)
    return target.name
