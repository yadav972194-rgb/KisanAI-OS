import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/network/api_client.dart';

import 'helpers/fake_backend.dart';

void main() {
  ApiClient clientFor(MockClient mock, {void Function()? onUnauthorized}) {
    return ApiClient(
      baseUrl: 'http://test.local',
      httpClient: mock,
      onUnauthorized: onUnauthorized,
      timeout: const Duration(seconds: 5),
    );
  }

  group('ApiClient', () {
    test('attaches bearer token when a token provider is set', () async {
      String? seenAuth;
      final mock = MockClient((request) async {
        seenAuth = request.headers['Authorization'];
        return jsonResponse(const {'ok': true});
      });
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: mock,
        tokenProvider: () async => 'secret-token',
      );
      await client.getJson('/api/auth/me', (json) => json);
      expect(seenAuth, 'Bearer secret-token');
    });

    test('omits Authorization header without a token', () async {
      String? seenAuth = 'unset';
      final mock = MockClient((request) async {
        seenAuth = request.headers['Authorization'];
        return jsonResponse(const {'ok': true});
      });
      final client = clientFor(mock);
      await client.getJson('/api/auth/me', (json) => json);
      expect(seenAuth, isNull);
    });

    test('getJson parses object responses', () async {
      final client = clientFor(FakeBackend().client());
      final body = await client.getJson('/api/weather', (json) => json);
      expect((body as Map)['location'], 'Delhi');
    });

    test('getJson parses array responses via parse fn', () async {
      final mock = MockClient(
        (_) async => jsonResponse(const [
          {'crop_id': 1, 'crop_name': 'गेहूँ'},
        ]),
      );
      final client = clientFor(mock);
      final list = await client.getJson('/api/crops', (json) => json as List);
      expect(list, hasLength(1));
    });

    test('postForm sends form-encoded body', () async {
      String? contentType;
      String? body;
      final mock = MockClient((request) async {
        contentType = request.headers['Content-Type'];
        body = request.body;
        return jsonResponse(const {'access_token': 't'});
      });
      final client = clientFor(mock);
      await client.postForm(
        '/api/auth/token',
        {'username': 'ravi', 'password': 'pass'},
        (json) => json,
      );
      expect(contentType, 'application/x-www-form-urlencoded');
      expect(body, contains('username=ravi'));
      expect(body, contains('password=pass'));
    });

    test('postJson sends a JSON body', () async {
      String? contentType;
      String? body;
      final mock = MockClient((request) async {
        contentType = request.headers['Content-Type'];
        body = request.body;
        return jsonResponse(const {'ok': true});
      });
      final client = clientFor(mock);
      await client.postJson(
        '/api/recommendations',
        {'crop_name': 'गेहूँ'},
        (json) => json,
      );
      expect(contentType, 'application/json');
      expect(jsonDecode(body!), {'crop_name': 'गेहूँ'});
    });

    test('postMultipart includes file part and optional fields', () async {
      String? contentType;
      String? body;
      final mock = MockClient((request) async {
        contentType = request.headers['Content-Type'];
        body = request.body;
        return jsonResponse(const {'status': 'MODEL_NOT_CONFIGURED'});
      });
      final client = clientFor(mock);
      await client.postMultipart(
        '/api/disease-detection',
        field: 'file',
        bytes: [1, 2, 3],
        filename: 'leaf.jpg',
        fields: {'crop_name': 'गेहूँ'},
        parse: (json) => json,
      );
      expect(contentType, contains('multipart/form-data'));
      expect(body, contains('name="file"'));
      expect(body, contains('leaf.jpg'));
      expect(body, contains('crop_name'));
    });

    test('non-2xx with FastAPI detail body surfaces message', () async {
      final mock = MockClient((_) async => jsonResponse(
            {'detail': {'success': false, 'message': 'Invalid credentials'}},
            status: 401,
          ));
      final client = clientFor(mock);
      await expectLater(
        client.getJson('/api/auth/me', (json) => json),
        throwsA(isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)
            .having((e) => e.message, 'message', 'Invalid credentials')
            .having((e) => e.isUnauthorized, 'isUnauthorized', isTrue)),
      );
    });

    test('non-2xx with flat error body surfaces message', () async {
      final mock = MockClient(
        (_) async => jsonResponse({'success': false, 'message': 'server down'}, status: 500),
      );
      final client = clientFor(mock);
      await expectLater(
        client.getJson('/api/weather', (json) => json),
        throwsA(isA<ApiException>()
            .having((e) => e.message, 'message', 'server down')
            .having((e) => e.isNetwork, 'isNetwork', false)),
      );
    });

    test('401 triggers onUnauthorized callback', () async {
      var notified = false;
      final mock = MockClient(
        (_) async => jsonResponse({'detail': {'message': 'no'}}, status: 401),
      );
      final client = clientFor(mock, onUnauthorized: () => notified = true);
      await expectLater(
        client.getJson('/api/auth/me', (json) => json),
        throwsA(isA<ApiException>()),
      );
      expect(notified, isTrue);
    });

    test('connection failure maps to a network ApiException', () async {
      final mock = MockClient(
        (_) async => throw http.ClientException('connection refused'),
      );
      final client = clientFor(mock);
      await expectLater(
        client.getJson('/api/weather', (json) => json),
        throwsA(isA<ApiException>().having((e) => e.isNetwork, 'isNetwork', true)),
      );
    });

    test('timeout maps to a network ApiException', () async {
      final mock = MockClient((_) async {
        await Future<void>.delayed(const Duration(milliseconds: 200));
        return jsonResponse(const {'ok': true});
      });
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: mock,
        timeout: const Duration(milliseconds: 20),
      );
      await expectLater(
        client.getJson('/api/weather', (json) => json),
        throwsA(isA<ApiException>().having((e) => e.isNetwork, 'isNetwork', true)),
      );
    });
  });
}
