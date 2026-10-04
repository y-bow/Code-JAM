# Gap Analysis: Hive vs Original Vision

## The Gap

The onboarding experience currently does NOT match the original vision:

| Step | Current | Required |
|------|---------|----------|
| Fresh Clone | ✅ | ✅ |
| Setup Wizard | ✅ | ✅ |
| Create Administrator | ✅ (step 1) | ✅ |
| Create Institution | ✅ (step 2) | ✅ |
| Choose Theme | ✅ (step 3) | ✅ |
| Configure Academic System | ❌ MISSING | ✅ (step 5) |
| Bulk Import Data | ❌ MISSING | ✅ (step 6 - REQUIRED) |
| Login with Data | ❌ Empty dashboard | ✅ (populated dashboard) |

## New Issues Created

### #30: Add Department model and migration for academic hierarchy
**Why**: The PRD and Architecture specify Department between Institution and Section. Currently there is no Department model. Required before academic configuration.

### #31: Add transactional rollback and username auto-generation to import system
**Why**: The current import partially succeeds (skips invalid rows). The vision requires all-or-nothing transactional import. Username generation is needed for login.

### #34: Add missing bulk import types: departments, sections, clubs, attendance, grades
**Why**: Currently only 5 import types exist. Vision requires 9 types (5 required + 2 optional). Missing: departments, sections, clubs, attendance, grades.

### #32: Extend Setup Wizard with Academic Configuration step
**Why**: After Theme selection, admin must configure Academic Year, Departments, and Sections before import. Currently missing from wizard.

### #35: Integrate Bulk Import as required Setup Wizard step
**Why**: The vision mandates bulk import as a REQUIRED wizard step. Currently import is a separate page. After import, accounts are created, passwords assigned, and only then should login work.

### #33: Ensure first login redirects to populated dashboard
**Why**: After setup completes, the dashboard must already contain institution data. An empty ERP after setup is unacceptable.

## Implementation Order

1. #30 - Department model (foundation)
2. #31 - Transactional rollback + username (infrastructure)
3. #34 - Missing import types (capability)
4. #32 - Academic configuration step (wizard extension)
5. #35 - Import integration into wizard (wizard extension)
6. #33 - Populated dashboard (final UX)
