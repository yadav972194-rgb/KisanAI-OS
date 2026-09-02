import 'detection_result.dart';

/// Structured crop-water-stress detection response (`WaterStressOut`).
///
/// Status values mirror the backend provider layer:
/// - `MODEL_NOT_CONFIGURED` — no model is bundled; never confused with
///   "no stress" or a real identification.
class WaterStressResult implements DetectionResultModel {
  const WaterStressResult({
    required this.success,
    required this.status,
    required this.crop,
    required this.stressLevel,
    required this.confidence,
    required this.model,
    required this.message,
  });

  static const String statusModelNotConfigured = 'MODEL_NOT_CONFIGURED';

  final bool success;
  final String status;
  final String? crop;
  final String? stressLevel;
  @override
  final double? confidence;
  final String? model;
  @override
  final String? message;

  @override
  bool get isModelNotConfigured => status == statusModelNotConfigured;

  factory WaterStressResult.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return WaterStressResult(
      success: map['success'] as bool? ?? true,
      status: map['status'] as String? ?? statusModelNotConfigured,
      crop: map['crop'] as String?,
      stressLevel: map['stress_level'] as String?,
      confidence: (map['confidence'] as num?)?.toDouble(),
      model: map['model'] as String?,
      message: map['message'] as String?,
    );
  }
}