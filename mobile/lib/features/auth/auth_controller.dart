import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/storage/token_storage.dart';
import '../../models/auth_models.dart';
import '../../services/auth_api.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

/// Owns the login session: restore on startup, login, logout.
class AuthController extends ChangeNotifier {
  AuthController(this._api, this._storage);

  final AuthApi _api;
  final TokenStorage _storage;

  AuthStatus status = AuthStatus.unknown;
  AuthUser? user;
  String? errorMessage;
  bool isLoggingIn = false;

  /// Restores a previously saved session (called on splash screen).
  Future<void> restoreSession() async {
    final token = await _storage.read();
    if (token == null || token.isEmpty) {
      status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }
    try {
      user = await _api.me();
      status = AuthStatus.authenticated;
    } on ApiException catch (e) {
      if (e.isUnauthorized) {
        await _storage.clear();
      }
      status = AuthStatus.unauthenticated;
    } catch (_) {
      status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  /// Attempts login; returns true on success.
  Future<bool> login(String username, String password) async {
    errorMessage = null;
    isLoggingIn = true;
    notifyListeners();
    try {
      final token = await _api.login(username, password);
      await _storage.write(token.accessToken);
      user = await _api.me();
      status = AuthStatus.authenticated;
      return true;
    } on ApiException catch (e) {
      errorMessage =
          e.isNetwork ? AppStrings.connectionError : AppStrings.invalidCredentials;
      status = AuthStatus.unauthenticated;
      return false;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      status = AuthStatus.unauthenticated;
      return false;
    } finally {
      isLoggingIn = false;
      notifyListeners();
    }
  }

  /// Ends the session and clears the stored token.
  Future<void> logout() async {
    await _storage.clear();
    user = null;
    errorMessage = null;
    status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
