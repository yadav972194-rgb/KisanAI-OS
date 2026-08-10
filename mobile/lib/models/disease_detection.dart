/// Structured disease-detection response (`DiseaseDetectionOut`).
///
/// Status values mirror the backend provider layer:
/// - `HEALTHY` — no disease detected
/// - `DISEASE_DETECTED` — a disease was found
/// - `MODEL_NOT_CONFIGURED` — no model is bundled; never confused with
///   "healthy" or a real diagnosis.
class DiseaseDetectionResult {
  const DiseaseDetectionResult({
    required this.success,
    required this.status,
    required this.crop,
    required this.diseaseName,
    required this.confidence,
    required this.model,
    required this.message,
  });

  static const String statusHealthy = 'HEALTHY';
  static const String statusDiseaseDetected = 'DISEASE_DETECTED';
  static const String statusModelNotConfigured = 'MODEL_NOT_CONFIGURED';

  final bool success;
  final String status;
  final String? crop;
  final String? diseaseName;
  final double? confidence;
  final String? model;
  final String? message;

  bool get isHealthy => status == statusHealthy;
  bool get isDiseaseDetected => status == statusDiseaseDetected;
  bool get isModelNotConfigured => status == statusModelNotConfigured;

  factory DiseaseDetectionResult.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return DiseaseDetectionResult(
      success: map['success'] as bool? ?? true,
      status: map['status'] as String? ?? statusModelNotConfigured,
      crop: map['crop'] as String?,
      diseaseName: map['disease_name'] as String?,
      confidence: (map['confidence'] as num?)?.toDouble(),
      model: map['model'] as String?,
      message: map['message'] as String?,
    );
  }
}
