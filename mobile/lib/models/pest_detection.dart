import 'detection_result.dart';

/// Structured pest-detection response (`PestDetectionOut`).
///
/// Status values mirror the backend provider layer:
/// - `MODEL_NOT_CONFIGURED` — no model is bundled; never confused with
///   "no pest" or a real identification.
class PestDetectionResult implements DetectionResultModel {
  const PestDetectionResult({
    required this.success,
    required this.status,
    required this.crop,
    required this.pestName,
    required this.confidence,
    required this.model,
    required this.message,
  });

  static const String statusModelNotConfigured = 'MODEL_NOT_CONFIGURED';

  final bool success;
  final String status;
  final String? crop;
  final String? pestName;
  @override
  final double? confidence;
  final String? model;
  @override
  final String? message;

  @override
  bool get isModelNotConfigured => status == statusModelNotConfigured;

  factory PestDetectionResult.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return PestDetectionResult(
      success: map['success'] as bool? ?? true,
      status: map['status'] as String? ?? statusModelNotConfigured,
      crop: map['crop'] as String?,
      pestName: map['pest_name'] as String?,
      confidence: (map['confidence'] as num?)?.toDouble(),
      model: map['model'] as String?,
      message: map['message'] as String?,
    );
  }
}