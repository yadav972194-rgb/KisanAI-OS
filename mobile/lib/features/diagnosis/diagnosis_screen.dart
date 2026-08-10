import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/common_views.dart';
import '../../models/disease_detection.dart';
import 'diagnosis_controller.dart';

/// Crop disease diagnosis via photo upload to the real backend.
class DiagnosisScreen extends StatefulWidget {
  const DiagnosisScreen({super.key});

  @override
  State<DiagnosisScreen> createState() => _DiagnosisScreenState();
}

class _DiagnosisScreenState extends State<DiagnosisScreen> {
  final _cropController = TextEditingController();

  @override
  void dispose() {
    _cropController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<DiagnosisController>();
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.diagnosisTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildImagePicker(context, controller),
          const SizedBox(height: 16),
          TextField(
            controller: _cropController,
            textInputAction: TextInputAction.done,
            decoration: const InputDecoration(
              labelText: AppStrings.cropHint,
              prefixIcon: Icon(Icons.grass),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: (controller.state == DiagnosisState.analyzing)
                ? null
                : () => _detect(context, controller),
            icon: const Icon(Icons.search),
            label: Text(controller.state == DiagnosisState.analyzing
                ? AppStrings.analyzing
                : AppStrings.detectButton),
          ),
          const SizedBox(height: 24),
          _buildResult(context, controller),
        ],
      ),
    );
  }

  Widget _buildImagePicker(BuildContext context, DiagnosisController controller) {
    final image = controller.selectedImage;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (image == null)
          OutlinedButton.icon(
            onPressed: controller.state == DiagnosisState.analyzing
                ? null
                : controller.selectImage,
            icon: const Icon(Icons.add_photo_alternate_outlined),
            label: const Text(AppStrings.pickImage),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size.fromHeight(120),
              side: BorderSide(color: Theme.of(context).colorScheme.primary),
            ),
          )
        else ...[
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.memory(
              Uint8List.fromList(image.bytes),
              height: 220,
              width: double.infinity,
              fit: BoxFit.cover,
              errorBuilder: (_, _, _) => const SizedBox(
                height: 220,
                child: Center(child: Icon(Icons.broken_image_outlined, size: 48)),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            image.name,
            style: Theme.of(context).textTheme.bodySmall,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          TextButton.icon(
            onPressed: controller.selectImage,
            icon: const Icon(Icons.swap_horiz),
            label: const Text(AppStrings.changeImage),
          ),
        ],
      ],
    );
  }

  Future<void> _detect(BuildContext context, DiagnosisController controller) async {
    FocusScope.of(context).unfocus();
    await controller.detect(cropName: _cropController.text);
  }

  Widget _buildResult(BuildContext context, DiagnosisController controller) {
    switch (controller.state) {
      case DiagnosisState.analyzing:
        return const LoadingView(label: AppStrings.analyzing);
      case DiagnosisState.error:
        return ErrorView(
          message: controller.errorMessage,
          onRetry: controller.selectedImage == null
              ? controller.selectImage
              : null,
        );
      case DiagnosisState.idle:
        return const SizedBox.shrink();
      case DiagnosisState.success:
        final result = controller.result;
        if (result == null) return const SizedBox.shrink();
        return _ResultCard(result: result);
    }
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});

  final DiseaseDetectionResult result;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (result.isModelNotConfigured) {
      return Card(
        color: const Color(0xFFFFF8E1),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              const Icon(Icons.info_outline, size: 40, color: Colors.orange),
              const SizedBox(height: 8),
              Text(
                AppStrings.modelNotConfigured,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                result.message?.isNotEmpty == true
                    ? result.message!
                    : AppStrings.modelNotConfiguredHint,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    final isHealthy = result.isHealthy;
    final color = isHealthy ? Colors.green : Colors.red;
    return Card(
      color: color.withValues(alpha: 0.08),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              AppStrings.resultHeading,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
                color: color,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(
                  isHealthy ? Icons.check_circle_outline : Icons.warning_amber,
                  size: 40,
                  color: color,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    isHealthy ? AppStrings.healthyCrop : result.diseaseName ?? '',
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: color,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            if (isHealthy) ...[
              const SizedBox(height: 4),
              Text(AppStrings.healthyCropHint),
            ] else if (result.confidence != null) ...[
              const SizedBox(height: 8),
              Text(
                '${AppStrings.confidenceLabel}: '
                '${(result.confidence! * 100).toStringAsFixed(0)}%',
              ),
            ],
            if (result.crop != null && result.crop!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text('फसल: ${result.crop}'),
            ],
          ],
        ),
      ),
    );
  }
}
