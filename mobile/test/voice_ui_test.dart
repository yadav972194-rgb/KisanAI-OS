import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/permissions/mic_permission.dart';
import 'package:kisanai/core/voice/voice_service.dart';
import 'package:kisanai/features/assistant/assistant_controller.dart';
import 'package:kisanai/features/assistant/assistant_screen.dart';
import 'package:kisanai/services/assistant_api.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';
import 'helpers/mock_voice_service.dart';

void main() {
  MockVoiceService makeVoice() => MockVoiceService();

  AssistantController makeController(FakeBackend backend) {
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    return AssistantController(AssistantApi(client));
  }

  Widget wrap(AssistantController controller, VoiceService voice) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AssistantController>.value(value: controller),
        ChangeNotifierProvider<VoiceService>.value(value: voice),
      ],
      child: const MaterialApp(home: AssistantScreen()),
    );
  }

  Future<void> sendQuestion(WidgetTester tester) async {
    await tester.enterText(find.byType(TextField), 'मेरी फसल के क्या हाल हैं?');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
  }

  group('voice unavailable / offline fallback', () {
    testWidgets('offline shows mic-off state and text input stays usable',
        (tester) async {
      final voice = makeVoice();
      voice.setOnline(false);
      final controller = makeController(FakeBackend());

      await tester.pumpWidget(wrap(controller, voice));

      // Mic button is disabled and a mic-off fallback is shown.
      expect(find.byIcon(Icons.mic_off), findsOneWidget);
      final sendButton = tester.widget<IconButton>(find.ancestor(
        of: find.byIcon(Icons.send),
        matching: find.byType(IconButton),
      ));
      expect(sendButton.onPressed, isNotNull);

      // The user can still ask questions via text while offline.
      await sendQuestion(tester);
      expect(find.textContaining('फसल की जानकारी'), findsOneWidget);
    });

    testWidgets('startListening returns false when offline', (tester) async {
      final voice = makeVoice();
      voice.setOnline(false);
      final started = await voice.startListening(onResult: (_, _) {});
      expect(started, isFalse);
      expect(voice.isVoiceAvailable, isFalse);
    });
  });

  group('text-to-speech controls', () {
    testWidgets('play then stop toggles the TTS controls', (tester) async {
      final voice = makeVoice();
      final backend = FakeBackend();
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      final controller = AssistantController(AssistantApi(client),
          voiceService: voice);

      await tester.pumpWidget(wrap(controller, voice));
      await sendQuestion(tester);

      // Play button appears after a successful answer.
      expect(find.byIcon(Icons.play_arrow), findsOneWidget);

      // Tapping play speaks the response -> shows the stop button.
      await tester.tap(find.byIcon(Icons.play_arrow));
      await tester.pump();
      expect(find.byIcon(Icons.stop), findsOneWidget);
      expect(find.byIcon(Icons.play_arrow), findsNothing);

      // Tapping stop halts speech -> returns to the play button.
      await tester.tap(find.byIcon(Icons.stop));
      await tester.pump();
      expect(find.byIcon(Icons.play_arrow), findsOneWidget);
      expect(find.byIcon(Icons.stop), findsNothing);

      // Flush the mock's simulated-speech completion timer.
      await tester.pump(const Duration(milliseconds: 200));
    });
  });

  group('microphone permission fallback text', () {
    testWidgets('shows the Hindi permission-denied message', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(body: SizedBox()),
        ),
      );

      showMicPermissionDeniedMessage(tester.element(find.byType(Scaffold)));
      await tester.pump();

      expect(find.text('माइक्रोफोन अनुमति नहीं मिली। टेक्स्ट से सवाल पूछें।'),
          findsOneWidget);
    });
  });
}
