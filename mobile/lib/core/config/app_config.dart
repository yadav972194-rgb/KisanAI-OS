/// App-wide configuration for KisanAI mobile.
///
/// No secrets are stored here. The only user-editable value is the backend
/// base URL, overridden at build time when needed, e.g.:
///
/// ```sh
/// flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
/// flutter build apk --dart-define=API_BASE_URL=https://api.example.com
/// ```
class AppConfig {
  AppConfig._();

  static const String appName = 'KisanAI';

  /// Backend base URL.
  ///
  /// Defaults to the production backend on Render. Local development against
  /// a machine-run backend can override it, e.g. with the Android emulator
  /// loopback alias `http://10.0.2.2:8000` or a LAN IP.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://kisanai-os.onrender.com',
  );

  /// Shared request/response timeout for all network calls.
  static const Duration networkTimeout = Duration(seconds: 25);
}
