import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/constants/app_strings.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/errors/error_messages.dart';

void main() {
  group('errorMessageFor', () {
    test('network errors map to the connection message', () {
      const e = ApiException('', isNetwork: true, code: ApiErrorCode.network);
      expect(errorMessageFor(e), AppStrings.connectionError);
    });

    test('wrong credentials map to the invalid-credentials message', () {
      const e = ApiException('Invalid credentials',
          statusCode: 401, code: ApiErrorCode.authInvalid);
      expect(errorMessageFor(e), AppStrings.invalidCredentials);
    });

    test('session expiry/revocation map to the session message', () {
      const expired = ApiException('expired',
          statusCode: 401, code: ApiErrorCode.sessionExpired);
      const revoked = ApiException('revoked',
          statusCode: 401, code: ApiErrorCode.sessionRevoked);
      expect(errorMessageFor(expired), AppStrings.sessionExpired);
      expect(errorMessageFor(revoked), AppStrings.sessionExpired);
    });

    test('rate limiting maps to the too-many-attempts message', () {
      const e = ApiException('too many',
          statusCode: 429, code: ApiErrorCode.rateLimited);
      expect(errorMessageFor(e), AppStrings.tooManyAttempts);
    });

    test('server errors map to the server message', () {
      const e = ApiException('boom', statusCode: 500, code: ApiErrorCode.server);
      expect(errorMessageFor(e), AppStrings.serverError);
    });

    test('unknown codes fall back to the backend message', () {
      const e = ApiException('server rejected', statusCode: 500);
      expect(errorMessageFor(e), 'server rejected');
    });

    test('empty messages fall back to the generic string', () {
      const e = ApiException('', statusCode: 400);
      expect(errorMessageFor(e), AppStrings.genericError);
    });
  });
}
