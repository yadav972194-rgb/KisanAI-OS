import '../../core/network/api_client.dart';
import '../../models/recommendation.dart';

/// Recommendation endpoint (`POST /api/recommendations`).
class RecommendationsApi {
  RecommendationsApi(this._client);

  final ApiClient _client;

  Future<RecommendationResult> fetchRecommendations(
    RecommendationInput input,
  ) {
    return _client.postJson(
      '/api/recommendations',
      input.toJson(),
      RecommendationResult.fromJson,
    );
  }
}
