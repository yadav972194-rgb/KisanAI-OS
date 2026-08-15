import '../../core/errors/api_exception.dart';
import '../../core/network/api_client.dart';
import '../../models/crop.dart';
import '../../models/farmer.dart';

/// Self-service farm endpoints (`/api/my-farm`).
///
/// Mirrors the FastAPI contract: a `GET` on an unset farm returns 404, which
/// this layer converts into `null` so the UI can offer the create form.
class MyFarmApi {
  MyFarmApi(this._client);

  final ApiClient _client;

  /// Fetches the current user's farm; returns null when none exists (404).
  Future<Farmer?> fetchFarm() async {
    try {
      return await _client.getJson('/api/my-farm', Farmer.fromJson);
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }

  /// Lists crops planted on the current user's farm.
  Future<List<Crop>> fetchCrops() {
    return _client.getJson('/api/my-farm/crops', _parseCrops);
  }

  Future<void> createFarm({
    required String village,
    required String district,
    required String state,
    double? farmSize,
  }) {
    return _client.postJson(
      '/api/my-farm',
      {
        'village': village,
        'district': district,
        'state': state,
        'farm_size': ?farmSize,
      },
      _message,
    );
  }

  Future<void> updateFarm({
    String? village,
    String? district,
    String? state,
    double? farmSize,
  }) {
    return _client.putJson(
      '/api/my-farm',
      {
        'village': ?village,
        'district': ?district,
        'state': ?state,
        'farm_size': ?farmSize,
      },
      _message,
    );
  }

  Future<void> deleteFarm() {
    return _client.deleteJson('/api/my-farm', _message);
  }

  Future<void> addCrop({
    required String cropName,
    required String season,
    required int durationDays,
    required String waterRequirement,
  }) {
    return _client.postJson(
      '/api/my-farm/crops',
      {
        'crop_name': cropName,
        'season': season,
        'duration_days': durationDays,
        'water_requirement': waterRequirement,
      },
      _message,
    );
  }

  Future<void> updateCrop(
    int cropId, {
    required String cropName,
    required String season,
    required int durationDays,
    required String waterRequirement,
  }) {
    return _client.putJson(
      '/api/my-farm/crops/$cropId',
      {
        'crop_name': cropName,
        'season': season,
        'duration_days': durationDays,
        'water_requirement': waterRequirement,
      },
      _message,
    );
  }

  Future<void> deleteCrop(int cropId) {
    return _client.deleteJson('/api/my-farm/crops/$cropId', _message);
  }

  static List<Crop> _parseCrops(Object? json) {
    if (json is! List) return const [];
    return json
        .whereType<Map<String, dynamic>>()
        .map(Crop.fromJson)
        .toList();
  }

  /// Validates a `MessageOut` body and throws on a failed operation.
  static void _message(Object? json) {
    final map = json;
    if (map is Map<String, dynamic> && map['success'] == false) {
      throw ApiException(map['message'] as String? ?? 'Request failed');
    }
  }
}
