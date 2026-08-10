import '../../core/network/api_client.dart';
import '../../models/disease.dart';

/// Disease reference endpoints (`GET /api/diseases`).
class DiseasesApi {
  DiseasesApi(this._client);

  final ApiClient _client;

  Future<List<Disease>> fetchDiseases() {
    return _client.getJson('/api/diseases', _parse);
  }

  static List<Disease> _parse(Object? json) {
    if (json is! List) return const [];
    return json
        .whereType<Map<String, dynamic>>()
        .map(Disease.fromJson)
        .toList();
  }
}
