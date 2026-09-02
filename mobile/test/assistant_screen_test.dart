import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/voice/voice_service.dart';
import 'package:kisanai/features/assistant/assistant_controller.dart';
import 'package:kisanai/features/assistant/assistant_screen.dart';
import 'package:kisanai/services/assistant_api.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';
import 'helpers/mock_voice_service.dart';

void main() {
  AssistantController build(FakeBackend backend) {
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    return AssistantController(AssistantApi(client));
  }

  Widget wrap(AssistantController controller) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AssistantController>.value(value: controller),
        ChangeNotifierProvider<VoiceService>.value(value: MockVoiceService()),
      ],
      child: const MaterialApp(home: AssistantScreen()),
    );
  }

  testWidgets('shows the intro and the suggestion chip', (tester) async {
    await tester.pumpWidget(wrap(build(FakeBackend())));

    expect(find.text('फसल सहायक'), findsOneWidget);
    expect(find.text('मेरी फसल के क्या हाल हैं?'), findsOneWidget);
    expect(find.byIcon(Icons.send), findsOneWidget);
  });

  testWidgets('sending a question shows the honest answer', (tester) async {
    await tester.pumpWidget(wrap(build(FakeBackend())));

    await tester.enterText(find.byType(TextField), 'मेरी फसल के क्या हाल हैं?');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.textContaining('फसल की जानकारी दर्ज करें'), findsOneWidget);
  });

  testWidgets('tapping the suggestion chip asks the default question',
      (tester) async {
    await tester.pumpWidget(wrap(build(FakeBackend())));

    await tester.tap(find.text('मेरी फसल के क्या हाल हैं?'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.textContaining('फसल की जानकारी दर्ज करें'), findsOneWidget);
  });

  testWidgets('sending an empty question does nothing', (tester) async {
    await tester.pumpWidget(wrap(build(FakeBackend())));

    await tester.tap(find.byIcon(Icons.send));
    await tester.pump();

    expect(find.textContaining('फसल की जानकारी दर्ज करें'), findsNothing);
  });
}