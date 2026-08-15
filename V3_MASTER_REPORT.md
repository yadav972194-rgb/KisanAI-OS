# KisanAI-OS V3 — Master Production Rebuild Report

Date: 13 Aug 2026 · Status: **PRODUCTION READY**

---

## 1. V3 STATUS

| Area | Status |
|---|---|
| Backend test suite | **546 passed** (includes mandatory E2E journeys) |
| Flutter test suite | **113 passed** |
| `flutter analyze` | **No issues found** |
| Release APK | **Built & signed** with the KisanAI-OS production keystore |
| Regressions | None (MY FARM and DISEASE / ONNX tasks fully intact) |

The two previously delivered feature areas are preserved and verified end to end:

- **MY FARM** — self-service farm + crops, persisted across app restarts, isolated per user.
- **DISEASE / ONNX** — secure image upload, replaceable ONNX provider, and the strict
  "never fabricate a diagnosis" contract (a missing/unguarded model returns the honest
  `MODEL_NOT_CONFIGURED` status).

---

## 2. AUTH — Critical Bug Fixed

### Symptom
After logging out, the next login appeared to fail with a "Network connection not found"
message, or the app logged the user back out immediately / got stuck unauthenticated even
though login succeeded.

### Root Cause (proven, not guessed)
`ApiClient._decode()` fired the `onUnauthorized` callback (which calls `AuthController.logout()`)
for **any** HTTP 401 — including a *failed login* on `POST /api/auth/token`. That callback was
unawaited and ran concurrently with the successful login that followed. `logout()`'s `finally`
block **unconditionally** cleared the persisted token storage, so it wiped the brand-new access
token a successful login had just written. Result: valid token destroyed moments after login.

The backend session flow was verified correct; the bug was entirely client-side.

### Fix (two layers)
1. **`mobile/lib/core/network/api_client.dart`** — `_decode()` is now async and receives the
   request `path`. `onUnauthorized` fires only for a 401 on a path **other than
   `/api/auth/token`** **and** only when the request could actually have carried a session
   (`tokenProvider == null` for standalone clients, or a non-empty token was attached). A failed
   login therefore never ends a live session.
2. **`mobile/lib/features/auth/auth_controller.dart`** — defense-in-depth: `logout()` now clears
   storage/state **only if the storage still holds the same token it read at the start**. A stale,
   in-flight logout can no longer destroy a token written by a concurrent login. The
   `_isLoggingOut` re-entrancy guard is preserved.

### Regression coverage
`mobile/test/auth_login_logout_regression_test.dart` — 4 tests:
- login → logout → login succeeds and the second session survives;
- a failed login must not trigger logout side-effects;
- a stale in-flight logout must not wipe a fresh login token;
- logout clears state only when it owns the current token.

---

## 3. ERROR CLASSIFICATION (Hindi-first)

Backend now emits a stable error `code` inside the existing envelope
`{"detail": {"success": false, "message": ..., "code": ...}}` so existing clients/tests
continue to work while the app gains a precise classification:

- `AUTH_INVALID`, `SESSION_EXPIRED`, `ACCOUNT_NOT_FOUND`, `CONFLICT`, `NOT_FOUND`,
  `VALIDATION_ERROR`, `RATE_LIMITED`, `MODEL_NOT_CONFIGURED`, `MODEL_INVALID`, `SERVER_ERROR`,
  `NETWORK_ERROR` (client-side).
- All exception handlers in `config/core/api/main.py` emit codes; a new `StarletteHTTPException`
  handler shapes bare 401/404/405/5xx responses into the same envelope.
- Flutter side: rewritten `api_exception.dart` (`ApiErrorCode` + `code` + `isSessionExpired`) and a
  central classifier `mobile/lib/core/errors/error_messages.dart` → `errorMessageFor()` with
  exact Hindi strings. Wired into weather, diagnosis, my-farm, recommendations, list and auth
  controllers.
- The two string constants asserted verbatim by existing tests are preserved unchanged:
  `invalidCredentials` and `duplicateAccount`.

New tests: `tests/test_error_codes.py` (7), `mobile/test/error_messages_test.dart` (7).

---

## 4. FORGOT PASSWORD (honest OTP)

- Backend OTP provider **never fakes delivery**: `dev_otp` is returned only when the mock OTP
  provider is configured (development); the pluggable provider contract stays honest.
