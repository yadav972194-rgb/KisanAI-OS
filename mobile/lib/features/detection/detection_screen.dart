import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/common_views.dart';
import '../../models/detection_result.dart';
import 'detection_controller.dart';

/// Reusable crop-photo detection screen for the crop-health suite.
///
/// Generic over the concrete detector result: pick → preview → detect →
/// result. Layout mirrors the disease-diagnosis screen while the state
/// machine lives in [DetectionController]; only the title, controller
/// lookup and result label differ per detector.
class DetectionScreen<R extends DetectionResultModel> extends StatefulWidget {
  const DetectionScreen({
    super.key,
    required this.title,
    required this.controllerOf,
    required this.labelOf,
  });

  final String title;

  /// Resolves the concrete detector controller from the widget tree.
  final DetectionController<R> Function(BuildContext context) controllerOf;

  /// Maps a successful result to the detector-specific display label
  /// (e.g. ``pest_name`` → कीट).
  final String Function(R result) labelOf;

  @override
  State<DetectionScreen<R>> createState() => _DetectionScreenState<R>();
}

class _DetectionScreenState<R extends DetectionResultModel>
    extends State<DetectionScreen<R>> {
  final _cropController = TextEditingController();

  @override
  void dispose() {
    _cropController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controllerOf(context);
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
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
            onPressed: (controller.state == DetectionState.analyzing)
                ? null
                : () => _detect(context, controller),
            icon: const Icon(Icons.search),
            label: Text(controller.state == DetectionState.analyzing
                ? AppStrings.analyzing
                : AppStrings.detectButton),
          ),
          const SizedBox(height: 24),
          _buildResult(context, controller),
        ],
      ),
    );
  }

  Widget _buildImagePicker(
      BuildContext context, DetectionController<R> controller) {
    final image = controller.selectedImage;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (image == null)
          OutlinedButton.icon(
            onPressed: controller.state == DetectionState.analyzing
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

  Future<void> _detect(
      BuildContext context, DetectionController<R> controller) async {
    FocusScope.of(context).unfocus();
    await controller.detect(cropName: _cropController.text);
  }

  Widget _buildResult(BuildContext context, DetectionController<R> controller) {
    switch (controller.state) {
      case DetectionState.analyzing:
        return const LoadingView(label: AppStrings.analyzing);
      case DetectionState.error:
        return ErrorView(
          message: controller.errorMessage,
          onRetry: controller.selectedImage == null
              ? controller.selectImage
              : null,
        );
      case DetectionState.idle:
        return const SizedBox.shrink();
      case DetectionState.success:
        final result = controller.result;
        if (result == null) return const SizedBox.shrink();
        return _ResultCard(result: result, labelOf: widget.labelOf);
    }
  }
}

class _ResultCard<R extends DetectionResultModel> extends StatelessWidget {
  const _ResultCard({required this.result, required this.labelOf});

  final R result;
  final String Function(R result) labelOf;

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

    final label = labelOf(result);
    final hasLabel = label.isNotEmpty;
    final color = Colors.green;
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
                  hasLabel
                      ? Icons.check_circle_outline
                      : Icons.warning_amber,
                  size: 40,
                  color: color,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    hasLabel ? label : AppStrings.healthyCrop,
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: color,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            if (hasLabel)
              const SizedBox(height: 4)
            else
              Text(AppStrings.healthyCropHint),
            if (result.confidence != null) ...[
              const SizedBox(height: 8),
              Text(
                '${AppStrings.confidenceLabel}: '
                '${(result.confidence! * 100).toStringAsFixed(0)}%',
              ),
            ],
            if (result.message != null && result.message!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(result.message!),
            ],
          ],
        ),
      ),
    );
  }
}