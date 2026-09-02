import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../models/water_stress.dart';
import 'detection_screen.dart';
import 'water_stress_controller.dart';

/// Crop water-stress identification via photo upload to
/// `POST /api/water-stress/detect`.
class WaterStressScreen extends StatelessWidget {
  const WaterStressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DetectionScreen<WaterStressResult>(
      title: AppStrings.waterStressTitle,
      controllerOf: (context) => context.watch<WaterStressController>(),
      labelOf: (result) => result.stressLevel ?? '',
    );
  }
}