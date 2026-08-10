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
///   triggers [onUnauthorized] (used to end an expired session).
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

  /// Invoked when any request fails with HTTP 401.
  final void Function()? onUnauthorized;

  Future<Map<String, String>> _headers() async {
    final token = await tokenProvider?.call();
    return <String, String>{
      'Accept': 'application/json',
      if (token != null && token.isNotEmpty)
        'Authorization': 'Bearer $token',
    };
  }

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  /// GET expecting a JSON object (or a JSON array parsed as a list).
  Future<T> getJson<T>(String path, T Function(Object? json) parse) async {
    final response = await _perform(() async {
      final headers = await _headers();
      return _http.get(_uri(path), headers: headers).timeout(_timeout);
    });
    return parse(_decode(response));
  }

  /// POST with a JSON body.
  Future<T> postJson<T>(
    String path,
    Map<String, dynamic> body,
    T Function(Object? json) parse,
  ) async {
    final response = await _perform(() async {
      final headers = await _headers();
      headers['Content-Type'] = 'application/json';
      return _http
          .post(_uri(path), headers: headers, body: jsonEncode(body))
          .timeout(_timeout);
    });
    return parse(_decode(response));
  }

  /// POST with an application/x-www-form-urlencoded body (used by
  /// `POST /api/auth/token`).
  Future<T> postForm<T>(
    String path,
    Map<String, String> fields,
    T Function(Object? json) parse,
  ) async {
    final response = await _perform(() async {
      final headers = await _headers();
      return _http
          .post(_uri(path), headers: headers, body: fields)
          .timeout(_timeout);
    });
    return parse(_decode(response));
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
    final response = await _perform(() async {
      final request = http.MultipartRequest('POST', _uri(path));
      final headers = await _headers();
      request.headers.addAll(headers);
      request.fields.addAll(fields);
      request.files.add(
        http.MultipartFile.fromBytes(field, bytes, filename: filename),
      );
      // Route through the injected client so tests can intercept the request;
      // `MultipartRequest.send()` would bypass it with the default IOClient.
      final streamed = await _http.send(request).timeout(_timeout);
      return http.Response.fromStream(streamed).timeout(_timeout);
    });
    return parse(_decode(response));
  }

  Future<http.Response> _perform(
    Future<http.Response> Function() request,
  ) async {
    try {
      return await request();
    } on SocketException {
      throw const ApiException('', isNetwork: true);
    } on TimeoutException {
      throw const ApiException('', isNetwork: true);
    } on http.ClientException {
      throw const ApiException('', isNetwork: true);
    }
  }

  Object? _decode(http.Response response) {
    final Object? body = _tryDecode(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }
    if (response.statusCode == 401) {
      onUnauthorized?.call();
    }
    throw ApiException(
      _extractMessage(response.statusCode, body),
      statusCode: response.statusCode,
    );
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
