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
      {'username': username, 'password': password},
      AuthToken.fromJson,
    );
  }

  /// `GET /api/auth/me` — current user, requires a valid token.
  Future<AuthUser> me() {
    return _client.getJson('/api/auth/me', AuthUser.fromJson);
  }
}
