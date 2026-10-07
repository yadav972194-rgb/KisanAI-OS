import 'crop.dart';

/// Farmer record model (`FarmerOut`), including nested crops.
class Farmer {
  const Farmer({
    required this.farmerId,
    required this.userId,
    required this.name,
    required this.mobile,
    required this.village,
    this.block,
    required this.district,
    required this.state,
    this.country,
    required this.farmSize,
    required this.createdAt,
    required this.crops,
  });

  final int farmerId;
  final int? userId;
  final String name;
  final String mobile;
  final String village;
  final String? block;
  final String district;
  final String state;
  final String? country;
  final double? farmSize;
  final String createdAt;
  final List<Crop> crops;

  factory Farmer.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    final block = map['block'] as String?;
    return Farmer(
      farmerId: (map['farmer_id'] as num).toInt(),
      userId: (map['user_id'] as num?)?.toInt(),
      name: map['name'] as String? ?? '',
      mobile: map['mobile'] as String? ?? '',
      village: map['village'] as String? ?? '',
      block: block == null || block.isEmpty ? null : block,
      district: map['district'] as String? ?? '',
      state: map['state'] as String? ?? '',
      country: map['country'] as String?,
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

  /// Short summary like "गाँव: X, जिला: Y" (with तहसील when set).
  String get locationSummary {
    final block = this.block;
    return block == null || block.isEmpty
        ? '$village, $district'
        : '$village, $block, $district';
  }
}
