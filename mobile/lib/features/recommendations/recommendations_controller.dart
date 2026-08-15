import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../models/recommendation.dart';
import '../../services/recommendations_api.dart';

enum RecommendationState { idle, loading, success, error }

/// Submits farmer context to the recommendation engine and holds the result.
class RecommendationsController extends ChangeNotifier {
  RecommendationsController(this._api);

  final RecommendationsApi _api;

  RecommendationState state = RecommendationState.idle;
  RecommendationResult? result;
  String? errorMessage;

  Future<void> submit(RecommendationInput input) async {
    state = RecommendationState.loading;
    errorMessage = null;
    notifyListeners();
    try {
      result = await _api.fetchRecommendations(input);
      state = RecommendationState.success;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = RecommendationState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = RecommendationState.error;
    }
    notifyListeners();
  }
}
