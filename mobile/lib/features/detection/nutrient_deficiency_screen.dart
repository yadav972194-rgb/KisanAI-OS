import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../models/nutrient_deficiency.dart';
import 'detection_screen.dart';
import 'nutrient_deficiency_controller.dart';

/// Crop nutrient-deficiency identification via photo upload to
/// `POST /api/nutrient-deficiency/detect`.
class NutrientDeficiencyScreen extends StatelessWidget {
  const NutrientDeficiencyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DetectionScreen<NutrientDeficiencyResult>(
      title: AppStrings.nutrientTitle,
      controllerOf: (context) =>
          context.watch<NutrientDeficiencyController>(),
      labelOf: (result) => result.deficiencyName ?? '',
    );
  }
}