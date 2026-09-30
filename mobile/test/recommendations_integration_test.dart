import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/recommendations/recommendations_controller.dart';
import 'package:kisanai/models/recommendation.dart';
import 'package:kisanai/services/recommendations_api.dart';

/// End-to-end integration tests for `/api/recommendations`.
///
/// These run the real production stack — `ApiClient` + [RecommendationsApi] +
/// models — over real TCP sockets against a local [HttpServer] that mirrors
/// the FastAPI contract (auth header check, the required-context missing-data
/// computation, the `RECOMMENDATION_AVAILABLE` shape, and the stable error
/// envelopes). The server binds to 127.0.0.1 so the suite is deterministic
/// and never touches the network.
void main() {
  const validToken = 'test-token';
  const requiredSoilFields = ['ph', 'moisture', 'nitrogen', 'phosphorus',
      'potassium'];
  const requiredWeatherFields = ['temperature', 'humidity', 'condition',
      'wind_speed'];
  late HttpServer server;
  late String baseUrl;

  List<String> missingFor(Map<String, dynamic> data) {
    final missing = <String>[];
    if (data['crop_name'] is! String) missing.add('crop');
    final soil = data['soil'];
    if (soil is! Map<String, dynamic> || soil.isEmpty) {
      missing.add('soil');
    } else {
      for (final field in requiredSoilFields) {
        if (soil[field] == null) missing.add('soil.$field');
      }
    }
    final weather = data['weather'];
    if (weather is! Map<String, dynamic> || weather.isEmpty) {
      missing.add('weather');
    } else {
      for (final field in requiredWeatherFields) {
        if (weather[field] == null) missing.add('weather.$field');
      }
    }
    return missing;
  }

  Future<void> handle(HttpRequest request) async {
    final body = await utf8.decoder.bind(request).join();
    final authorized =
        request.headers.value('authorization') == 'Bearer $validToken';

    Map<String, dynamic> data;
    try {
      data = body.isEmpty
          ? const {}
          : jsonDecode(body) as Map<String, dynamic>;
    } on FormatException {
      data = const {};
    }

    Map<String, dynamic>? payload;
    var status = 200;
    if (!authorized) {
      status = 401;
      payload = {
        'detail': {
          'success': false,
          'message': 'Not authenticated',
          'code': 'SESSION_EXPIRED',
        },
      };
    } else {
      final missing = missingFor(data);
      if (missing.isNotEmpty) {
        payload = {
          'success': true,
          'status': 'INSUFFICIENT_DATA',
          'recommendation_type': 'general',
          'recommendations': [],
          'warnings': [],
          'required_context': ['crop', 'soil', 'weather'],
          'missing': missing,
          'reason': 'Required agricultural context is missing',
          'confidence': null,
          'model': null,
          'provider': null,
          'message': 'Insufficient data to generate a recommendation',
        };
      } else {
        payload = {
          'success': true,
          'status': 'RECOMMENDATION_AVAILABLE',
          'recommendation_type': 'general',
          'recommendations': [
            {
              'category': 'जल',
              'text': 'सुबह हल्की सिंचाई करें',
              'reason': 'मिट्टी की नमी कम है',
              'source': 'recommendation_engine',
            },
          ],
          'warnings': ['मौसम पूर्वानुमान उपलब्ध नहीं'],
          'required_context': ['crop', 'soil', 'weather'],
          'missing': [],
          'reason': null,
          'confidence': null,
          'model': null,
          'provider': null,
          'message': '',
        };
      }
    }

    request.response
      ..statusCode = status
      ..headers.contentType = ContentType.json
      ..write(jsonEncode(payload));
    await request.response.close();
  }

  setUpAll(() async {
    HttpOverrides.global = null;
    server = await HttpServer.bind('127.0.0.1', 0);
    baseUrl = 'http://127.0.0.1:${server.port}';
    server.listen((request) async {
      await handle(request);
    });
  });

  tearDownAll(() async {
    await server.close(force: true);
  });

  ApiClient authenticatedClient() => ApiClient(
        baseUrl: baseUrl,
        tokenProvider: () async => validToken,
      );

  const fullInput = RecommendationInput(
    cropName: 'Wheat',
    ph: 6.5,
    moisture: 30,
    nitrogen: 40,
    phosphorus: 25,
    potassium: 30,
    temperature: 28,
    humidity: 60,
  );

  test('authenticated full app-provided context mirrors the real engine',
      () async {
    final api = RecommendationsApi(authenticatedClient());
    final result = await api.fetchRecommendations(fullInput);

    // The app's recommendation form supplies temperature + humidity, so the
    // real engine (faithfully mirrored here) still requires condition +
    // wind_speed and reports exactly those as missing context. This proves
    // the real API path end-to-end without fabricating a recommendation.
    expect(result.success, isTrue);
    expect(result.isInsufficientData, isTrue);
    expect(result.hasRecommendations, isFalse);
    expect(result.missing, ['weather.condition', 'weather.wind_speed']);
    expect(result.requiredContext, ['crop', 'soil', 'weather']);
    expect(result.recommendations, isEmpty);
    expect(result.warnings, isEmpty);
    expect(result.reason, 'Required agricultural context is missing');
  });

  test('missing context surfaces INSUFFICIENT_DATA with the missing keys',
      () async {
    final api = RecommendationsApi(authenticatedClient());
    final result = await api.fetchRecommendations(
      const RecommendationInput(cropName: 'Wheat'),
    );

    expect(result.success, isTrue);
    expect(result.isInsufficientData, isTrue);
    expect(result.recommendations, isEmpty);
    expect(result.requiredContext, contains('soil'));
    expect(result.requiredContext, contains('weather'));
    expect(result.missing, contains('soil'));
    expect(result.missing, contains('weather'));
  });

  test('unauthenticated request raises a 401 session error', () async {
    final api = RecommendationsApi(ApiClient(baseUrl: baseUrl));
    await expectLater(
      api.fetchRecommendations(fullInput),
      throwsA(
        isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)
            .having((e) => e.code, 'code', 'SESSION_EXPIRED'),
      ),
    );
  });

  test('insufficient data never fabricates recommendations', () async {
    final client = ApiClient(
      baseUrl: baseUrl,
      tokenProvider: () async => validToken,
    );
    final controller = RecommendationsController(
      RecommendationsApi(client),
    );
    await controller.submit(fullInput);

    expect(controller.state, RecommendationState.success);
    expect(controller.result!.isInsufficientData, isTrue);
    expect(controller.result!.hasRecommendations, isFalse);
    expect(
      controller.result!.missing,
      ['weather.condition', 'weather.wind_speed'],
    );
  });
}