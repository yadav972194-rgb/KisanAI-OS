import '../../core/network/api_client.dart';
import '../../models/farmer.dart';

/// Farmer endpoints (`GET /api/farmers`).
class FarmersApi {
  FarmersApi(this._client);

  final ApiClient _client;

  Future<List<Farmer>> fetchFarmers() {
    return _client.getJson('/api/farmers', _parse);
  }

  static List<Farmer> _parse(Object? json) {
    if (json is! List) return const [];
    return json
        .whereType<Map<String, dynamic>>()
        .map(Farmer.fromJson)
        .toList();
  }
}
