/// Stable, machine-readable error codes shared between the KisanAI backend
/// (``{"success": false, "message": "...", "code": "..."}``) and the app.
class ApiErrorCode {
  ApiErrorCode._();

  /// Request never reached the server (no connection / timeout).
  static const String network = 'NETWORK_ERROR';

  /// Credentials were rejected (login / OTP).
  static const String authInvalid = 'AUTH_INVALID';

  /// The session token has expired and can no longer be used.
  static const String sessionExpired = 'SESSION_EXPIRED';

  /// The session was revoked server-side (e.g. logout elsewhere).
  static const String sessionRevoked = 'SESSION_REVOKED';

  /// The server failed while fulfilling the request.
  static const String server = 'SERVER_ERROR';

  /// The requested resource does not exist.
  static const String notFound = 'NOT_FOUND';

  /// No account exists for the given mobile (forgot-password flows).
  static const String accountNotFound = 'ACCOUNT_NOT_FOUND';

  /// A resource already exists (duplicate account / farm / crop).
  static const String conflict = 'CONFLICT';

  /// Request validation failed.
  static const String validation = 'VALIDATION_ERROR';

  /// No disease/prediction model is configured.
  static const String modelNotConfigured = 'MODEL_NOT_CONFIGURED';

  /// A model exists but is invalid or failed at inference time.
  static const String modelInvalid = 'MODEL_INVALID';

  /// Too many attempts; the request is rate limited.
  static const String rateLimited = 'RATE_LIMITED';
}

/// Errors thrown by the data layer.
///
/// `ApiException` is the single error type surfaced by [ApiClient]. It
/// distinguishes transient network problems from HTTP errors, carries the
/// backend's stable [code], and flags 401 so UI layers can treat it as a
/// session expiry.
class ApiException implements Exception {
  const ApiException(
    this.message, {
    this.statusCode,
    this.isNetwork = false,
    this.code,
  });

  /// User-friendly message (may come from the backend error body).
  final String message;

  /// HTTP status code, when the failure came from a real HTTP response.
  final int? statusCode;

  /// True when the request never reached the server (no connection / timeout).
  final bool isNetwork;

  /// Stable backend error code (see [ApiErrorCode]); null when absent.
  final String? code;

  bool get isUnauthorized => statusCode == 401;

  bool get isSessionExpired =>
      code == ApiErrorCode.sessionExpired ||
      code == ApiErrorCode.sessionRevoked;

  @override
  String toString() => 'ApiException(statusCode: $statusCode, '
      'isNetwork: $isNetwork, code: $code, message: $message)';
}