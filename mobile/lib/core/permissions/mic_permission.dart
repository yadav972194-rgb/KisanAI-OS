import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../constants/app_strings.dart';

/// Handles microphone permission request with a Hindi rationale dialog.
///
/// Returns true if permission is granted, false otherwise.
Future<bool> requestMicPermission(BuildContext context) async {
  final SpeechToText speech = SpeechToText();
  bool hasPermission = await speech.hasPermission;

  if (hasPermission) return true;

  // Show rationale dialog before requesting
  final shouldRequest = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (context) => AlertDialog(
      title: const Text('माइक्रोफोन अनुमति'),
      content: const Text(
        'आवाज़ से सवाल पूछने के लिए माइक्रोफोन की अनुमति चाहिए। '
        'अनुमति देने पर आप हिंदी में बोलकर सवाल पूछ सकते हैं।',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text(AppStrings.cancel),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('अनुमति दें'),
        ),
      ],
    ),
  );

  if (shouldRequest != true) return false;

  // Initialize speech to trigger permission request
  await speech.initialize();
  return await speech.hasPermission;
}

/// Shows a SnackBar with the permission denied message in Hindi.
void showMicPermissionDeniedMessage(BuildContext context) {
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(
      content: Text('माइक्रोफोन अनुमति नहीं मिली। टेक्स्ट से सवाल पूछें।'),
      duration: Duration(seconds: 3),
    ),
  );
}