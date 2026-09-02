import 'package:flutter/material.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../../core/voice/voice_service.dart';

/// A microphone button that starts/stops speech-to-text listening.
///
/// Shows animated states for idle, listening, and processing.
/// Calls [onResult] with the recognized text when listening completes.
class VoiceInputButton extends StatefulWidget {
  const VoiceInputButton({
    super.key,
    required this.voiceService,
    required this.onResult,
    this.enabled = true,
  });

  final VoiceService voiceService;
  final void Function(String text) onResult;
  final bool enabled;

  @override
  State<VoiceInputButton> createState() => _VoiceInputButtonState();
}

class _VoiceInputButtonState extends State<VoiceInputButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnimation;
  String _partialText = '';

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.3).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    widget.voiceService.addListener(_onVoiceServiceChange);
  }

  @override
  void dispose() {
    widget.voiceService.removeListener(_onVoiceServiceChange);
    _pulseController.dispose();
    super.dispose();
  }

  void _onVoiceServiceChange() {
    if (mounted) setState(() {});
  }

  Future<void> _toggleListening() async {
    if (widget.voiceService.isListening) {
      await widget.voiceService.stopListening();
      if (_partialText.isNotEmpty) {
        widget.onResult(_partialText);
        _partialText = '';
      }
    } else {
      _partialText = '';
      final started = await widget.voiceService.startListening(
        onResult: (text, isFinal) {
          _partialText = text;
          if (isFinal && text.isNotEmpty) {
            widget.onResult(text);
            _partialText = '';
          }
        },
      );
      if (!started && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(widget.voiceService.lastError ?? AppStrings.genericError)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isListening = widget.voiceService.isListening;
    final color = isListening ? Colors.red : AppTheme.primaryGreen;

    return IconButton.filled(
      tooltip: isListening ? AppStrings.stopListening : AppStrings.startVoiceInput,
      onPressed: widget.enabled ? _toggleListening : null,
      style: IconButton.styleFrom(
        backgroundColor: color.withValues(alpha: 0.15),
        foregroundColor: color,
      ),
      icon: AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (context, child) {
          if (!isListening) return child!;
          return Transform.scale(
            scale: _pulseAnimation.value,
            child: child,
          );
        },
        child: Icon(isListening ? Icons.mic : Icons.mic_none, size: 28),
      ),
    );
  }
}