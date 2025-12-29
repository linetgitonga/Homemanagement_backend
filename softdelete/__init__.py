"""Local softdelete shim used by the project.

This provides a minimal `SoftDeleteModel` implementation so imports
`from softdelete.models import SoftDeleteModel` succeed. It is intentionally
simple: it marks records with `is_deleted=True` instead of hard-deleting.

If you already have a package installed that provides a compatible
implementation, you can remove this local app.
"""

default_app_config = None