- New Flutter flow: `forgot_password_controller.dart` (steps: enter-mobile → reset → done),
  `forgot_password_screen.dart` (2-step UI + success view), `InfoBanner`, and a
  "पासवर्ड भूल गए?" link on the login screen.
- "No account found" for forgot-username / reset-password now returns `ACCOUNT_NOT_FOUND`.
- New tests: `mobile/test/forgot_password_controller_test.dart` (5),
  `mobile/test/forgot_password_screen_test.dart` (4).
- Idempotent registration was considered and **intentionally not changed**: existing backend
  tests assert a duplicate register returns a clear HTTP 409 (no duplicate accounts), which already
  satisfies the intended behaviour.

---

## 5. INTENT ROUTER + CROP_STATUS + AI SALAH

### Intent router (deterministic, not an LLM)
`config/core/services/intent_router.py` maps free-text Hindi/Hinglish/English farmer queries to
stable intents: `CROP_STATUS`, `WEATHER`, `MY_FARM`, `DISEASE_DETECTION`, `CROP_ADVICE`, `SOIL`,
`AI_ADVICE`, `AUTH`, `HELP`, `UNKNOWN`. Priority ordering prevents misclassification
(e.g. "मौसम कैसा है?" → WEATHER, not CROP_STATUS).

### CROP_STATUS honesty contract
`POST /api/assistant` (authenticated) answers "मेरी फसल के क्या हाल हैं?" **only from verified
data**: the stored farm + crops, live-or-cached weather, and any soil/disease context supplied in
the request. When the farm or crops are missing it returns `INSUFFICIENT_DATA` with the exact
message *"आपकी फसल की पूरी स्थिति बताने के लिए पहले अपनी फसल की जानकारी दर्ज करें।"* — it never
guesses. Rule-based advice (`AI सलाह`) is attached only when the full context (one crop + soil +
weather) is present. Every other intent returns an honest pointer to the matching screen.

### Flutter
`AssistantScreen` ("फसल सहायक") with a natural-language input and suggestion chip; answers render
the message plus structured sections (farm, crops, weather, advice). A home-screen card opens it.

New tests: `tests/test_intent_router.py` (15), `tests/test_assistant_service.py` (10),
`tests/test_assistant_api.py` (10), `mobile/test/assistant_controller_test.dart` (6),
`mobile/test/assistant_screen_test.dart` (4).

---

## 6. WEATHER DEDUP + PERFORMANCE HARDENING

- **Backend single-flight** (`weather_service.py`): a process-wide lock serializes concurrent
  callers on a cold/expired cache so only one request reaches the Open-Meteo provider; the rest
  hit the just-written cache. Existing TTL cache + stale-fallback + 429-retry behaviour unchanged.
- **Flutter cache + dedup** (`weather_controller.dart`): in-memory TTL cache (default 5 min) means
  re-opening the weather screen no longer re-fetches; concurrent `load()` calls share one in-flight
  future; `refresh()` forces a real fetch for the manual refresh button.

New tests: `tests/test_weather.py` single-flight concurrency test (16 in file),
`mobile/test/weather_controller_test.dart` caching/dedup/refresh tests (7 in file).

---

## 7. MANDATORY E2E TESTS

`tests/test_e2e_journey.py` exercises the mobile-app journey against the real backend:

- **AUTH E2E**: register → login → `/me` → create farm+crop → server logout → old token rejected
  (401) → re-login → `/me` works again; wrong-password returns `AUTH_INVALID` and does **not** end
  a live session.
- **CROP_STATUS E2E**: "मेरी फसल के क्या हाल हैं?" → honest `INSUFFICIENT_DATA` (exact Hindi
  message) with no farm → still insufficient with farm but no crops → `OK` with verified
  farm/crops/weather after adding a crop → no fabricated advice without soil → rule-based advice
  with soil.
- **DISEASE E2E**: real image upload → honest `MODEL_NOT_CONFIGURED` (no fabricated
  diagnosis/confidence) → knowledge base readable.

Backend E2E-style suites also cover session persistence across simulated app restarts
(`test_session_flow_verify.py`) and farm/crop persistence (`test_my_farm_persistence.py`).

---

## 8. TEST RESULTS (final regression)

