import '../../core/errors/api_exception.dart';
import '../../core/network/api_client.dart';

/// Location hierarchy endpoints (`/api/locations`).
///
/// Mirrors the FastAPI contract: plain JSON string arrays for
/// countries/states, and `?state=` / `?district=` / `?tehsil=` query
/// filtering for districts/tehsils/villages. Results are de-duplicated so a
/// dropdown never sees duplicate option values.
class LocationApi {
  LocationApi(this._client);

  final ApiClient _client;

  /// All supported countries.
  Future<List<String>> fetchCountries() {
    return _client.getJson('/api/locations/countries', _parseList);
  }

  /// All supported Indian states/UTs.
  Future<List<String>> fetchStates() {
    return _client.getJson('/api/locations/states', _parseList);
  }

  /// Districts belonging to [state].
  Future<List<String>> fetchDistricts(String state) {
    final query = Uri.encodeQueryComponent(state);
    return _client.getJson('/api/locations/districts?state=$query', _parseList);
  }

  /// Blocks/tehsils belonging to [district].
  Future<List<String>> fetchBlocks(String district) {
    final query = Uri.encodeQueryComponent(district);
    return _client.getJson('/api/locations/blocks?district=$query', _parseList);
  }

  /// Villages belonging to [tehsil].
  ///
  /// A 404 (older backend without the villages endpoint) degrades to an
  /// empty list so the UI falls back to free-text गाँव entry.
  Future<List<String>> fetchVillages(String tehsil) async {
    final query = Uri.encodeQueryComponent(tehsil);
    try {
      return await _client.getJson(
        '/api/locations/villages?tehsil=$query',
        _parseList,
      );
    } on ApiException catch (e) {
      if (e.statusCode == 404) return const [];
      rethrow;
    }
  }

  static List<String> _parseList(Object? json) {
    if (json is! List) return const [];
    final names = json
        .whereType<String>()
        .map((item) => item.trim())
        .where((item) => item.isNotEmpty)
        .toList();
    return names.toSet().toList();
  }
}