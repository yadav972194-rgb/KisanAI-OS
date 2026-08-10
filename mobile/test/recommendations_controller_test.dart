import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/recommendations/recommendations_controller.dart';
import 'package:kisanai/models/recommendation.dart';
import 'package:kisanai/services/recommendations_api.dart';

import 'helpers/fake_backend.dart';

void main() {
  group('RecommendationsController', () {
    (RecommendationsController, FakeBackend) build(FakeBackend backend) {
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      return (
        RecommendationsController(RecommendationsApi(client)),
        backend,
      );
    }

    const input = RecommendationInput(cropName: 'गेहूँ');

    test('submit with available recommendations parses items', () async {
      final (controller, _) = build(FakeBackend());
      await controller.submit(input);
      expect(controller.state, RecommendationState.success);
      expect(controller.result!.hasRecommendations, isTrue);
      expect(controller.result!.recommendations.first.category, 'जल');
      expect(controller.result!.recommendations.first.text, isNotEmpty);
    });

    test('submit with INSUFFICIENT_DATA surfaces missing context', () async {
      final (controller, _) = build(
        FakeBackend(recommendationStatus: 'INSUFFICIENT_DATA'),
      );
      await controller.submit(input);
      expect(controller.state, RecommendationState.success);
      expect(controller.result!.isInsufficientData, isTrue);
      expect(controller.result!.requiredContext, contains('soil.ph'));
      expect(controller.result!.recommendations, isEmpty);
    });

    test('submit with MODEL_NOT_CONFIGURED flags the status', () async {
      final (controller, _) = build(
        FakeBackend(recommendationStatus: 'MODEL_NOT_CONFIGURED'),
      );
      await controller.submit(input);
      expect(controller.state, RecommendationState.success);
      expect(controller.result!.isModelNotConfigured, isTrue);
    });

    test('submit network failure surfaces connection error', () async {
      final controller = RecommendationsController(
        _ThrowingRecommendationsApi(
          ApiClient(
            baseUrl: 'http://test.local',
            httpClient: FakeBackend().client(),
          ),
        ),
      );
      await controller.submit(input);
      expect(controller.state, RecommendationState.error);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });

    test('submit API error surfaces server message', () async {
      final controller = RecommendationsController(
        _ApiErrorRecommendationsApi(
          ApiClient(
            baseUrl: 'http://test.local',
            httpClient: FakeBackend().client(),
          ),
        ),
      );
      await controller.submit(input);
      expect(controller.state, RecommendationState.error);
      expect(controller.errorMessage, 'server rejected');
    });
  });
}

class _ThrowingRecommendationsApi extends RecommendationsApi {
  _ThrowingRecommendationsApi(super.client);

  @override
  Future<RecommendationResult> fetchRecommendations(
    RecommendationInput input,
  ) async {
    throw ApiException('', isNetwork: true);
  }
}

class _ApiErrorRecommendationsApi extends RecommendationsApi {
  _ApiErrorRecommendationsApi(super.client);

  @override
  Future<RecommendationResult> fetchRecommendations(
    RecommendationInput input,
  ) async {
    throw ApiException('server rejected', statusCode: 500);
  }
}
