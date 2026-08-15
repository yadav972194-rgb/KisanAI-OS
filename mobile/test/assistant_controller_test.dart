import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/assistant/assistant_controller.dart';
import 'package:kisanai/models/assistant.dart';
import 'package:kisanai/services/assistant_api.dart';

import 'helpers/fake_backend.dart';

void main() {
  group('AssistantController', () {
    (AssistantController, FakeBackend) build(FakeBackend backend) {
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      return (AssistantController(AssistantApi(client)), backend);
    }

    test('CROP_STATUS without farm surfaces the honest missing-data message',
        () async {
      final (controller, _) = build(FakeBackend());
      await controller.ask('मेरी फसल के क्या हाल हैं?');

      expect(controller.state, AssistantState.success);
      expect(controller.response!.intent, 'CROP_STATUS');
      expect(controller.response!.isInsufficientData, isTrue);
      expect(controller.response!.message, contains('फसल की जानकारी दर्ज करें'));
    });

    test('CROP_STATUS with farm and crops returns verified status',
        () async {
      final backend = FakeBackend();
      backend.myFarm = {
        'farmer_id': 1,
        'village': 'Rampur',
        'district': 'Sitapur',
        'state': 'Uttar Pradesh',
        'farm_size': 3.5,
        'crops': <Map<String, dynamic>>[],
      };
      backend.myCrops.add({
        'crop_id': 1,
        'crop_name': 'गेहूँ',
        'season': 'Rabi',
        'duration_days': 120,
        'water_requirement': 'Medium',
      });
      final (controller, _) = build(backend);
      await controller.ask('मेरी फसल के क्या हाल हैं?');

      expect(controller.state, AssistantState.success);
      expect(controller.response!.isOk, isTrue);
      final data = controller.response!.data!;
      expect(data['farm']['village'], 'Rampur');
      expect(data['crops'], hasLength(1));
      expect((data['crops'] as List).first['crop_name'], 'गेहूँ');
      expect(data['weather']['condition'], 'Clear');
    });

    test('WEATHER question returns honest weather', () async {
      final (controller, _) = build(FakeBackend());
      await controller.ask('आज मौसम कैसा है?');

      expect(controller.state, AssistantState.success);
      expect(controller.response!.intent, 'WEATHER');
      expect(controller.response!.message, contains('मौसम'));
      expect(controller.response!.data!['temperature'], 28.5);
    });

    test('empty question is ignored (stays idle)', () async {
      final (controller, _) = build(FakeBackend());
      await controller.ask('   ');
      expect(controller.state, AssistantState.idle);
      expect(controller.response, isNull);
    });

    test('network failure surfaces connection error', () async {
      final controller = AssistantController(
        _ThrowingAssistantApi(
          ApiClient(
            baseUrl: 'http://test.local',
            httpClient: FakeBackend().client(),
          ),
        ),
      );
      await controller.ask('मेरी फसल के क्या हाल हैं?');
      expect(controller.state, AssistantState.error);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });

    test('clear resets state', () async {
      final (controller, _) = build(FakeBackend());
      await controller.ask('मेरी फसल के क्या हाल हैं?');
      controller.clear();
      expect(controller.state, AssistantState.idle);
      expect(controller.response, isNull);
    });
  });
}

class _ThrowingAssistantApi extends AssistantApi {
  _ThrowingAssistantApi(super.client);

  @override
  Future<AssistantResponse> ask(
    String text, {
    Map<String, dynamic>? soil,
  }) async {
    throw ApiException('', isNetwork: true);
  }
}
