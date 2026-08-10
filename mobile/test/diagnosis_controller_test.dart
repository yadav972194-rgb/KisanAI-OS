import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/image/picked_image.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/diagnosis/diagnosis_controller.dart';
import 'package:kisanai/models/disease_detection.dart';
import 'package:kisanai/services/disease_detection_api.dart';

import 'helpers/fake_backend.dart';

const _leaf = PickedImage(name: 'leaf.jpg', bytes: [1, 2, 3, 4]);

void main() {
  (DiagnosisController, FakeBackend) build({
    required ImagePickerFn picker,
    String detectStatus = 'MODEL_NOT_CONFIGURED',
  }) {
    final backend = FakeBackend(detectStatus: detectStatus);
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    final controller = DiagnosisController(
      DiseaseDetectionApi(client),
      picker,
    );
    return (controller, backend);
  }

  group('DiagnosisController', () {
    test('selectImage without a picked file keeps state idle', () async {
      final (controller, _) = build(picker: () async => null);
      await controller.selectImage();
      expect(controller.state, DiagnosisState.idle);
      expect(controller.selectedImage, isNull);
    });

    test('selectImage stores the picked image and clears old result', () async {
      final (controller, _) = build(picker: () async => _leaf);
      await controller.selectImage();
      expect(controller.selectedImage, isNotNull);
      expect(controller.selectedImage!.name, 'leaf.jpg');
      expect(controller.state, DiagnosisState.idle);
    });

    test('detect without image reports a friendly error', () async {
      final (controller, _) = build(picker: () async => null);
      await controller.detect();
      expect(controller.state, DiagnosisState.error);
      expect(controller.errorMessage, contains('फोटो'));
    });

    test('MODEL_NOT_CONFIGURED result is a success state, not an error',
        () async {
      final (controller, _) = build(picker: () async => _leaf);
      await controller.selectImage();
      await controller.detect(cropName: 'गेहूँ');
      expect(controller.state, DiagnosisState.success);
      expect(controller.result, isNotNull);
      expect(controller.result!.isModelNotConfigured, isTrue);
      expect(controller.errorMessage, isNull);
    });

    test('HEALTHY result parses correctly', () async {
      final (controller, _) =
          build(picker: () async => _leaf, detectStatus: 'HEALTHY');
      await controller.selectImage();
      await controller.detect();
      expect(controller.state, DiagnosisState.success);
      expect(controller.result!.isHealthy, isTrue);
    });

    test('network failure surfaces connection error', () async {
      final controller = DiagnosisController(
        _ThrowingDetectionApi(ApiClient(
          baseUrl: 'http://test.local',
          httpClient: FakeBackend().client(),
        )),
        () async => _leaf,
      );
      await controller.selectImage();
      await controller.detect();
      expect(controller.state, DiagnosisState.error);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });
  });
}

class _ThrowingDetectionApi extends DiseaseDetectionApi {
  _ThrowingDetectionApi(super.client);

  @override
  Future<DiseaseDetectionResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) async {
    throw ApiException('', isNetwork: true);
  }
}
