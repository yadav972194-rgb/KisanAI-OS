/// App-wide configuration for KisanAI mobile.
///
/// No secrets are stored here. The only user-editable value is the backend
/// base URL, overridden at build time when needed, e.g.:
///
/// ```sh
/// flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
/// flutter build apk --dart-define=API_BASE_URL=https://api.example.com
/// ```
class AppConfig {
  AppConfig._();

  static const String appName = 'KisanAI';

  /// Backend base URL.
  ///
  /// Defaults to the Android emulator loopback alias, which resolves to the
  /// host machine where the FastAPI backend runs.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  /// Shared request/response timeout for all network calls.
  static const Duration networkTimeout = Duration(seconds: 25);
}
