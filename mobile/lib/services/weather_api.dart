import '../../core/network/api_client.dart';
import '../../models/weather.dart';

/// Weather endpoint (`GET /api/weather`).
class WeatherApi {
  WeatherApi(this._client);

  final ApiClient _client;

  Future<Weather> fetchWeather() {
    return _client.getJson('/api/weather', Weather.fromJson);
  }
}
