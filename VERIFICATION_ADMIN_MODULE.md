# Verification Report — Admin Control & Farmer Support Module

## Status
COMPLETE. No commit made (per directive). All evidence below is from final runs.

## Test evidence
- Backend: `python -m pytest tests/ -q` → **850 passed** (1 pre-existing StarletteDeprecationWarning), 96s.
  - Includes 50 new admin tests: `test_admin_support.py`, `test_admin_audit.py`, `test_admin_super_admin.py`, `test_admin_isolation.py`.
- Mobile: `flutter test` → **220 passed** (16 new in `admin_controller_test.dart`).
- Mobile: `flutter analyze lib` → **0 new issues** (17 remaining are all pre-existing info-level lints). Test helper files: `flutter analyze test/admin_controller_test.dart test/helpers/fake_backend.dart` → clean.

## Files created
### Backend
- `alembic/versions/0008_admin_support_module.py` — feedback, contact_record, admin_audit_log, notification; `users.super_admin`.
- `config/core/schemas/admin.py`, `config/core/schemas/support.py` — admin/support schemas (`ContactCreate.farmer_id` optional).
- `config/core/services/audit.py`, `admin_user.py`, `support.py`, `notification.py`, `admin_farmer.py` (under existing service layout).
- `config/core/api/admin_routes.py` — 22 `/api/admin` paths registered via `main.py` (verified in `app.openapi()['paths']`; router surfaces as `_IncludedRouter`, not in `app.routes`).
- Tests: `tests/test_admin_{support,audit,super_admin,isolation}.py`; conftest additions (`super_admin_headers`, `_register_and_login(super_admin=...)`).

### Mobile
- `lib/models/admin_models.dart` (AdminSummary, FarmerProfile, ContactRecord, FeedbackItem, NotificationItem, AuditEntry, DeletePreview).
- `lib/services/admin_api.dart` (thin `/api/admin/*` wrappers).
- `lib/features/admin_admin/` — `admin_controller.dart` + 6 screens (hub, farmers directory, farmer profile w/ deactivate/restore/delete-preview, problems workflow, notifications, audit).
- `lib/core/network/api_client.dart` — additive `patchJson`.
- `lib/dependencies.dart` (AdminApi + AdminController registration), `lib/features/home/home_screen.dart` (role-gated `admin` card), `lib/core/constants/app_strings.dart` (Hindi admin strings).
- `test/admin_controller_test.dart`, `test/helpers/fake_backend.dart` (admin routes).

## Route mapping (backend <-> mobile)
- `/api/admin/me` → admin hub summary + super-admin detection.
- `/api/admin/farmers` (search `?q=`), `/api/admin/farmers/{id}`, crops, soils, contacts, problems, deactivate/restore, `delete/preview`, `DELETE ...?confirm=true`.
- `/api/admin/problems` (list/create/update/PATCH status), `/api/admin/notifications` (list/create/POST deliver), `/api/admin/audit`, `/api/admin/users/*`.
- Delivery route returns `{"success": true, "message": "Notification marked as delivered"}` (MessageOut shape).

## Blockers / notes
- Migration `0008` applied automatically for tests (conftest) but **not** yet applied to the dev DB `kisanai.db` — run `alembic upgrade head` before manual API verification.
- Flutter screen-level widget tests for the admin UI not added (controller + fake-backend integration covered); no emulator/device run performed.
- Bootstrap admin now creates `super_admin=True`; the "last active super-admin" guard is exercised at service level via monkeypatch (unreachable through the API in tests).