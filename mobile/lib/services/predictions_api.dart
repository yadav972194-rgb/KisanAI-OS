import '../../core/network/api_client.dart';
import '../../models/prediction.dart';

/// Prediction endpoint (`POST /api/predictions`).
class PredictionsApi {
  PredictionsApi(this._client);

  final ApiClient _client;

  Future<PredictionResult> fetchPredictions(PredictionInput input) {
    return _client.postJson(
      '/api/predictions',
      input.toJson(),
      PredictionResult.fromJson,
    );
  }
}