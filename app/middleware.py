from app.core.tenant.middleware import (
    tenant_scoped as school_scoped,
    role_minimum,
    owns_resource,
)

from app.core.tenant.middleware import (
    tenant_scoped,
    role_minimum as role_minimum_original,
    owns_resource as owns_resource_original,
)

# Convenience aliases
__all__ = ['school_scoped', 'role_minimum', 'owns_resource']
