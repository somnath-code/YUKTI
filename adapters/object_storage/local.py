import os
import re
import tempfile
from pathlib import Path
from packages.provenance.sources import digest


class LocalArtifacts:
    def __init__(self, directory: Path):
        self.directory = directory

    def path(self, checksum: str) -> Path:
        if not re.fullmatch('[0-9a-f]{64}', checksum):
            raise ValueError('Invalid artifact digest')
        return self.directory / checksum[:2] / checksum

    def put(self, data: bytes) -> str:
        checksum = digest(data)
        path = self.path(checksum)
        try:
            path.parent.mkdir(parents=True, mode=0o2770)
        except FileExistsError:
            pass
        else:
            path.parent.chmod(0o2770)
        fd, name = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fchmod(stream.fileno(), 0o660)
                os.fsync(stream.fileno())
            try:
                os.link(name, path)
            except FileExistsError:
                pass
        finally:
            os.unlink(name)
        self.get(checksum)
        return checksum

    def get(self, checksum: str) -> bytes:
        data = self.path(checksum).read_bytes()
        if digest(data) != checksum:
            raise OSError('Artifact checksum mismatch')
        return data
