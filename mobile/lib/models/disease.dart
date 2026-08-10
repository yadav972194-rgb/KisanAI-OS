/// Disease record model (`DiseaseOut`).
class Disease {
  const Disease({
    required this.diseaseId,
    required this.cropId,
    required this.cropName,
    required this.diseaseName,
    required this.symptoms,
    required this.solution,
    required this.severity,
    required this.createdAt,
  });

  final int diseaseId;
  final int? cropId;
  final String cropName;
  final String diseaseName;
  final String symptoms;
  final String solution;
  final String severity;
  final String createdAt;

  factory Disease.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return Disease(
      diseaseId: (map['disease_id'] as num).toInt(),
      cropId: (map['crop_id'] as num?)?.toInt(),
      cropName: map['crop_name'] as String? ?? '',
      diseaseName: map['disease_name'] as String? ?? '',
      symptoms: map['symptoms'] as String? ?? '',
      solution: map['solution'] as String? ?? '',
      severity: map['severity'] as String? ?? '',
      createdAt: map['created_at'] as String? ?? '',
    );
  }
}
