import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/auth/forgot_password_controller.dart';
import 'package:kisanai/services/auth_api.dart';

import 'helpers/fake_backend.dart';

void main() {
  ForgotPasswordController build(FakeBackend backend) {
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    return ForgotPasswordController(AuthApi(client));
  }

  group('ForgotPasswordController', () {
    test('starts in the enter-mobile step', () {
      final controller = build(FakeBackend());
      expect(controller.step, ForgotPasswordStep.enterMobile);
      expect(controller.errorMessage, isNull);
    });

    test('requesting an OTP moves to the reset step and surfaces dev_otp',
        () async {
      final controller = build(FakeBackend());
      final ok = await controller.requestOtp('9876543210');
      expect(ok, isTrue);
      expect(controller.step, ForgotPasswordStep.resetting);
      expect(controller.mobile, '9876543210');
      expect(controller.infoMessage, contains('123456'));
      expect(controller.errorMessage, isNull);
    });

    test('requesting an OTP on a network failure shows the connection error',
        () async {
      final controller = build(FakeBackend()..failLogin = true);
      final ok = await controller.requestOtp('9876543210');
      expect(ok, isFalse);
      expect(controller.step, ForgotPasswordStep.enterMobile);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });

    test('resetting the password reaches the done step', () async {
      final controller = build(FakeBackend());
      await controller.requestOtp('9876543210');
      final ok = await controller.resetPassword(
        code: '123456',
        newPassword: 'newpass123',
      );
      expect(ok, isTrue);
      expect(controller.step, ForgotPasswordStep.done);
    });

    test('a failed reset stays on the reset step with an error', () async {
      // OTP request succeeds; reset-password fails with a connection error.
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: MockClient((request) async {
          if (request.url.path == '/api/auth/reset-password') {
            throw http.ClientException('connection refused');
          }
          if (request.url.path == '/api/auth/otp/request') {
            return jsonResponse({
              'success': true,
              'message': 'OTP sent successfully (development mock)',
              'ttl_seconds': 300,
              'dev_otp': '123456',
            });
          }
          return jsonResponse({'message': 'not found'}, status: 404);
        }),
      );
      final controller = ForgotPasswordController(AuthApi(client));
      await controller.requestOtp('9876543210');
      expect(controller.step, ForgotPasswordStep.resetting);

      final ok = await controller.resetPassword(
        code: '123456',
        newPassword: 'newpass123',
      );
      expect(ok, isFalse);
      expect(controller.step, ForgotPasswordStep.resetting);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });
  });
}