import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../models/weather.dart';
import '../../services/weather_api.dart';

/// Loads and caches the current weather.
///
/// Hardening against redundant network traffic:
/// - [load] serves a fresh in-memory snapshot for up to [cacheTtl] instead of
///   re-fetching every time a screen opens.
/// - Concurrent [load] calls are deduplicated: while one request is in flight,
///   other callers share the same future instead of firing duplicate requests.
/// - [refresh] forces a real refetch (used by the manual refresh button).
class WeatherController extends ChangeNotifier {
  WeatherController(this._api, {this.cacheTtl = const Duration(minutes: 5)});

  final WeatherApi _api;

  /// How long a fetched snapshot is reused before a refetch is allowed.
  final Duration cacheTtl;

  Weather? weather;
  bool isLoading = false;
  String? errorMessage;

  DateTime? _lastFetchedAt;
  Future<void>? _inFlight;

  bool get _isFresh {
    final fetched = _lastFetchedAt;
    if (fetched == null) return false;
    return DateTime.now().difference(fetched) < cacheTtl;
  }

  /// Loads weather, serving the fresh cache when available and
  /// deduplicating concurrent requests.
  Future<void> load({bool force = false}) {
    final inFlight = _inFlight;
    if (inFlight != null) return inFlight;
    if (!force && weather != null && _isFresh) {
      return Future.value();
    }
    return _start();
  }

  /// Force a fresh fetch from the backend.
  Future<void> refresh() => load(force: true);

  Future<void> _start() {
    isLoading = true;
    errorMessage = null;
    notifyListeners();

    final future = _fetch().whenComplete(() => _inFlight = null);
    _inFlight = future;
    return future;
  }

  Future<void> _fetch() async {
    try {
      weather = await _api.fetchWeather();
      _lastFetchedAt = DateTime.now();
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
    } catch (_) {
      errorMessage = AppStrings.genericError;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }
}
