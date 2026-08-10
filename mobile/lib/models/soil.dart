/// Soil record model (`SoilOut`).
class Soil {
  const Soil({
    required this.soilId,
    required this.farmerId,
    required this.soilType,
    required this.ph,
    required this.moisture,
    required this.nitrogen,
    required this.phosphorus,
    required this.potassium,
    required this.createdAt,
  });

  final int soilId;
  final int? farmerId;
  final String soilType;
  final double ph;
  final double moisture;
  final int nitrogen;
  final int phosphorus;
  final int potassium;
  final String createdAt;

  factory Soil.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return Soil(
      soilId: (map['soil_id'] as num).toInt(),
      farmerId: (map['farmer_id'] as num?)?.toInt(),
      soilType: map['soil_type'] as String? ?? '',
      ph: (map['ph'] as num?)?.toDouble() ?? 0,
      moisture: (map['moisture'] as num?)?.toDouble() ?? 0,
      nitrogen: (map['nitrogen'] as num?)?.toInt() ?? 0,
      phosphorus: (map['phosphorus'] as num?)?.toInt() ?? 0,
      potassium: (map['potassium'] as num?)?.toInt() ?? 0,
      createdAt: map['created_at'] as String? ?? '',
    );
  }
}
