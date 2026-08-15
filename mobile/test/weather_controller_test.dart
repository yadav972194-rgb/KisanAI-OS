import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/weather/weather_controller.dart';
import 'package:kisanai/services/weather_api.dart';

import 'helpers/fake_backend.dart';

void main() {
  group('WeatherController', () {
    (WeatherController, FakeBackend) build(FakeBackend backend) {
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      return (WeatherController(WeatherApi(client)), backend);
    }

    test('load sets weather from the API', () async {
      final (controller, _) = build(FakeBackend());
      expect(controller.isLoading, isFalse);
      await controller.load();
      expect(controller.weather, isNotNull);
      expect(controller.weather!.location, 'Delhi');
      expect(controller.weather!.temperature, 28.5);
      expect(controller.errorMessage, isNull);
      expect(controller.isLoading, isFalse);
    });

    test('load failure surfaces a connection error', () async {
      final (controller, _) = build(FakeBackend()..failWeather = true);
      await controller.load();
      expect(controller.weather, isNull);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });

    test('load toggles isLoading while in flight', () async {
      final (controller, _) = build(FakeBackend());
      final future = controller.load();
      expect(controller.isLoading, isTrue);
      await future;
      expect(controller.isLoading, isFalse);
    });

    test('fresh cache is served without a second network request', () async {
      final backend = FakeBackend();
      final (controller, _) = build(backend);
      await controller.load();
      final callsAfterFirstLoad = backend.weatherCalls;

      await controller.load();
      expect(controller.weather, isNotNull);
      expect(backend.weatherCalls, callsAfterFirstLoad);
    });

    test('expired cache refetches from the network', () async {
      final backend = FakeBackend();
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      final controller = WeatherController(
        WeatherApi(client),
        cacheTtl: Duration.zero,
      );
      await controller.load();
      final callsAfterFirstLoad = backend.weatherCalls;

      await controller.load();
      expect(backend.weatherCalls, greaterThan(callsAfterFirstLoad));
    });

    test('concurrent load calls are deduplicated', () async {
      final backend = FakeBackend();
      final (controller, _) = build(backend);

      await Future.wait([controller.load(), controller.load()]);
      expect(controller.weather, isNotNull);
      expect(backend.weatherCalls, 1);
    });

    test('refresh forces a real fetch even when cached', () async {
      final backend = FakeBackend();
      final (controller, _) = build(backend);
      await controller.load();
      final callsAfterFirstLoad = backend.weatherCalls;

      await controller.refresh();
      expect(backend.weatherCalls, callsAfterFirstLoad + 1);
    });
  });
}
