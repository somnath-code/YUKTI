from packages.accessibility.checks import validate_pdf
from packages.contracts.models import ArtifactStore


def check(storage: ArtifactStore, checksum: str, pages: int) -> None:
    validate_pdf(storage.get(checksum), pages)
