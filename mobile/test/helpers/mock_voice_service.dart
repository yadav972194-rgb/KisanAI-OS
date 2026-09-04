import 'package:flutter/foundation.dart';
import 'package:kisanai/core/voice/voice_service.dart';

/// A mock VoiceService for testing that doesn't require platform channels.
class MockVoiceService extends ChangeNotifier implements VoiceService {
  MockVoiceService();

  bool _speechAvailable = true;
  bool _isListening = false;
  bool _isSpeaking = false;
  bool _isOnline = true;
  String? _lastError;

  void setSpeechAvailable(bool value) {
    _speechAvailable = value;
    notifyListeners();
  }

  void setOnline(bool value) {
    _isOnline = value;
    notifyListeners();
  }

  void setError(String? value) {
    _lastError = value;
    notifyListeners();
  }

  @override
  bool get isListening => _isListening;

  @override
  bool get isSpeaking => _isSpeaking;

  @override
  bool get speechAvailable => _speechAvailable;

  @override
  bool get isOnline => _isOnline;

  @override
  bool get isVoiceAvailable => _isOnline && _speechAvailable;

  @override
  String? get lastError => _lastError;

  @override
  Future<bool> initialize() async {
    _speechAvailable = true;
    notifyListeners();
    return true;
  }

  @override
  Future<bool> startListening({
    required void Function(String text, bool isFinal) onResult,
  }) async {
    if (!isVoiceAvailable) {
      _lastError = _isOnline
          ? 'Speech recognition not available'
          : 'No internet connection';
      notifyListeners();
      return false;
    }
    if (_isListening) return true;
    _isListening = true;
    notifyListeners();
    // Simulate a result after a short delay
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_isListening) {
        onResult('test voice input', true);
        _isListening = false;
        notifyListeners();
      }
    });
    return true;
  }

  @override
  Future<void> stopListening() async {
    if (!_isListening) return;
    _isListening = false;
    notifyListeners();
  }

  @override
  Future<bool> speak(String text) async {
    if (text.trim().isEmpty) return false;
    if (_isSpeaking) await stopSpeaking();
    _isSpeaking = true;
    notifyListeners();
    // Simulate completion
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_isSpeaking) {
        _isSpeaking = false;
        notifyListeners();
      }
    });
    return true;
  }

  @override
  Future<void> stopSpeaking() async {
    if (!_isSpeaking) return;
    _isSpeaking = false;
    notifyListeners();
  }

  @override
  Future<bool> isHindiSupported() async => true;
}