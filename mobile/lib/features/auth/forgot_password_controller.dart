import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../services/auth_api.dart';

/// Step of the forgot-password flow.
enum ForgotPasswordStep { enterMobile, resetting, done }

/// Drives password recovery: request an OTP for the mobile, then set a new
/// password. The OTP is verified server-side by the reset-password endpoint;
/// in development mock mode the backend returns the code in `dev_otp` so the
/// flow is testable without an SMS provider. It never fakes delivery.
class ForgotPasswordController extends ChangeNotifier {
  ForgotPasswordController(this._api);

  final AuthApi _api;

  ForgotPasswordStep step = ForgotPasswordStep.enterMobile;
  bool isLoading = false;
  String? errorMessage;
  String? infoMessage;
  String mobile = '';

  Future<bool> requestOtp(String mobile) async {
    errorMessage = null;
    infoMessage = null;
    isLoading = true;
    notifyListeners();
    try {
      final result = await _api.requestOtp(
        mobile: mobile.trim(),
        purpose: 'forgot_password',
      );
      this.mobile = mobile.trim();
      final devOtp = result.devOtp;
      if (devOtp != null && devOtp.isNotEmpty) {
        infoMessage = '${AppStrings.devOtpHint}: $devOtp';
      } else {
        infoMessage = AppStrings.otpSent;
      }
      step = ForgotPasswordStep.resetting;
      return true;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      return false;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      return false;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> resetPassword({
    required String code,
    required String newPassword,
  }) async {
    errorMessage = null;
    isLoading = true;
    notifyListeners();
    try {
      await _api.resetPassword(
        mobile: mobile,
        code: code.trim(),
        newPassword: newPassword,
      );
      step = ForgotPasswordStep.done;
      return true;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      return false;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      return false;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }
}