import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../models/pest_detection.dart';
import 'detection_screen.dart';
import 'pest_controller.dart';

/// Crop-pest identification via photo upload to `POST /api/pest/detect`.
class PestScreen extends StatelessWidget {
  const PestScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DetectionScreen<PestDetectionResult>(
      title: AppStrings.pestTitle,
      controllerOf: (context) => context.watch<PestController>(),
      labelOf: (result) => result.pestName ?? '',
    );
  }
}