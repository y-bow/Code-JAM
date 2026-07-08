from app.models.tenant import School as Institution, AcademicYear
from .middleware import tenant_scoped, role_minimum, owns_resource
