import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// Service wrapping Speech-to-Text and Text-to-Speech for Hindi (hi-IN).
///
/// Provides a simple interface for the Assistant feature. All methods are
/// safe to call from the UI thread; errors are caught and surfaced via
/// callbacks or return values so the caller can show appropriate Hindi
/// messages.
class VoiceService extends ChangeNotifier {
  VoiceService();

  final SpeechToText _speech = SpeechToText();
  final FlutterTts _tts = FlutterTts();
  final Connectivity _connectivity = Connectivity();

  bool _speechAvailable = false;
  bool _isListening = false;
  bool _isSpeaking = false;
  bool _isOnline = true;
  String? _lastError;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;

  bool get isListening => _isListening;
  bool get isSpeaking => _isSpeaking;
  bool get speechAvailable => _speechAvailable;
  bool get isOnline => _isOnline;
  String? get lastError => _lastError;

  /// True when voice input is usable: the device is online and the STT engine
  /// initialized successfully. Used by the Assistant UI to enable/disable the
  /// microphone button and fall back to a textual mic-off state.
  bool get isVoiceAvailable => _isOnline && _speechAvailable;

  /// Initialize both STT and TTS engines.
  ///
  /// Returns true if both are available, false otherwise.
  /// Call this once on app startup (e.g., in [AppDependencies]).
  Future<bool> initialize() async {
    try {
      _speechAvailable = await _speech.initialize(
        onError: (error) {
          _lastError = error.errorMsg;
          _isListening = false;
          notifyListeners();
          if (kDebugMode) {
            debugPrint('STT error: ${error.errorMsg}');
          }
        },
        onStatus: (status) {
          if (status == 'done' || status == 'notListening') {
            _isListening = false;
            notifyListeners();
          }
        },
      );

      await _tts.setLanguage('hi-IN');
      await _tts.setSpeechRate(0.5);
      await _tts.setVolume(1.0);
      await _tts.setPitch(1.0);

      _tts.setStartHandler(() {
        _isSpeaking = true;
        notifyListeners();
      });

      _tts.setCompletionHandler(() {
        _isSpeaking = false;
        notifyListeners();
      });

      _tts.setErrorHandler((msg) {
        _lastError = msg;
        _isSpeaking = false;
        notifyListeners();
        if (kDebugMode) {
          debugPrint('TTS error: $msg');
        }
      });

      _setupConnectivityMonitoring();

      return _speechAvailable;
    } catch (e) {
      _lastError = e.toString();
      _speechAvailable = false;
      notifyListeners();
      return false;
    }
  }

  /// Watches connectivity changes so the voice UI can fall back to a disabled
  /// mic state when the device is offline/airplane mode. Fully defensive so a
  /// missing platform channel (e.g. in widget tests) never breaks startup.
  void _setupConnectivityMonitoring() {
    try {
      _connectivitySub =
          _connectivity.onConnectivityChanged.listen((results) {
        final online = !results.contains(ConnectivityResult.none);
        if (online != _isOnline) {
          _isOnline = online;
          notifyListeners();
        }
      });
    } catch (_) {
      _isOnline = true;
    }
  }

  /// Start listening for Hindi speech.
  ///
  /// [onResult] is called with the recognized text (partial or final).
  /// Returns true if listening started, false if unavailable or error.
  Future<bool> startListening({
    required void Function(String text, bool isFinal) onResult,
  }) async {
    if (!isVoiceAvailable) {
      _lastError = _isOnline
          ? 'Speech recognition not available'
          : 'No internet connection';
      return false;
    }
    if (_isListening) return true;

    try {
      _isListening = true;
      notifyListeners();
      // Using deprecated parameters as the new SpeechListenOptions API
      // has different parameter names in this version.
      // ignore: deprecated_member_use
      await _speech.listen(
        onResult: (result) {
          onResult(result.recognizedWords, result.finalResult);
        },
        localeId: 'hi-IN',
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
      );
      return true;
    } catch (e) {
      _isListening = false;
      _lastError = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Stop listening.
  Future<void> stopListening() async {
    if (!_isListening) return;
    try {
      await _speech.stop();
    } catch (_) {}
    _isListening = false;
    notifyListeners();
  }

  /// Speak the given Hindi text using TTS.
  ///
  /// Returns true if speech started, false if unavailable or error.
  Future<bool> speak(String text) async {
    if (text.trim().isEmpty) return false;
    if (_isSpeaking) {
      await stopSpeaking();
    }

    try {
      _isSpeaking = true;
      notifyListeners();
      final result = await _tts.speak(text);
      return result == 1;
    } catch (e) {
      _isSpeaking = false;
      _lastError = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Stop any ongoing TTS speech.
  Future<void> stopSpeaking() async {
    if (!_isSpeaking) return;
    try {
      await _tts.stop();
    } catch (_) {}
    _isSpeaking = false;
    notifyListeners();
  }

  /// Check if Hindi locale is supported for TTS.
  Future<bool> isHindiSupported() async {
    try {
      final languages = await _tts.getLanguages;
      return languages?.contains('hi-IN') ?? false;
    } catch (_) {
      return false;
    }
  }

  @override
  void dispose() {
    _connectivitySub?.cancel();
    _speech.cancel();
    _tts.stop();
    super.dispose();
  }
}