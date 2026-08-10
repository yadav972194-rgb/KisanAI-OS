import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../models/weather.dart';
import '../../services/weather_api.dart';

/// Loads and caches the current weather.
class WeatherController extends ChangeNotifier {
  WeatherController(this._api);

  final WeatherApi _api;

  Weather? weather;
  bool isLoading = false;
  String? errorMessage;

  Future<void> load() async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      weather = await _api.fetchWeather();
    } on ApiException catch (e) {
      errorMessage =
          e.isNetwork ? AppStrings.connectionError : e.message;
    } catch (_) {
      errorMessage = AppStrings.genericError;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }
}
