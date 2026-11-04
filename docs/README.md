# NIWI Documentation Index

Welcome to the NIWI (Neurodiversity Inclusion Workplace Index) documentation.

---

## 📚 Quick Navigation

### For New Developers
- **Start here**: [Main README](../README.md) - Project overview and setup
- **Architecture**: [System Architecture](architecture/NIWI_AZURE_SERVICE_BUS_ARCHITECTURE.md)
- **API Reference**: [API Documentation](api/)
- **Setup Guide**: [SETUP.md](SETUP.md)

### For Administrators
- **Deployment**: [Deployment Guide](operations/DEPLOYMENT_GUIDE.md)
- **Operations**: [Operations Documentation](operations/)
- **Troubleshooting**: Check [operations/](operations/) directory

### For QA and Testing
- **Testing Strategy**: [Product Audit - Testing Report](product-audit/05_TESTING_QA_AND_PERFORMANCE_REPORT.md)
- **Performance Testing**: [Performance Testing Guide](../tests/performance/README.md)
- **Test Files**: See [../tests/](../tests/) directory

### For Product Managers
- **Product Requirements**: [Product Audit](product-audit/)
- **Executive Summary**: [Executive Audit Summary](product-audit/EXECUTIVE_AUDIT_SUMMARY.md)
- **Calculation Logic**: [Formula Documentation](product-audit/06_FORMULA_AND_CALCULATION_LOGIC.md)

---

## 📁 Documentation Structure

### `/architecture/` - System Architecture
Complete technical architecture documentation including:
- Service Bus architecture
- Database design
- Backend and frontend architecture
- Infrastructure details

**Key Files**:
- [NIWI_AZURE_SERVICE_BUS_ARCHITECTURE.md](architecture/NIWI_AZURE_SERVICE_BUS_ARCHITECTURE.md) - Azure Service Bus integration

### `/api/` - API Documentation
Comprehensive API reference including:
- Endpoint documentation
- Authentication and authorization
- Request/response examples
- Error codes
- OpenAPI specification

**Key Files**:
- [API.md](API.md) - Main API documentation
- [API_INDEX.md](api/API_INDEX.md) - API endpoint index

### `/operations/` - Operations and Deployment
Production deployment and operations guides:
- Deployment procedures
- Rollback procedures
- Service Bus deployment
- Monitoring and troubleshooting

**Key Files**:
- [DEPLOYMENT_GUIDE.md](operations/DEPLOYMENT_GUIDE.md) - Main deployment guide
- [NIWI_DEPLOYMENT_AND_ROLLBACK_GUIDE.md](operations/NIWI_DEPLOYMENT_AND_ROLLBACK_GUIDE.md)
- [NIWI_SERVICE_BUS_DEPLOYMENT_AND_ROLLBACK.md](operations/NIWI_SERVICE_BUS_DEPLOYMENT_AND_ROLLBACK.md)

### `/product-audit/` - Product Documentation
Complete product audit and requirements:
- Product requirements document
- Frontend technical documentation
- Backend technical documentation
- System workflow and architecture
- Testing and QA reports
- Formula and calculation logic
- Executive audit summary

**Key Files**:
- [README.md](product-audit/README.md) - Product audit index
- [01_PRODUCT_REQUIREMENTS_DOCUMENT.md](product-audit/01_PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [EXECUTIVE_AUDIT_SUMMARY.md](product-audit/EXECUTIVE_AUDIT_SUMMARY.md)

### `/archive/` - Historical Documentation

#### `/archive/historical-reports/` - Implementation Reports
Historical implementation and verification reports from development phases:
- Implementation reports
- Pre/post deployment verification
- Performance and optimization reports
- Reliability audits
- Architecture audits

**Purpose**: Historical reference for understanding system evolution

#### `/archive/upgrades/` - Upgrade Documentation
Documentation from major version upgrades:
- Version 3.1 upgrade documentation
- Migration guides
- Upgrade diagnostics

#### `/archive/legacy/` - Legacy Documentation
Archived legacy documentation including:
- Old deployment guides
- Historical feature documentation
- Deprecated setup instructions

---

## 🔍 Finding Documentation

### By Topic

**Authentication & Security**:
- [API Authentication](api/AUTHENTICATION_AND_AUTHORIZATION.md)
- [Security Architecture](product-audit/03_BACKEND_TECHNICAL_DOCUMENTATION.md)

**Database**:
- [Database Migrations](../migrations/)
- [SQL Scripts](../sql/)
- [Database Architecture](architecture/)

**Frontend**:
- [Frontend Technical Docs](product-audit/02_FRONTEND_TECHNICAL_DOCUMENTATION.md)
- [Vue Components](../frontend/src/)

**Backend**:
- [Backend Technical Docs](product-audit/03_BACKEND_TECHNICAL_DOCUMENTATION.md)
- [API Routes](../app/api/)
- [Services](../app/services/)

**Testing**:
- [Testing Strategy](product-audit/05_TESTING_QA_AND_PERFORMANCE_REPORT.md)
- [Test Files](../tests/)
- [Performance Tests](../tests/performance/)

**Calculations**:
- [Formula Logic](product-audit/06_FORMULA_AND_CALCULATION_LOGIC.md)
- [Scoring Service](../app/services/scoring_service.py)

---

## 📝 Documentation Standards

### For Contributors

When updating documentation:

1. **Keep it current**: Update docs when code changes
2. **Be specific**: Include code examples and specific commands
3. **Test instructions**: Verify all commands and examples work
4. **Link related docs**: Add cross-references to related documentation
5. **Archive obsolete**: Move outdated docs to archive/ with dated filename

### Document Types

- **README.md**: Overview and quick start
- **GUIDE.md**: Step-by-step instructions
- **REFERENCE.md**: Comprehensive reference material
- **REPORT.md**: Analysis and audit reports (typically archived)

---

## 🔄 Recently Reorganized (November 2026)

Documentation was reorganized in November 2026 to improve navigation and reduce duplication:

**Changes**:
- Created clear directory structure by category
- Moved historical reports to `/archive/historical-reports/`
- Consolidated duplicate documentation
- Established this index for easy navigation
- Archived superseded SQL scripts to `../sql/archive/`

**If you can't find something**: Check `/archive/` directories or git history.

---

## 📞 Getting Help

- **Technical Questions**: Refer to [Product Audit](product-audit/)
- **Deployment Issues**: Check [Operations Documentation](operations/)
- **API Questions**: See [API Documentation](api/)
- **Setup Problems**: See [SETUP.md](SETUP.md) or [Main README](../README.md)

---

**Last Updated**: November 4, 2026  
**Documentation Version**: 2.0 (Post-Reorganization)
