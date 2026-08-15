import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../models/assistant.dart';
import '../../services/assistant_api.dart';

enum AssistantState { idle, loading, success, error }

/// Asks the assistant a natural-language question and holds the answer.
///
/// The backend classifies the intent (CROP_STATUS, WEATHER, ...) and
/// answers honestly from verified data or with a pointer; this controller
/// only surfaces that answer and classifies transport/API failures.
class AssistantController extends ChangeNotifier {
  AssistantController(this._api);

  final AssistantApi _api;

  AssistantState state = AssistantState.idle;
  AssistantResponse? response;
  String? errorMessage;

  Future<void> ask(String text, {Map<String, dynamic>? soil}) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return;

    state = AssistantState.loading;
    errorMessage = null;
    response = null;
    notifyListeners();

    try {
      response = await _api.ask(trimmed, soil: soil);
      state = AssistantState.success;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = AssistantState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = AssistantState.error;
    }
    notifyListeners();
  }

  void clear() {
    state = AssistantState.idle;
    response = null;
    errorMessage = null;
    notifyListeners();
  }
}
