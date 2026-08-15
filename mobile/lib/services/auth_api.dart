import '../../core/network/api_client.dart';
import '../../models/auth_models.dart';

/// Auth endpoints (`/api/auth/*`).
class AuthApi {
  AuthApi(this._client);

  final ApiClient _client;

  /// `POST /api/auth/token` — form-encoded credentials → bearer token.
  Future<AuthToken> login(String username, String password) {
    return _client.postForm(
      '/api/auth/token',
      {
        'grant_type': 'password',
        'username': username,
        'password': password,
      },
      AuthToken.fromJson,
    );
  }

  /// `POST /api/auth/register` — JSON user payload → created user.
  Future<AuthUser> register({
    required String username,
    required String password,
    String? fullName,
    String? mobile,
    String role = 'farmer',
  }) {
    return _client.postJson(
      '/api/auth/register',
      {
        'username': username,
        'password': password,
        'full_name': fullName,
        'mobile': mobile,
        'role': role,
      },
      AuthUser.fromJson,
    );
  }

  /// `POST /api/auth/register/otp` — register after mobile OTP verification.
  Future<AuthUser> registerWithOtp({
    required String mobile,
    required String code,
    required String username,
    required String password,
    String? fullName,
  }) {
    return _client.postJson(
      '/api/auth/register/otp',
      {
        'mobile': mobile,
        'code': code,
        'username': username,
        'password': password,
        'full_name': fullName,
      },
      AuthUser.fromJson,
    );
  }

  /// `POST /api/auth/otp/request` — request an OTP for a mobile + purpose.
  Future<OtpRequestResult> requestOtp({
    required String mobile,
    required String purpose,
  }) {
    return _client.postJson(
      '/api/auth/otp/request',
      {'mobile': mobile, 'purpose': purpose},
      OtpRequestResult.fromJson,
    );
  }

  /// `POST /api/auth/otp/verify` — verify an OTP code.
  Future<void> verifyOtp({
    required String mobile,
    required String purpose,
    required String code,
  }) {
    return _client.postJson(
      '/api/auth/otp/verify',
      {'mobile': mobile, 'purpose': purpose, 'code': code},
      (_) {},
    );
  }

  /// `POST /api/auth/forgot-username` — recover the username for a mobile.
  Future<String> forgotUsername({
    required String mobile,
    required String code,
  }) async {
    final username = await _client.postJson<Object?>(
      '/api/auth/forgot-username',
      {'mobile': mobile, 'code': code},
      (json) => json,
    );
    final map = username as Map<String, dynamic>? ?? const {};
    return map['username'] as String? ?? '';
  }

  /// `POST /api/auth/reset-password` — set a new password after OTP check.
  Future<void> resetPassword({
    required String mobile,
    required String code,
    required String newPassword,
  }) {
    return _client.postJson(
      '/api/auth/reset-password',
      {'mobile': mobile, 'code': code, 'new_password': newPassword},
      (_) {},
    );
  }

  /// `POST /api/auth/logout` — revoke the current session server-side.
  Future<void> logout() {
    return _client.postJson('/api/auth/logout', const {}, (_) {});
  }

  /// `GET /api/auth/me` — current user, requires a valid token.
  Future<AuthUser> me() {
    return _client.getJson('/api/auth/me', AuthUser.fromJson);
  }
}
