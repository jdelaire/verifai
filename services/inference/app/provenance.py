"""Content-provenance (C2PA) verification.

TODO: Integrate the c2pa-python library once it is stable enough for
production use.  The C2PA SDK will let us parse embedded manifests and
verify the trust chain, giving us a much stronger provenance signal.
"""

from __future__ import annotations

from app.schemas import ProvenanceResult


def check_provenance(image_bytes: bytes) -> ProvenanceResult:  # noqa: ARG001
    """Check for C2PA content-provenance data in the image.

    Parameters
    ----------
    image_bytes:
        The raw bytes of the image file (unused in the MVP stub).

    Returns
    -------
    ProvenanceResult
        For the MVP this always reports that C2PA data is absent.
    """

    # TODO: Replace this stub with real C2PA manifest parsing using
    # the c2pa-python library (https://github.com/contentauth/c2pa-python).
    return ProvenanceResult(
        c2pa_present=False,
        c2pa_valid=None,
        notes=["C2PA verification not yet implemented"],
    )
