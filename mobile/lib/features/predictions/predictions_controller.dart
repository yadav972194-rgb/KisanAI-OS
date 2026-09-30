import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../models/prediction.dart';
import '../../services/predictions_api.dart';

enum PredictionState { idle, loading, success, error }

/// Submits agricultural context to the prediction engine and holds the result.
class PredictionsController extends ChangeNotifier {
  PredictionsController(this._api);

  final PredictionsApi _api;

  PredictionState state = PredictionState.idle;
  PredictionResult? result;
  String? errorMessage;

  Future<void> submit(PredictionInput input) async {
    state = PredictionState.loading;
    errorMessage = null;
    notifyListeners();
    try {
      result = await _api.fetchPredictions(input);
      state = PredictionState.success;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = PredictionState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = PredictionState.error;
    }
    notifyListeners();
  }
}