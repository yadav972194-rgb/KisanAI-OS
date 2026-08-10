import '../../core/network/api_client.dart';
import '../../models/soil.dart';

/// Soil endpoints (`GET /api/soils`).
class SoilsApi {
  SoilsApi(this._client);

  final ApiClient _client;

  Future<List<Soil>> fetchSoils() {
    return _client.getJson('/api/soils', _parse);
  }

  static List<Soil> _parse(Object? json) {
    if (json is! List) return const [];
    return json
        .whereType<Map<String, dynamic>>()
        .map(Soil.fromJson)
        .toList();
  }
}