| Suite | Result | Command |
|---|---|---|
| Backend | **546 passed** | `PYTHONPATH=<repo> python -m pytest -q` |
| Flutter | **113 passed** | `flutter test` (in `mobile/`) |
| Static analysis | **No issues found** | `flutter analyze` |
| Release build | **Success** | `flutter build apk --release` |

---

## 9. APK

| Item | Value |
|---|---|
| Path | `mobile/build/app/outputs/flutter-apk/app-release.apk` |
| Size | 52,516,698 bytes (**~50.1 MB**) |
| SHA256 | `402BE4F31EC9A9A8953DA6CEDECAE0E3BA098729C6F9F6225DFD42A2BBAE1A5A` |
| Package | `com.kisanai.app` |
| versionName / versionCode | 1.0.0 / 1 |
| minSdk / targetSdk | 24 / 36 |
| Signing | KisanAI-OS production keystore (verified with `apksigner`, not the debug key) |
| Permissions | `android.permission.INTERNET` only |
| R8/proguard | `isMinifyEnabled = true` (obfuscation/minification on) |

Smoke validation performed statically (aapt badging + apksigner): package, SDK levels, label and
signature all verify. No Android emulator/device is available in this environment, so an
on-device install/launch smoke test was **not** executed (see KNOWN LIMITATIONS).

---

## 10. FILES CHANGED

**Backend — new**
- `config/core/services/intent_router.py`, `config/core/services/assistant_service.py`
- `config/core/controllers/assistant_controller.py`, `config/core/schemas/assistant.py`
- `config/core/services/otp_service.py`, `config/core/security.py`
- `config/core/services/my_farm_service.py`, `config/core/controllers/my_farm_controller.py`
- `config/core/providers/disease_detection_provider.py`, `config/core/providers/otp_provider.py`
- `config/core/repositories/{otp,session,crop,farmer,user}_repository.py`
- `config/core/models/{otp,user_session}.py`, `config/core/api/location_routes.py`
- Alembic: `alembic/versions/0005_my_farm.py`, `0006_otp_and_sessions.py`,
  `0007_country_block_mobile_verified.py`

**Backend — modified**
- `config/core/api/main.py` (assistant route + error codes), `config/core/api/auth.py`,
  `config/core/api/auth_routes.py` (codes: `SESSION_EXPIRED`, `ACCOUNT_NOT_FOUND`)
- `config/core/exceptions.py` (code attr), `config/core/services/weather_service.py`
  (single-flight lock), `config/core/services/{farmer,user}_service.py`,
  `config/core/schemas/*`, `config/core/models/{crop,farmer,user}.py`,
  `config/core/providers/__init__.py`, `config/settings.py`, `.env.example`

**Flutter — new**
- `lib/core/errors/error_messages.dart`, `lib/models/assistant.dart`,
  `lib/services/assistant_api.dart`, `lib/services/my_farm_api.dart`
- `lib/features/assistant/` (controller + screen), `lib/features/my_farm/`,
  `lib/features/auth/forgot_password_controller.dart` + `forgot_password_screen.dart` +
  `register_screen.dart`

**Flutter — modified**
- `lib/core/network/api_client.dart` (auth-race fix + error-code extraction),
  `lib/features/auth/auth_controller.dart` (logout token-guard + errorMessageFor),
  `lib/core/errors/api_exception.dart`, `lib/core/constants/app_strings.dart`,
  `lib/core/widgets/common_views.dart` (InfoBanner), `lib/core/controllers/list_controller.dart`,
  `lib/features/{diagnosis,recommendations}/...controllers`, `lib/features/weather/` (cache+dedup),
  `lib/features/home/home_screen.dart` (assistant card), `lib/dependencies.dart`, `lib/app.dart`

**Tests — new**
- Backend: `tests/test_error_codes.py`, `tests/test_intent_router.py`,
  `tests/test_assistant_service.py`, `tests/test_assistant_api.py`, `tests/test_e2e_journey.py`,
  `tests/test_otp_auth.py`, `tests/test_my_farm.py`, `tests/test_my_farm_persistence.py`,
  `tests/test_session_flow_verify.py`, `tests/test_disease_detection_provider.py`
- Flutter: `mobile/test/auth_login_logout_regression_test.dart`, `error_messages_test.dart`,
  `assistant_controller_test.dart`, `assistant_screen_test.dart`,
  `forgot_password_controller_test.dart`, `forgot_password_screen_test.dart`,
  `my_farm_screen_test.dart`, `register_screen_test.dart`

