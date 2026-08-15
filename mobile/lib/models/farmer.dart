import 'crop.dart';

/// Farmer record model (`FarmerOut`), including nested crops.
class Farmer {
  const Farmer({
    required this.farmerId,
    required this.userId,
    required this.name,
    required this.mobile,
    required this.village,
    required this.district,
    required this.state,
    required this.farmSize,
    required this.createdAt,
    required this.crops,
  });

  final int farmerId;
  final int? userId;
  final String name;
  final String mobile;
  final String village;
  final String district;
  final String state;
  final double? farmSize;
  final String createdAt;
  final List<Crop> crops;

  factory Farmer.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return Farmer(
      farmerId: (map['farmer_id'] as num).toInt(),
      userId: (map['user_id'] as num?)?.toInt(),
      name: map['name'] as String? ?? '',
      mobile: map['mobile'] as String? ?? '',
      village: map['village'] as String? ?? '',
      district: map['district'] as String? ?? '',
      state: map['state'] as String? ?? '',
      farmSize: (map['farm_size'] as num?)?.toDouble(),
      createdAt: map['created_at'] as String? ?? '',
      crops: _parseCrops(map['crops']),
    );
  }

  static List<Crop> _parseCrops(Object? value) {
    if (value is! List) return const [];
    return value
        .whereType<Map<String, dynamic>>()
        .map(Crop.fromJson)
        .toList();
  }

  /// Short summary like "गाँव: X, जिला: Y".
  String get locationSummary => '$village, $district';
}
