import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../models/weed_detection.dart';
import 'detection_screen.dart';
import 'weed_controller.dart';

/// Crop-weed identification via photo upload to `POST /api/weed/detect`.
class WeedScreen extends StatelessWidget {
  const WeedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DetectionScreen<WeedDetectionResult>(
      title: AppStrings.weedTitle,
      controllerOf: (context) => context.watch<WeedController>(),
      labelOf: (result) => result.weedName ?? '',
    );
  }
}