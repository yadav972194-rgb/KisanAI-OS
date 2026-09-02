import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/constants/app_strings.dart';
import 'package:kisanai/core/image/picked_image.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/detection/growth_stage_controller.dart';
import 'package:kisanai/features/detection/nutrient_deficiency_controller.dart';
import 'package:kisanai/features/detection/pest_controller.dart';
import 'package:kisanai/features/detection/pest_screen.dart';
import 'package:kisanai/features/detection/water_stress_controller.dart';
import 'package:kisanai/features/detection/weed_controller.dart';
import 'package:kisanai/features/detection_hub/detection_hub_screen.dart';
import 'package:kisanai/features/diagnosis/diagnosis_controller.dart';
import 'package:kisanai/services/growth_stage_api.dart';
import 'package:kisanai/services/nutrient_deficiency_api.dart';
import 'package:kisanai/services/pest_detection_api.dart';
import 'package:kisanai/services/water_stress_api.dart';
import 'package:kisanai/services/weed_detection_api.dart';
import 'package:kisanai/services/disease_detection_api.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';

void main() {
  Widget wrap(Widget child) {
    final backend = FakeBackend();
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    Future<PickedImage?> picker() async => null;
    return MultiProvider(
      providers: [
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
      child: MaterialApp(home: child),
    );
  }

  testWidgets('hub renders all six detector tiles', (tester) async {
    tester.view.physicalSize = const Size(800, 1400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(wrap(const DetectionHubScreen()));

    expect(find.text(AppStrings.detectionHubTitle), findsOneWidget);
    expect(find.text(AppStrings.diagnosisTitle), findsOneWidget);
    expect(find.text(AppStrings.pestTitle), findsOneWidget);
    expect(find.text(AppStrings.weedTitle), findsOneWidget);
    expect(find.text(AppStrings.nutrientTitle), findsOneWidget);
    expect(find.text(AppStrings.growthStageTitle), findsOneWidget);
    expect(find.text(AppStrings.waterStressTitle), findsOneWidget);
  });

  testWidgets('tapping a pest tile opens the pest screen', (tester) async {
    await tester.pumpWidget(wrap(const DetectionHubScreen()));

    await tester.tap(find.text(AppStrings.pestTitle));
    await tester.pumpAndSettle();

    expect(find.byType(PestScreen), findsOneWidget);
    expect(
      find.descendant(
        of: find.byType(AppBar),
        matching: find.text(AppStrings.pestTitle),
      ),
      findsOneWidget,
    );
  });
}