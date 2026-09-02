import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../models/growth_stage.dart';
import 'detection_screen.dart';
import 'growth_stage_controller.dart';

/// Crop growth-stage identification via photo upload to
/// `POST /api/growth-stage/detect`.
class GrowthStageScreen extends StatelessWidget {
  const GrowthStageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DetectionScreen<GrowthStageResult>(
      title: AppStrings.growthStageTitle,
      controllerOf: (context) => context.watch<GrowthStageController>(),
      labelOf: (result) => result.growthStage ?? '',
    );
  }
}