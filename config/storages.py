"""Custom static-files storage backends."""
from whitenoise.storage import CompressedManifestStaticFilesStorage


class ForgivingManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Content-hashed + compressed static files (auto cache-busting), but
    tolerant: a missing referenced asset degrades to the un-hashed name
    instead of raising a 500 across the whole site.
    """

    manifest_strict = False
