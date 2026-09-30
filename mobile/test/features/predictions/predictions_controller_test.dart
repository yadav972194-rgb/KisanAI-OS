import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/constants/app_strings.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/predictions/predictions_controller.dart';
import 'package:kisanai/models/prediction.dart';
import 'package:kisanai/services/predictions_api.dart';

import '../../helpers/fake_backend.dart';

void main() {
  group('PredictionsController', () {
    (PredictionsController, FakeBackend) build(FakeBackend backend) {
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      return (
        PredictionsController(PredictionsApi(client)),
        backend,
      );
    }

    const input = PredictionInput(
      predictionType: PredictionInput.typeCropYield,
      cropName: 'Wheat',
    );

    test('submit with MODEL_NOT_CONFIGURED is surfaced, never fabricated',
        () async {
      final (controller, _) = build(FakeBackend());
      await controller.submit(input);
      expect(controller.state, PredictionState.success);
      expect(controller.result!.isModelNotConfigured, isTrue);
      expect(controller.result!.result, isNull);
      expect(controller.result!.confidence, isNull);
      expect(controller.result!.model, isNull);
    });

    test('submit with a real provider payload parses the result', () async {
      final (controller, _) = build(
        FakeBackend(predictionStatus: 'COMPLETE'),
      );
      await controller.submit(input);
      expect(controller.state, PredictionState.success);
      expect(controller.result!.isModelNotConfigured, isFalse);
      expect(controller.result!.result, contains('yield_tons_per_hectare'));
      expect(controller.result!.confidence, 0.88);
      expect(controller.result!.model, 'fake-yield-1.0');
    });

    test('submit network failure surfaces connection error', () async {
      final controller = PredictionsController(
        _ThrowingPredictionsApi(
          ApiClient(
            baseUrl: 'http://test.local',
            httpClient: FakeBackend().client(),
          ),
        ),
      );
      await controller.submit(input);
      expect(controller.state, PredictionState.error);
      expect(controller.errorMessage, AppStrings.connectionError);
    });

    test('submit API error surfaces server message', () async {
      final controller = PredictionsController(
        _ApiErrorPredictionsApi(
          ApiClient(
            baseUrl: 'http://test.local',
            httpClient: FakeBackend().client(),
          ),
        ),
      );
      await controller.submit(input);
      expect(controller.state, PredictionState.error);
      expect(controller.errorMessage, 'server rejected');
    });

    test('submit session-expired error surfaces session message', () async {
      final controller = PredictionsController(
        _SessionExpiredPredictionsApi(
          ApiClient(
            baseUrl: 'http://test.local',
            httpClient: FakeBackend().client(),
          ),
        ),
      );
      await controller.submit(input);
      expect(controller.state, PredictionState.error);
      expect(controller.errorMessage, AppStrings.sessionExpired);
    });
  });
}

class _ThrowingPredictionsApi extends PredictionsApi {
  _ThrowingPredictionsApi(super.client);

  @override
  Future<PredictionResult> fetchPredictions(PredictionInput input) async {
    throw ApiException('', isNetwork: true);
  }
}

class _ApiErrorPredictionsApi extends PredictionsApi {
  _ApiErrorPredictionsApi(super.client);

  @override
  Future<PredictionResult> fetchPredictions(PredictionInput input) async {
    throw ApiException('server rejected', statusCode: 500);
  }
}

class _SessionExpiredPredictionsApi extends PredictionsApi {
  _SessionExpiredPredictionsApi(super.client);

  @override
  Future<PredictionResult> fetchPredictions(PredictionInput input) async {
    throw const ApiException(
      'Session expired',
      statusCode: 401,
      code: ApiErrorCode.sessionExpired,
    );
  }
}