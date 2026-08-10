/// Errors thrown by the data layer.
///
/// `ApiException` is the single error type surfaced by [ApiClient]. It
/// distinguishes transient network problems from HTTP errors so UI layers
/// can show the right (Hindi) message and treat 401 as a session expiry.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.isNetwork = false});

  /// User-friendly message (may come from the backend error body).
  final String message;

  /// HTTP status code, when the failure came from a real HTTP response.
  final int? statusCode;

  /// True when the request never reached the server (no connection / timeout).
  final bool isNetwork;

  bool get isUnauthorized => statusCode == 401;

  @override
  String toString() => 'ApiException(statusCode: $statusCode, '
      'isNetwork: $isNetwork, message: $message)';
}
