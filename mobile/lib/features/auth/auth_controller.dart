import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
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
  bool isRegistering = false;
  bool _isLoggingOut = false;

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
      errorMessage = errorMessageFor(e);
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

  /// Attempts registration; returns true on success. The caller returns the
  /// user to the login screen (no auto-login).
  Future<bool> register({
    required String username,
    required String password,
    String? fullName,
    String? mobile,
    String role = 'farmer',
  }) async {
    errorMessage = null;
    isRegistering = true;
    notifyListeners();
    try {
      await _api.register(
        username: username,
        password: password,
        fullName: fullName,
        mobile: mobile,
        role: role,
      );
      return true;
    } on ApiException catch (e) {
      if (e.isNetwork) {
        errorMessage = AppStrings.connectionError;
      } else if (e.statusCode == 409) {
        errorMessage = AppStrings.duplicateAccount;
      } else if (e.message.isNotEmpty) {
        errorMessage = e.message;
      } else {
        errorMessage = AppStrings.genericError;
      }
      return false;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      return false;
    } finally {
      isRegistering = false;
      notifyListeners();
    }
  }

  /// Ends the session and clears the stored token.
  ///
  /// Best-effort server-side revocation (POST /api/auth/logout) so the
  /// session ledger entry for this token is revoked and the token stops
  /// being valid. The local session is always cleared, even when the
  /// server call fails (offline / already-expired token). A re-entrancy
  /// guard prevents infinite recursion when the logout request itself
  /// bounces back a 401 (which would otherwise re-trigger `onUnauthorized`).
  ///
  /// The local token is only cleared if it still equals the token that was
  /// being logged out. If a *concurrent* login has since stored a fresh
  /// token, this logout must not wipe the new session.
  Future<void> logout() async {
    if (_isLoggingOut) return;
    _isLoggingOut = true;
    final revokedToken = await _storage.read();
    try {
      await _api.logout();
    } catch (_) {
      // Local logout must still succeed if revocation is impossible.
    } finally {
      if (await _storage.read() == revokedToken) {
        await _storage.clear();
        user = null;
        errorMessage = null;
        status = AuthStatus.unauthenticated;
      }
      _isLoggingOut = false;
      notifyListeners();
    }
  }
}
