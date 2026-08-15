import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:kisanai/core/errors/api_exception.dart';
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
      onUnauthorized: () {},
    );
    return (AuthController(AuthApi(client), storage), storage);
  }

  // Issues a distinct token per login and delays the logout response so a
  // "stale" logout stays in flight while a new login completes.
  MockClient delayedLogoutBackend() {
    var tokenSeq = 0;
    return MockClient((request) async {
      final path = request.url.path;
      switch (path) {
        case '/api/auth/token':
          if (request.body.contains('password=secret')) {
            tokenSeq++;
            return jsonResponse({
              'access_token': 'token-$tokenSeq',
              'token_type': 'bearer',
            });
          }
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Invalid credentials'}},
            status: 401,
          );
        case '/api/auth/me':
          return jsonResponse(defaultUser);
        case '/api/auth/logout':
          await Future<void>.delayed(const Duration(milliseconds: 50));
          return jsonResponse({'success': true, 'message': 'Logged out'});
        default:
          return jsonResponse({'message': 'not found'}, status: 404);
      }
    });
  }

  group('login-after-logout regression', () {
    test('login -> logout -> login with the same account succeeds', () async {
      final (controller, storage) = build(FakeBackend());
      expect(await controller.login('ravi', 'secret'), isTrue);

      await controller.logout();
      expect(controller.status, AuthStatus.unauthenticated);
      expect(await storage.read(), isNull);

      final ok = await controller.login('ravi', 'secret');
      expect(ok, isTrue);
      expect(controller.status, AuthStatus.authenticated);
      expect(controller.user!.username, 'ravi');
      expect(await storage.read(), 'test-token');
    });

    test('a failed login must NOT trigger server-side logout side effects',
        () async {
      final backend = FakeBackend();
      backend.logoutCalls = 0;
      final storage = InMemoryTokenStorage();
      // Leftover token from a previously failed session restore.
      await storage.write('stale-token');
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
        tokenProvider: storage.read,
        onUnauthorized: () {},
      );
      final controller = AuthController(AuthApi(client), storage);

      final ok = await controller.login('ravi', 'wrong-password');
      expect(ok, isFalse);
      expect(controller.status, AuthStatus.unauthenticated);
      // Wrong credentials are NOT an expired-session signal.
      expect(backend.logoutCalls, 0);
      expect(await storage.read(), 'stale-token');
    });

    test(
        'a stale in-flight logout must not wipe a fresh concurrent login',
        () async {
      final storage = InMemoryTokenStorage();
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: delayedLogoutBackend(),
        tokenProvider: storage.read,
        onUnauthorized: () {},
      );
      final controller = AuthController(AuthApi(client), storage);

      await controller.login('ravi', 'secret');
      expect(await storage.read(), 'token-1');

      final logoutFuture = controller.logout();
      final ok = await controller.login('ravi', 'secret');
      expect(ok, isTrue);
      expect(controller.status, AuthStatus.authenticated);

      await logoutFuture;
      // The stale logout finished AFTER the new token was stored.
      expect(controller.status, AuthStatus.authenticated);
      expect(await storage.read(), 'token-2');
    });

    test('logout clears the local session when it still owns the token',
        () async {
      final (controller, storage) = build(FakeBackend());
      await controller.login('ravi', 'secret');
      expect(await storage.read(), 'test-token');

      await controller.logout();
      expect(controller.status, AuthStatus.unauthenticated);
      expect(await storage.read(), isNull);
    });

    test(
        'a stale 401 from an old session must not revoke a fresh login',
        () async {
      final storage = InMemoryTokenStorage();
      var tokenSeq = 0;
      var logoutCalls = 0;
      late final AuthController controller;
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: MockClient((request) async {
          final path = request.url.path;
          switch (path) {
            case '/api/auth/token':
              tokenSeq++;
              return jsonResponse({
                'access_token': 'token-$tokenSeq',
                'token_type': 'bearer',
              });
            case '/api/auth/me':
              return jsonResponse(defaultUser);
            case '/api/auth/logout':
              logoutCalls++;
              return jsonResponse({'success': true, 'message': 'Logged out'});
            case '/api/weather':
              // A slow endpoint that finally rejects the *old* token with
              // 401 — after the user has already logged back in.
              await Future<void>.delayed(const Duration(milliseconds: 50));
              return jsonResponse(
                {
                  'detail': {
                    'success': false,
                    'message': 'not authenticated',
                    'code': 'AUTH_INVALID',
                  },
                },
                status: 401,
              );
            default:
              return jsonResponse({'message': 'not found'}, status: 404);
          }
        }),
        tokenProvider: storage.read,
        // Production wiring (see AppDependencies): an expired session ends
        // the session via logout().
        onUnauthorized: () => controller.logout(),
      );
      controller = AuthController(AuthApi(client), storage);

      await controller.login('ravi', 'secret');
      expect(await storage.read(), 'token-1');

      // In-flight request from the OLD session (carries token-1). Its 401
      // response is delayed so it lands AFTER the fresh login below.
      final staleRequest = client.getJson('/api/weather', (json) => json);

      await controller.logout();
      expect(await storage.read(), isNull);

      final ok = await controller.login('ravi', 'secret');
      expect(ok, isTrue);
      expect(controller.status, AuthStatus.authenticated);
      expect(await storage.read(), 'token-2');

      // The stale 401 now lands. It must NOT end the fresh session.
      await expectLater(
        staleRequest,
        throwsA(isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)),
      );
      expect(controller.status, AuthStatus.authenticated);
      expect(await storage.read(), 'token-2');
      expect(logoutCalls, 1);
    });
  });
}
