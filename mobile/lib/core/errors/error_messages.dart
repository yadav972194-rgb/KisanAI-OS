import '../constants/app_strings.dart';
import 'api_exception.dart';

/// Maps an [ApiException] to the correct user-facing Hindi message.
///
/// This is the single source of truth for error classification: real
/// transport failures become the network message, known backend codes get
/// their dedicated Hindi string, and anything else falls back to the
/// backend's own message (or a generic string when absent).
String errorMessageFor(ApiException e) {
  if (e.isNetwork) return AppStrings.connectionError;

  switch (e.code) {
    case ApiErrorCode.authInvalid:
      return AppStrings.invalidCredentials;
    case ApiErrorCode.sessionExpired:
    case ApiErrorCode.sessionRevoked:
      return AppStrings.sessionExpired;
    case ApiErrorCode.rateLimited:
      return AppStrings.tooManyAttempts;
    case ApiErrorCode.server:
      return AppStrings.serverError;
    case ApiErrorCode.notFound:
      return e.message.isNotEmpty
          ? e.message
          : AppStrings.accountNotFound;
    case ApiErrorCode.accountNotFound:
      return AppStrings.accountNotFound;
    case ApiErrorCode.conflict:
      return e.message.isNotEmpty
          ? e.message
          : AppStrings.duplicateAccount;
    case ApiErrorCode.modelNotConfigured:
    case ApiErrorCode.modelInvalid:
      return AppStrings.modelNotConfigured;
    default:
      return e.message.isNotEmpty ? e.message : AppStrings.genericError;
  }
}
