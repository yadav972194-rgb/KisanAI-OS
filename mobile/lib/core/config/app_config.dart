import 'package:flutter/foundation.dart';

/// App-wide configuration for KisanAI mobile.
///
/// No secrets are stored here. The only user-editable value is the backend
/// base URL, overridden at build time when needed, e.g.:
///
/// ```sh
/// flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
/// flutter build apk --dart-define=API_BASE_URL=https://api.example.com
/// ```
///
/// Resolution rules ([resolveApiBaseUrl]):
/// - A **release** build can never resolve to a loopback/localhost URL. Any
///   explicit override that points at the phone itself (`127.0.0.1`,
///   `localhost`, emulator alias `10.0.2.2`) is rejected and falls back to
///   the production backend, so a physical-device APK never silently targets
///   itself. Non-loopback overrides (e.g. a staging domain) are honored.
/// - A **debug/profile** build honors an explicit override (loopback allowed)
///   and otherwise defaults to production. Local development therefore always
///   requires an explicit selection.
class AppConfig {
  AppConfig._();

  static const String appName = 'KisanAI';

  /// Deployed production backend.
  static const String productionApiBaseUrl = 'https://kisanai-os.onrender.com';

  /// Local-development backend (explicitly selected only).
  static const String localApiBaseUrl = 'http://127.0.0.1:8712';

  /// Build-time override supplied via `--dart-define=API_BASE_URL=...`.
  static const String apiBaseUrlOverride = String.fromEnvironment(
    'API_BASE_URL',
  );

  /// Pure URL-selection logic.
  ///
  /// [isRelease] mirrors `kReleaseMode`; [override] mirrors the
  /// `--dart-define` value. Exposed for tests so both branches are verifiable
  /// deterministically.
  static String resolveApiBaseUrl({
    required bool isRelease,
    String override = '',
  }) {
    final trimmed = override.trim();
    if (isRelease) {
      if (trimmed.isEmpty || _isLoopback(trimmed)) return productionApiBaseUrl;
      return trimmed;
    }
    return trimmed.isNotEmpty ? trimmed : productionApiBaseUrl;
  }

  /// Backend base URL for the current build.
  static String get apiBaseUrl =>
      resolveApiBaseUrl(isRelease: kReleaseMode, override: apiBaseUrlOverride);

  static bool _isLoopback(String url) {
    final lower = url.trim().toLowerCase();
    final String host;
    if (lower.contains('://')) {
      host = Uri.tryParse(lower)?.host ?? lower;
    } else {
      host = lower.split(RegExp(r'[/:]')).first;
    }
    return const {
      '127.0.0.1',
      'localhost',
      '0.0.0.0',
      '::1',
      '10.0.2.2',
    }.contains(host);
  }

  /// Shared request/response timeout for all network calls.
  static const Duration networkTimeout = Duration(seconds: 25);
}