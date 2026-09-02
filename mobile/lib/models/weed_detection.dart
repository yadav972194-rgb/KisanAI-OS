import 'detection_result.dart';

/// Structured weed-detection response (`WeedDetectionOut`).
///
/// Status values mirror the backend provider layer:
/// - `MODEL_NOT_CONFIGURED` — no model is bundled; never confused with
///   "no weed" or a real identification.
class WeedDetectionResult implements DetectionResultModel {
  const WeedDetectionResult({
    required this.success,
    required this.status,
    required this.crop,
    required this.weedName,
    required this.confidence,
    required this.model,
    required this.message,
  });

  static const String statusModelNotConfigured = 'MODEL_NOT_CONFIGURED';

  final bool success;
  final String status;
  final String? crop;
  final String? weedName;
  @override
  final double? confidence;
  final String? model;
  @override
  final String? message;

  @override
  bool get isModelNotConfigured => status == statusModelNotConfigured;

  factory WeedDetectionResult.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return WeedDetectionResult(
      success: map['success'] as bool? ?? true,
      status: map['status'] as String? ?? statusModelNotConfigured,
      crop: map['crop'] as String?,
      weedName: map['weed_name'] as String?,
      confidence: (map['confidence'] as num?)?.toDouble(),
      model: map['model'] as String?,
      message: map['message'] as String?,
    );
  }
}