import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../core/voice/voice_service.dart';
import '../../models/assistant.dart';
import '../../services/assistant_api.dart';

enum AssistantState { idle, loading, success, error }

/// Asks the assistant a natural-language question and holds the answer.
///
/// The backend classifies the intent (CROP_STATUS, WEATHER, ...) and
/// answers honestly from verified data or with a pointer; this controller
/// only surfaces that answer and classifies transport/API failures.
class AssistantController extends ChangeNotifier {
  AssistantController(this._api, {this.voiceService});

  final AssistantApi _api;
  final VoiceService? voiceService;

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

  /// Speaks the assistant's response message using TTS (Hindi).
  ///
  /// Does nothing if no voice service is configured or no response to speak.
  Future<void> speakResponse() async {
    if (voiceService == null) return;
    final message = response?.message;
    if (message == null || message.isEmpty) return;
    await voiceService!.speak(message);
  }

  /// Stops any ongoing TTS speech.
  Future<void> stopSpeaking() async {
    await voiceService?.stopSpeaking();
  }

  void clear() {
    state = AssistantState.idle;
    response = null;
    errorMessage = null;
    notifyListeners();
  }
}
