import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/feedback/feedback_controller.dart';
import 'package:kisanai/services/feedback_api.dart';

import 'helpers/fake_backend.dart';

void main() {
  group('FeedbackController', () {
    (FeedbackController, FakeBackend) build(FakeBackend backend) {
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      return (FeedbackController(FeedbackApi(client)), backend);
    }

    test('load populates the user own feedback history', () async {
      final (controller, _) = build(FakeBackend());
      expect(controller.items, isEmpty);
      await controller.load();
      expect(controller.state, FeedbackViewState.ready);
      expect(controller.items, hasLength(1));
      expect(controller.items.first.subject, 'सिंचाई समस्या');
    });

    test('load failure surfaces a connection error', () async {
      final (controller, _) = build(FakeBackend()..failFeedback = true);
      await controller.load();
      expect(controller.items, isEmpty);
      expect(controller.state, FeedbackViewState.error);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });

    test('submit raises feedback and refreshes the history', () async {
      final (controller, _) = build(FakeBackend());
      await controller.load();
      final ok = await controller.submit(
        subject: 'लोन समस्या',
        description: 'किसान क्रेडिट कार्ड चाहिए',
        priority: 'high',
      );
      expect(ok, isTrue);
      expect(controller.items, hasLength(2));
      expect(controller.items.first.subject, 'लोन समस्या');
      expect(controller.busy, isFalse);
    });

    test('submit never sends farmer_id or user_id', () async {
      final backend = FakeBackend();
      final (controller, _) = build(backend);
      final ok = await controller.submit(
        subject: 'प्रमाणित बीज',
        description: 'अच्छे बीज की आपूर्ति चाहिए',
      );
      expect(ok, isTrue);
      expect(backend.lastFeedbackPayload, isNotNull);
      expect(
        backend.lastFeedbackPayload!.containsKey('farmer_id'),
        isFalse,
      );
      expect(backend.lastFeedbackPayload!.containsKey('user_id'), isFalse);
      expect(backend.lastFeedbackPayload!['priority'], 'medium');
    });

    test('submit failure returns false and surfaces the error', () async {
      final backend = FakeBackend();
      final (controller, _) = build(backend);
      backend.failFeedback = true;
      final ok = await controller.submit(
        subject: 'समस्या',
        description: 'विवरण',
      );
      expect(ok, isFalse);
      expect(controller.errorMessage, contains('नेटवर्क'));
      expect(controller.busy, isFalse);
    });
  });
}