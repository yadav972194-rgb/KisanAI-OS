import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../errors/api_exception.dart';

/// Thin HTTP wrapper around the KisanAI backend.
///
/// - Attaches the stored bearer token to every request.
/// - Applies a shared timeout.
/// - Converts transport failures into [ApiException] with
///   `isNetwork == true`.
/// - Converts non-2xx responses into [ApiException]; a 401 additionally
///   triggers [onUnauthorized] when an authenticated session is rejected
///   (used to end an expired session), but never for a failed login.
/// - Extracts the human-readable `message` from FastAPI error bodies
///   (`{"detail": {"success": false, "message": "..."}}` and
///   `{"success": false, "message": "..."}`).
class ApiClient {
  ApiClient({
    required this.baseUrl,
    http.Client? httpClient,
    this.tokenProvider,
    this.onUnauthorized,
    Duration? timeout,
  })  : _http = httpClient ?? http.Client(),
        _timeout = timeout ?? AppConfig.networkTimeout;

  final String baseUrl;
  final http.Client _http;
  final Duration _timeout;

  /// Supplies the current access token, if any.
  final Future<String?> Function()? tokenProvider;

  /// Invoked when the server rejects an *authenticated* request with HTTP
  /// 401, i.e. when a session the client believed to be valid is refused.
  ///
  /// It is deliberately NOT fired for a 401 from `POST /api/auth/token`
  /// (wrong credentials must not end the current session), nor when no
  /// session token was attached (there is nothing to end).
  final void Function()? onUnauthorized;

  /// Builds the headers for one request and also returns the exact token that
  /// was attached to it. Callers thread this token through to [_decode] so an
  /// expired-session (401) can be attributed to the session the request was
  /// made against — not to whatever token happens to be current by the time
  /// the response arrives.
  Future<({Map<String, String> headers, String? token})> _headers() async {
    final token = await tokenProvider?.call();
    return (
      headers: <String, String>{
        'Accept': 'application/json',
        if (token != null && token.isNotEmpty)
          'Authorization': 'Bearer $token',
      },
      token: token,
    );
  }

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  /// GET expecting a JSON object (or a JSON array parsed as a list).
  Future<T> getJson<T>(String path, T Function(Object? json) parse) async {
    final request = await _headers();
    final response = await _perform(() async {
      return _http.get(_uri(path), headers: request.headers).timeout(_timeout);
    });
    return parse(
      await _decode(response, path: path, requestToken: request.token),
    );
  }

  /// POST with a JSON body.
  Future<T> postJson<T>(
    String path,
    Map<String, dynamic> body,
    T Function(Object? json) parse,
  ) async {
    final request = await _headers();
    request.headers['Content-Type'] = 'application/json';
    final response = await _perform(() async {
      return _http
          .post(_uri(path), headers: request.headers, body: jsonEncode(body))
          .timeout(_timeout);
    });
    return parse(
      await _decode(response, path: path, requestToken: request.token),
    );
  }

  /// PUT with a JSON body.
  Future<T> putJson<T>(
    String path,
    Map<String, dynamic> body,
    T Function(Object? json) parse,
  ) async {
    final request = await _headers();
    request.headers['Content-Type'] = 'application/json';
    final response = await _perform(() async {
      return _http
          .put(_uri(path), headers: request.headers, body: jsonEncode(body))
          .timeout(_timeout);
    });
    return parse(
      await _decode(response, path: path, requestToken: request.token),
    );
  }

  /// DELETE expecting a JSON response body.
  Future<T> deleteJson<T>(
    String path,
    T Function(Object? json) parse,
  ) async {
    final request = await _headers();
    final response = await _perform(() async {
      return _http
          .delete(_uri(path), headers: request.headers)
          .timeout(_timeout);
    });
    return parse(
      await _decode(response, path: path, requestToken: request.token),
    );
  }

