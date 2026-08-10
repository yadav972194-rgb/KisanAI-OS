/// Crop model (`CropOut`).
class Crop {
  const Crop({
    required this.cropId,
    required this.farmerId,
    required this.cropName,
    required this.season,
    required this.durationDays,
    required this.waterRequirement,
    required this.createdAt,
  });

  final int cropId;
  final int? farmerId;
  final String cropName;
  final String season;
  final int durationDays;
  final String waterRequirement;
  final String createdAt;

  factory Crop.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return Crop(
      cropId: (map['crop_id'] as num).toInt(),
      farmerId: (map['farmer_id'] as num?)?.toInt(),
      cropName: map['crop_name'] as String? ?? '',
      season: map['season'] as String? ?? '',
      durationDays: (map['duration_days'] as num?)?.toInt() ?? 0,
      waterRequirement: map['water_requirement'] as String? ?? '',
      createdAt: map['created_at'] as String? ?? '',
    );
  }
}
