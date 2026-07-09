from app.core.tenant.middleware import (
    tenant_scoped,
    role_minimum,
    owns_resource,
)

from app.core.tenant.middleware import (
    tenant_scoped,
    role_minimum as role_minimum_original,
    owns_resource as owns_resource_original,
)

school_scoped = tenant_scoped
institution_scoped = tenant_scoped

__all__ = ['school_scoped', 'institution_scoped', 'tenant_scoped', 'role_minimum', 'owns_resource']
