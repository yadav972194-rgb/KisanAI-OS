/// Recommendation request + response models (`RecommendationRequest`,
/// `RecommendationOut`).
library;

class RecommendationItem {
  const RecommendationItem({
    required this.category,
    required this.text,
    required this.reason,
    required this.source,
  });

  final String category;
  final String text;
  final String? reason;
  final String? source;

  factory RecommendationItem.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return RecommendationItem(
      category: map['category'] as String? ?? '',
      text: map['text'] as String? ?? '',
      reason: map['reason'] as String?,
      source: map['source'] as String?,
    );
  }
}

/// Input captured by the recommendation form. Null fields are omitted so the
/// backend engine reports exactly what context is missing.
class RecommendationInput {
  const RecommendationInput({
    this.cropName,
    this.ph,
    this.moisture,
    this.nitrogen,
    this.phosphorus,
    this.potassium,
    this.temperature,
    this.humidity,
    this.diseaseName,
    this.severity,
  });

  final String? cropName;
  final double? ph;
  final double? moisture;
  final int? nitrogen;
  final int? phosphorus;
  final int? potassium;
  final double? temperature;
  final int? humidity;
  final String? diseaseName;
  final String? severity;

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> soil = {
      if (ph != null) 'ph': ph,
      if (moisture != null) 'moisture': moisture,
      if (nitrogen != null) 'nitrogen': nitrogen,
      if (phosphorus != null) 'phosphorus': phosphorus,
      if (potassium != null) 'potassium': potassium,
    };
    final Map<String, dynamic> weather = {
      if (temperature != null) 'temperature': temperature,
      if (humidity != null) 'humidity': humidity,
    };
    final Map<String, dynamic> disease = {
      if (diseaseName != null) 'name': diseaseName,
      if (severity != null) 'severity': severity,
    };
    return {
      if (cropName != null) 'crop_name': cropName,
      if (soil.isNotEmpty) 'soil': soil,
      if (weather.isNotEmpty) 'weather': weather,
      if (disease.isNotEmpty) 'disease': disease,
    };
  }
}

/// Parsed recommendation-engine response.
class RecommendationResult {
  const RecommendationResult({
    required this.success,
    required this.status,
    required this.recommendationType,
    required this.recommendations,
    required this.warnings,
    required this.requiredContext,
    required this.missing,
    required this.reason,
    required this.confidence,
    required this.model,
    required this.provider,
    required this.message,
  });

  static const String statusAvailable = 'RECOMMENDATION_AVAILABLE';
  static const String statusInsufficientData = 'INSUFFICIENT_DATA';
  static const String statusModelNotConfigured = 'MODEL_NOT_CONFIGURED';
  static const String statusProviderUnavailable = 'PROVIDER_UNAVAILABLE';

  final bool success;
  final String status;
  final String recommendationType;
  final List<RecommendationItem> recommendations;
  final List<String> warnings;
  final List<String> requiredContext;
  final List<String> missing;
  final String? reason;
  final double? confidence;
  final String? model;
  final String? provider;
  final String? message;

  bool get hasRecommendations => recommendations.isNotEmpty;
  bool get isInsufficientData => status == statusInsufficientData;
  bool get isModelNotConfigured => status == statusModelNotConfigured;
  bool get isProviderUnavailable => status == statusProviderUnavailable;

  factory RecommendationResult.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return RecommendationResult(
      success: map['success'] as bool? ?? true,
      status: map['status'] as String? ?? '',
      recommendationType: map['recommendation_type'] as String? ?? '',
      recommendations: _parseItems(map['recommendations']),
      warnings: _parseStrings(map['warnings']),
      requiredContext: _parseStrings(map['required_context']),
      missing: _parseStrings(map['missing']),
      reason: map['reason'] as String?,
      confidence: (map['confidence'] as num?)?.toDouble(),
      model: map['model'] as String?,
      provider: map['provider'] as String?,
      message: map['message'] as String?,
    );
  }

  static List<RecommendationItem> _parseItems(Object? value) {
    if (value is! List) return const [];
    return value.whereType<Map<String, dynamic>>().map(RecommendationItem.fromJson).toList();
  }

  static List<String> _parseStrings(Object? value) {
    if (value is! List) return const [];
    return value.whereType<String>().toList();
  }
}
