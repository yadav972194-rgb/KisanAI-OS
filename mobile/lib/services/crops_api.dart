import '../../core/network/api_client.dart';
import '../../models/crop.dart';

/// Crops endpoints (`GET /api/crops`).
class CropsApi {
  CropsApi(this._client);

  final ApiClient _client;

  Future<List<Crop>> fetchCrops() {
    return _client.getJson('/api/crops', _parse);
  }

  static List<Crop> _parse(Object? json) {
    if (json is! List) return const [];
    return json
        .whereType<Map<String, dynamic>>()
        .map(Crop.fromJson)
        .toList();
  }
}
