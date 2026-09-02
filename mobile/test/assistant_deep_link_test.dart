import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:kisanai/core/constants/app_strings.dart';
import 'package:kisanai/core/image/picked_image.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/voice/voice_service.dart';
import 'package:kisanai/features/assistant/assistant_controller.dart';
import 'package:kisanai/features/assistant/assistant_screen.dart';
import 'package:kisanai/features/detection/growth_stage_controller.dart';
import 'package:kisanai/features/detection/nutrient_deficiency_controller.dart';
import 'package:kisanai/features/detection/pest_controller.dart';
import 'package:kisanai/features/detection/water_stress_controller.dart';
import 'package:kisanai/features/detection/water_stress_screen.dart';
import 'package:kisanai/features/detection/weed_controller.dart';
import 'package:kisanai/features/diagnosis/diagnosis_controller.dart';
import 'package:kisanai/services/assistant_api.dart';
import 'package:kisanai/services/disease_detection_api.dart';
import 'package:kisanai/services/growth_stage_api.dart';
import 'package:kisanai/services/nutrient_deficiency_api.dart';
import 'package:kisanai/services/pest_detection_api.dart';
import 'package:kisanai/services/water_stress_api.dart';
import 'package:kisanai/services/weed_detection_api.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';
import 'helpers/mock_voice_service.dart';

void main() {
  Widget wrap(AssistantController assistant, {String intent = 'WATER_STRESS'}) {
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: _assistantClient(intent),
    );
    Future<PickedImage?> picker() async => null;
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AssistantController>.value(value: assistant),
        ChangeNotifierProvider<VoiceService>.value(value: MockVoiceService()),
        ChangeNotifierProvider<DiagnosisController>.value(
          value: DiagnosisController(DiseaseDetectionApi(client), picker),
        ),
        ChangeNotifierProvider<PestController>.value(
          value: PestController(PestDetectionApi(client), picker),
        ),
        ChangeNotifierProvider<WeedController>.value(
          value: WeedController(WeedDetectionApi(client), picker),
        ),
        ChangeNotifierProvider<NutrientDeficiencyController>.value(
          value: NutrientDeficiencyController(
              NutrientDeficiencyApi(client), picker),
        ),
        ChangeNotifierProvider<GrowthStageController>.value(
          value: GrowthStageController(GrowthStageApi(client), picker),
        ),
        ChangeNotifierProvider<WaterStressController>.value(
          value: WaterStressController(WaterStressApi(client), picker),
        ),
      ],
      child: const MaterialApp(home: AssistantScreen()),
    );
  }

  testWidgets('water-stress intent shows the deep-link chip', (tester) async {
    final assistant = AssistantController(
      AssistantApi(ApiClient(
        baseUrl: 'http://test.local',
        httpClient: _assistantClient('WATER_STRESS'),
      )),
    );
    await tester.pumpWidget(wrap(assistant));

    await tester.enterText(find.byType(TextField), 'जल तनाव पहचान');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text(AppStrings.openDetectionScreen), findsOneWidget);
  });

  testWidgets('tapping the deep-link chip opens the water-stress screen',
      (tester) async {
    final assistant = AssistantController(
      AssistantApi(ApiClient(
        baseUrl: 'http://test.local',
        httpClient: _assistantClient('WATER_STRESS'),
      )),
    );
    await tester.pumpWidget(wrap(assistant));

    await tester.enterText(find.byType(TextField), 'जल तनाव पहचान');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text(AppStrings.openDetectionScreen));
    await tester.pumpAndSettle();

    expect(find.byType(WaterStressScreen), findsOneWidget);
    expect(
      find.descendant(
        of: find.byType(AppBar),
        matching: find.text(AppStrings.waterStressTitle),
      ),
      findsOneWidget,
    );
  });

  testWidgets('unrelated intents do not show a deep-link chip',
      (tester) async {
    final assistant = AssistantController(
      AssistantApi(ApiClient(
        baseUrl: 'http://test.local',
        httpClient: _assistantClient('WEATHER'),
      )),
    );
    await tester.pumpWidget(wrap(assistant));

    await tester.enterText(find.byType(TextField), 'आज मौसम कैसा है?');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text(AppStrings.openDetectionScreen), findsNothing);
  });
}

MockClient _assistantClient(String intent) {
  return MockClient((request) async {
    if (request.url.path == '/api/assistant') {
      return jsonResponse({
        'intent': intent,
        'status': 'OK',
        'message': 'पहचान स्क्रीन खोलें।',
        'data': null,
      });
    }
    return jsonResponse({'message': 'not found'}, status: 404);
  });
}