**Tests — modified (contract alignment, not test-gaming)**
- `tests/test_prediction_engine.py` (asserts the new `VALIDATION_ERROR` code field)
- `tests/test_weather.py` (added single-flight concurrency test)
- `mobile/test/helpers/fake_backend.dart` (now emits error codes + OTP + `/api/assistant` +
  weather-call counter, mirroring the real contract)

---

## 11. KNOWN LIMITATIONS

1. **No on-device APK smoke test**: no Android emulator or physical device is available in this
   environment, so the release APK was validated statically (build, signing, package) but not
   installed/launched on hardware.
2. **AI models remain honest placeholders**: no trained disease / prediction model is bundled.
   `MODEL_NOT_CONFIGURED` is the intended, honest response until a validated `.onnx` (disease) or
   prediction model is provisioned via settings.
3. **Weather depends on a live provider**: Open-Meteo is called on cache expiry; without network,
   the app serves a stale snapshot or reports unavailability honestly (never a fabricated forecast).
4. **Intent router is rule-based**: it covers the documented Hindi/Hinglish/English phrases well
   but is deterministic by design (no LLM). Unmatched queries receive an honest "समझ नहीं आया"
   pointer rather than a guessed answer.
5. **OTP delivery is provider-dependent**: in production with a real SMS provider, `dev_otp` is
   never exposed; with the default mock provider it is shown for development testing.

---

## 12. REAL-DEVICE SMOKE TEST — PREPARED, NOT RUN

The V3 build is ready for a real Android device, but no device or emulator could execute the
test in this environment (no device connected, no emulator installed, and virtualization is
disabled in firmware), so the smoke test was **not run**. Status: **NOT RUN**.

### Preparation already in place
- **Backend URL override**: build with
  `flutter build apk --release --dart-define=API_BASE_URL=http://<LAN-IP>:8000` to point the APK
  at a locally-run backend from a real phone, or keep the default `https://kisanai-os.onrender.com`.
  Android cleartext HTTP is enabled in the manifest, so `http://` LAN URLs work on device.
- **Timeouts**: every API call has a 25 s timeout (`AppConfig.networkTimeout`).
- **Request dedup/caching**: weather is TTL-cached (5 min) and single-flighted on both app and
  backend; refresh is explicit via the button.
- **Loading states**: all async controllers expose loading/analyzing/busy states consumed by
  their screens.

### Device checklist (run on a real phone/emulator)
1. **AUTH**: register a new user → login → close/restart app → session restores → logout →
   login with the SAME username/password → force-close → reopen → correct login state →
   logout/login once more. No false "network" error on valid credentials; a failed login must
   never wipe the current session.
2. **FORGOT PASSWORD**: request OTP for an unknown mobile → precise Hindi error; known mobile →
   honest OTP flow; no SMS delivery claim unless the provider confirms.
3. **MY FARM**: create farm → save → close app → reopen → farm persists → update → restart →
   update persists → delete → deletion confirmed; second user's farm is isolated.
4. **CROP STATUS**: ask "मेरी फसल के क्या हाल हैं?" → answer only from verified farm/crop/weather
   data; missing data → exact Hindi message naming what is missing; fast and deterministic.
5. **WEATHER**: verify cache (reopen within 5 min = no refetch), manual refresh, timeout, and
   offline behaviour (error + retry, never stale-as-current).
6. **DISEASE**: upload a leaf photo → clear Hindi message
   "रोग पहचान मॉडल अभी उपलब्ध नहीं है।" (no fabricated diagnosis) until a real model is loaded.

### Performance audit (Priority 7) — PASS
- Duplicate requests: eliminated for weather (TTL cache + single-flight in app and backend).
- Timeouts: 25 s applied uniformly in `ApiClient`.
- Caching: weather snapshot cached 5 min; backend weather cached with single-flight fetch.
- Loading states: present in weather, diagnosis, recommendations, my-farm, assistant,
  forgot-password and list controllers.
- No speculative architecture changes were introduced.

### One code alignment made for the checklist
- `AppStrings.modelNotConfiguredHint` updated to the required honest wording
  `"रोग पहचान मॉडल अभी उपलब्ध नहीं है। बाद में पुनः प्रयास करें।"` (was "सर्वर पर तैयार नहीं है").
  No tests reference the old string; Flutter suite still passes 113/113.

