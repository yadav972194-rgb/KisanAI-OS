import 'package:flutter/material.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../../core/voice/voice_service.dart';

/// Play/Stop controls for Text-to-Speech playback.
///
/// Shows a play button when idle/stopped, stop button when speaking.
class TtsControls extends StatelessWidget {
  const TtsControls({
    super.key,
    required this.voiceService,
    this.onPlay,
    this.onStop,
  });

  final VoiceService voiceService;
  final VoidCallback? onPlay;
  final VoidCallback? onStop;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: voiceService,
      builder: (context, _) {
        final isSpeaking = voiceService.isSpeaking;
        if (!isSpeaking && onPlay == null) return const SizedBox.shrink();

        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (!isSpeaking && onPlay != null)
              IconButton.outlined(
                tooltip: AppStrings.playVoice,
                onPressed: onPlay,
                icon: const Icon(Icons.play_arrow),
                style: IconButton.styleFrom(foregroundColor: AppTheme.primaryGreen),
              ),
            if (isSpeaking)
              IconButton.filled(
                tooltip: AppStrings.stopVoice,
                onPressed: onStop,
                icon: const Icon(Icons.stop),
              ),
          ],
        );
      },
    );
  }
}