import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/constants/app_strings.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/predictions/predictions_controller.dart';
import 'package:kisanai/models/prediction.dart';
import 'package:kisanai/services/predictions_api.dart';

/// End-to-end integration tests for `/api/predictions`.
///
/// These run the real production stack — `ApiClient` + [PredictionsApi] +
/// models — over real TCP sockets against a local [HttpServer] that mirrors
/// the FastAPI contract (auth header check, prediction_type validation, the
/// `MODEL_NOT_CONFIGURED` response shape, and the stable error envelopes).
/// The server binds to 127.0.0.1 so the suite is deterministic and never
/// touches the network.
void main() {
  const validTypes = {'crop_yield', 'soil_analysis'};
  const validToken = 'test-token';
  late HttpServer server;
  late String baseUrl;

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
    } else if (data['prediction_type'] is! String ||
        !validTypes.contains(data['prediction_type'])) {
      status = 422;
      payload = {
        'success': false,
        'message': 'Validation failed',
        'code': 'VALIDATION_ERROR',
      };
    } else {
      payload = {
        'success': true,
        'status': 'MODEL_NOT_CONFIGURED',
        'prediction_type': data['prediction_type'],
        'result': null,
        'confidence': null,
        'model': null,
        'metadata': null,
        'message': 'Prediction model is not configured',
      };
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

  const fullInput = PredictionInput(
    predictionType: PredictionInput.typeCropYield,
    cropName: 'Wheat',
    soil: PredictionSoilContext(
      soilType: 'Loamy',
      ph: 6.5,
      moisture: 30,
      nitrogen: 40,
      phosphorus: 25,
      potassium: 30,
    ),
    weather: PredictionWeatherContext(
      temperature: 28,
      humidity: 60,
      condition: 'Partly Cloudy',
      windSpeed: 8,
    ),
  );

  test('authenticated full-context request returns MODEL_NOT_CONFIGURED',
      () async {
    final api = PredictionsApi(authenticatedClient());
    final result = await api.fetchPredictions(fullInput);

    expect(result.success, isTrue);
    expect(result.isModelNotConfigured, isTrue);
    expect(result.predictionType, PredictionInput.typeCropYield);
    expect(result.result, isNull);
    expect(result.confidence, isNull);
    expect(result.model, isNull);
    expect(result.message, 'Prediction model is not configured');
  });

  test('minimal request (only prediction_type) parses', () async {
    final api = PredictionsApi(authenticatedClient());
    final result = await api.fetchPredictions(
      const PredictionInput(predictionType: PredictionInput.typeSoilAnalysis),
    );

    expect(result.success, isTrue);
    expect(result.isModelNotConfigured, isTrue);
    expect(result.predictionType, PredictionInput.typeSoilAnalysis);
  });

  test('unauthenticated request raises a 401 session error', () async {
    final api = PredictionsApi(ApiClient(baseUrl: baseUrl));
    await expectLater(
      api.fetchPredictions(fullInput),
      throwsA(
        isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 401)
            .having((e) => e.isUnauthorized, 'isUnauthorized', isTrue)
            .having((e) => e.code, 'code', 'SESSION_EXPIRED'),
      ),
    );
  });

  test('rejected session surfaces the session-expired message', () async {
    ApiClient? client;
    var loggedOut = false;
    client = ApiClient(
      baseUrl: baseUrl,
      tokenProvider: () async => 'stale-token',
      onUnauthorized: () => loggedOut = true,
    );
    final controller = PredictionsController(PredictionsApi(client));

    await controller.submit(fullInput);

    expect(controller.state, PredictionState.error);
    expect(controller.errorMessage, AppStrings.sessionExpired);
    // The live session the request was made with was refused.
    expect(loggedOut, isTrue);
  });

  test('controller surfaces MODEL_NOT_CONFIGURED honestly', () async {
    final controller = PredictionsController(
      PredictionsApi(authenticatedClient()),
    );
    await controller.submit(fullInput);

    expect(controller.state, PredictionState.success);
    expect(controller.result!.isModelNotConfigured, isTrue);
    expect(controller.result!.result, isNull);
    expect(controller.result!.confidence, isNull);
    expect(controller.result!.model, isNull);
  });

  test('invalid prediction_type maps to a controlled validation error',
      () async {
    final api = PredictionsApi(authenticatedClient());
    await expectLater(
      api.fetchPredictions(
        const PredictionInput(
          predictionType: 'quantum_yield',
          cropName: 'Wheat',
        ),
      ),
      throwsA(
        isA<ApiException>()
            .having((e) => e.statusCode, 'statusCode', 422)
            .having((e) => e.code, 'code', 'VALIDATION_ERROR'),
      ),
    );
  });
}