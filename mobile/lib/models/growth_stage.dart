import 'detection_result.dart';

/// Structured crop-growth-stage detection response (`GrowthStageOut`).
///
/// Status values mirror the backend provider layer:
/// - `MODEL_NOT_CONFIGURED` — no model is bundled; never confused with
///   "no stage" or a real identification.
class GrowthStageResult implements DetectionResultModel {
  const GrowthStageResult({
    required this.success,
    required this.status,
    required this.crop,
    required this.growthStage,
    required this.confidence,
    required this.model,
    required this.message,
  });

  static const String statusModelNotConfigured = 'MODEL_NOT_CONFIGURED';

  final bool success;
  final String status;
  final String? crop;
  final String? growthStage;
  @override
  final double? confidence;
  final String? model;
  @override
  final String? message;

  @override
  bool get isModelNotConfigured => status == statusModelNotConfigured;

  factory GrowthStageResult.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return GrowthStageResult(
      success: map['success'] as bool? ?? true,
      status: map['status'] as String? ?? statusModelNotConfigured,
      crop: map['crop'] as String?,
      growthStage: map['growth_stage'] as String?,
      confidence: (map['confidence'] as num?)?.toDouble(),
      model: map['model'] as String?,
      message: map['message'] as String?,
    );
  }
}