  /// POST with an application/x-www-form-urlencoded body (used by
  /// `POST /api/auth/token`).
  Future<T> postForm<T>(
    String path,
    Map<String, String> fields,
    T Function(Object? json) parse,
  ) async {
    final request = await _headers();
    final response = await _perform(() async {
      return _http
          .post(_uri(path), headers: request.headers, body: fields)
          .timeout(_timeout);
    });
    return parse(
      await _decode(response, path: path, requestToken: request.token),
    );
  }

  /// POST multipart/form-data (used by `POST /api/disease-detection`).
  Future<T> postMultipart<T>(
    String path, {
    required String field,
    required List<int> bytes,
    required String filename,
    Map<String, String> fields = const {},
    required T Function(Object? json) parse,
  }) async {
    final request = await _headers();
    final response = await _perform(() async {
      final httpRequest = http.MultipartRequest('POST', _uri(path));
      httpRequest.headers.addAll(request.headers);
      httpRequest.fields.addAll(fields);
      httpRequest.files.add(
        http.MultipartFile.fromBytes(field, bytes, filename: filename),
      );
      // Route through the injected client so tests can intercept the request;
      // `MultipartRequest.send()` would bypass it with the default IOClient.
      final streamed = await _http.send(httpRequest).timeout(_timeout);
      return http.Response.fromStream(streamed).timeout(_timeout);
    });
    return parse(
      await _decode(response, path: path, requestToken: request.token),
    );
  }

  Future<http.Response> _perform(
    Future<http.Response> Function() request,
  ) async {
    try {
      return await request();
    } on SocketException {
      throw const ApiException('', isNetwork: true, code: ApiErrorCode.network);
    } on TimeoutException {
      throw const ApiException('', isNetwork: true, code: ApiErrorCode.network);
    } on http.ClientException {
      throw const ApiException('', isNetwork: true, code: ApiErrorCode.network);
    }
  }

  Future<Object?> _decode(
    http.Response response, {
    required String path,
    required String? requestToken,
  }) async {
    final Object? body = _tryDecode(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }
    if (response.statusCode == 401 && path != '/api/auth/token') {
      // Fire only when the request that was rejected actually carried the
      // session that is still live *right now*. The token attached to THIS
      // request is authoritative: a stale in-flight request that was sent
      // with an older (already-revoked) token and only returns 401 after a
      // fresh login must NOT end the new session.
      //
      // - No token provider (standalone client): nothing to compare against,
      //   so fire.
      // - The request carried no token: there was no session to expire.
      // - The request carried a token different from the current one: the
      //   session it belonged to is already gone; this is a stale response.
      final liveToken = await tokenProvider?.call();
      final stillLive = requestToken != null &&
          requestToken.isNotEmpty &&
          requestToken == liveToken;
      final shouldNotify =
          tokenProvider == null || (requestToken != null && stillLive);
      if (shouldNotify) {
        onUnauthorized?.call();
      }
    }
    throw ApiException(
      _extractMessage(response.statusCode, body),
      statusCode: response.statusCode,
      code: _extractCode(body),
    );
  }

  /// Reads the stable backend error `code` from
  /// `{"code": "..."}` or `{"detail": {"code": "..."}}`.
  String? _extractCode(Object? body) {
    if (body is Map<String, dynamic>) {
      final direct = body['code'];
      if (direct is String && direct.isNotEmpty) return direct;
      final detail = body['detail'];
      if (detail is Map<String, dynamic>) {
        final detailCode = detail['code'];
        if (detailCode is String && detailCode.isNotEmpty) return detailCode;
      }
    }
    return null;
  }

  Object? _tryDecode(String text) {
    if (text.isEmpty) return null;
    try {
      return jsonDecode(text);
    } on FormatException {
      return null;
    }
  }

  String _extractMessage(int statusCode, Object? body) {
    if (body is Map<String, dynamic>) {
      final message = body['message'];
      if (message is String && message.isNotEmpty) return message;
      final detail = body['detail'];
      if (detail is String && detail.isNotEmpty) return detail;
      if (detail is Map<String, dynamic>) {
        final detailMessage = detail['message'];
        if (detailMessage is String && detailMessage.isNotEmpty) {
          return detailMessage;
        }
      }
    }
    return 'HTTP $statusCode';
  }
}
