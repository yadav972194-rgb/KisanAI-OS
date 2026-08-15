# KisanAI Mobile App

Hindi-first Flutter (Android) companion for the KisanAI backend. It covers
login/session handling, a dashboard, live weather, farmer/crop/soil/disease
read-only foundations, photo-based disease diagnosis, and the AI
recommendation engine.

All data comes from the real FastAPI endpoints (see the API contract in the
root `README.md`). No secrets are stored in the app; the only configuration is
the backend URL.

## Requirements

- Flutter 3.44+ (Dart 3.12+)
- Android SDK (minSdk 23, compileSdk from the Flutter SDK)
- A running KisanAI backend (`python main.py` from the repository root)

## Setup

```bash
cd mobile
flutter pub get
```

## Run

The default API base URL is `https://kisanai-os.onrender.com` — the production
backend.

```bash
flutter run
```

For local development against a backend running on your machine, point the app
at it with `--dart-define`:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # Android emulator
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000  # physical device
```

For a custom backend, override the same way for any command.

## Test

```bash
flutter test
```

The suite uses an in-memory token store and a mocked HTTP client, so no
device, emulator, or backend is needed.

## Analyze

```bash
flutter analyze
```

## Build

```bash
flutter build apk --debug
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.com
```

The debug APK is written to `build/app/outputs/flutter-apk/app-debug.apk`.

## Release (Play Store)

Release configuration lives in `android/app/build.gradle.kts`:

- **Application ID:** `com.kisanai.app`
- **Version:** `1.0.0+1` (`versionName`/`versionCode` are read from `pubspec.yaml`)
- **minSdk / targetSdk / compileSdk:** 24 / 36 / 36 (from the Flutter SDK defaults)
- **Signing:** release builds are signed with the keystore below.
- **R8:** minification enabled via `android/app/proguard-rules.pro` (shrinking off).

### Point the app at the production backend

The default `API_BASE_URL` is already `https://kisanai-os.onrender.com`, so a
plain release build talks to production. Override it only when building for a
different backend:

```bash
flutter build apk --release --dart-define=API_BASE_URL=https://api.your-backend.com
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.your-backend.com
```

### Release signing

Secrets are never committed. The signing config reads environment variables
first, then falls back to a local, git-ignored file:

1. **Keystore** (already generated on this machine):
   `mobile/android/app/kisanai-release.jks` — **back this file up.** The Play
   Store release key can never be replaced; losing it means you cannot publish
   updates to the existing application.
2. **Credentials** in `mobile/android/key.properties` (git-ignored):
   `storeFile`, `storePassword`, `keyAlias`, `keyPassword`.
3. **Environment overrides (preferred for CI):**
   `KISANAI_STORE_FILE`, `KISANAI_STORE_PASSWORD`, `KISANAI_KEY_ALIAS`,
   `KISANAI_KEY_PASSWORD`.

To create a fresh keystore yourself (e.g. on a new machine or for a different
alias):

```powershell
keytool -genkeypair -v -keystore app/kisanai-release.jks -alias kisanai `
  -keyalg RSA -keysize 2048 -validity 10000 -storepass CHANGE_ME `
  -dname "CN=KisanAI-OS, OU=Mobile, O=KisanAI, L=New Delhi, ST=Delhi, C=IN"
```

Then update `android/key.properties` with the new passwords.

### Release commands

```bash
flutter pub get
flutter analyze
flutter test

# Signed release APK (defaults to the production backend)
flutter build apk --release
# -> build/app/outputs/flutter-apk/app-release.apk

# Android App Bundle (what you upload to Google Play)
flutter build appbundle --release
# -> build/app/outputs/bundle/release/app-release.aab
```

### Toolchain (verified)

- Flutter 3.44.9 stable / Dart 3.12.2
- Android SDK 36.0.0 (`C:\Android\Sdk`)
- JDK: Microsoft OpenJDK 17.0.20 (`C:\Android\jdk-17`, `JAVA_HOME` set)
- Gradle 9.1.0 wrapper / AGP 9.0.1 / Kotlin 2.3.20

### Notes for the Play Store listing

- `android:usesCleartextTraffic="true"` is kept for local HTTP backends during
  development; release builds use the HTTPS production backend by default.
- The backend is live at `https://kisanai-os.onrender.com`.

## Login

Create a user against the backend first (admin is bootstrapped from `.env`;
additional users via `POST /api/auth/register`), then log in on the app. The
access token is stored with `flutter_secure_storage` (Android Keystore) and
expired sessions return the user to the login screen.

## Current AI model limitation

The diagnosis, prediction and recommendation screens talk to real backend
endpoints, but no trained ML model is bundled with the backend yet:

- **Disease diagnosis** returns the controlled `MODEL_NOT_CONFIGURED` status —
  the app shows the backend message instead of fabricating a diagnosis. It is
  never presented as "healthy" or a real disease result.
- **Recommendations** return either `MODEL_NOT_CONFIGURED` (no model) or
  `INSUFFICIENT_DATA` (missing context, with the exact missing fields listed).
- **Predictions** return `MODEL_NOT_CONFIGURED` with `result`/`confidence`
  explicitly `null`.

These states are first-class in the app's models, tests, and UI. Wiring a real
model later requires no mobile changes — the same endpoints will start
returning real results.

## Layout

```
lib/
├── main.dart                  # Entry point
├── app.dart                   # KisanApp, provider tree, auth gate
├── dependencies.dart          # Composition root (injectable for tests)
├── core/                      # config, network, storage, theme, widgets
├── models/                    # Backend schema mirrors (safe JSON parsing)
├── services/                  # HTTP clients per endpoint group
└── features/                  # auth, home, weather, crops, soils, farmers,
                               # diseases, diagnosis, recommendations, profile
```
