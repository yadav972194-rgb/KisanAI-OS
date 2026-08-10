import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/storage/token_storage.dart';
import 'package:kisanai/features/auth/auth_controller.dart';
import 'package:kisanai/services/auth_api.dart';

import 'helpers/fake_backend.dart';

void main() {
  (AuthController, InMemoryTokenStorage) build(FakeBackend backend) {
    final storage = InMemoryTokenStorage();
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
      tokenProvider: storage.read,
    );
    return (AuthController(AuthApi(client), storage), storage);
  }

  // Backend where /api/auth/token works but /api/auth/me always returns 401.
  MockClient expiredSessionBackend() => MockClient((request) async {
        if (request.url.path == '/api/auth/token') {
          return http.Response(
            '{"access_token":"x","token_type":"bearer"}',
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response(
          '{"detail":{"success":false,"message":"not authenticated"}}',
          401,
          headers: {'content-type': 'application/json'},
        );
      });

  group('AuthController', () {
    test('starts unknown', () {
      final (controller, _) = build(FakeBackend());
      expect(controller.status, AuthStatus.unknown);
    });

    test('restoreSession without token -> unauthenticated', () async {
      final (controller, _) = build(FakeBackend());
      await controller.restoreSession();
      expect(controller.status, AuthStatus.unauthenticated);
      expect(controller.user, isNull);
    });

    test('restoreSession with valid token -> authenticated', () async {
      final (controller, storage) = build(FakeBackend());
      await storage.write('test-token');
      await controller.restoreSession();
      expect(controller.status, AuthStatus.authenticated);
      expect(controller.user!.username, 'ravi');
    });

    test('restoreSession with expired token -> unauthenticated + cleared',
        () async {
      final storage = InMemoryTokenStorage();
      await storage.write('expired-token');
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: expiredSessionBackend(),
        tokenProvider: storage.read,
      );
      final controller = AuthController(AuthApi(client), storage);
      await controller.restoreSession();
      expect(controller.status, AuthStatus.unauthenticated);
      expect(await storage.read(), isNull);
    });

    test('login success stores token and authenticates', () async {
      final (controller, storage) = build(FakeBackend());
      final ok = await controller.login('ravi', 'secret');
      expect(ok, isTrue);
      expect(controller.status, AuthStatus.authenticated);
      expect(controller.user!.username, 'ravi');
      expect(await storage.read(), 'test-token');
    });

    test('login failure sets error and stays unauthenticated', () async {
      final (controller, storage) = build(FakeBackend());
      final ok = await controller.login('ravi', 'wrong-password');
      expect(ok, isFalse);
      expect(controller.status, AuthStatus.unauthenticated);
      expect(controller.errorMessage, isNotEmpty);
      expect(await storage.read(), isNull);
    });

    test('login network failure surfaces connection error', () async {
      final (controller, _) = build(FakeBackend()..failLogin = true);
      final ok = await controller.login('ravi', 'secret');
      expect(ok, isFalse);
      expect(controller.status, AuthStatus.unauthenticated);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });

    test('logout clears token and session', () async {
      final (controller, storage) = build(FakeBackend());
      await controller.login('ravi', 'secret');
      await controller.logout();
      expect(controller.status, AuthStatus.unauthenticated);
      expect(controller.user, isNull);
      expect(await storage.read(), isNull);
    });
  });
}
