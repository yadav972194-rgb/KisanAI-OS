import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/errors/api_exception.dart';
import 'package:kisanai/core/image/picked_image.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/detection/detection_controller.dart';
import 'package:kisanai/features/detection/pest_controller.dart';
import 'package:kisanai/models/pest_detection.dart';
import 'package:kisanai/services/pest_detection_api.dart';

import 'helpers/fake_backend.dart';

const _leaf = PickedImage(name: 'leaf.jpg', bytes: [1, 2, 3, 4]);

void main() {
  (DetectionController<PestDetectionResult>, FakeBackend) build({
    required ImagePickerFn picker,
    String? path,
    String? status,
  }) {
    final backend = FakeBackend(
      detectionStatuses: {if (path != null && status != null) path: status},
    );
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    final controller = PestController(PestDetectionApi(client), picker);
    return (controller, backend);
  }

  group('PestController', () {
    test('selectImage without a picked file keeps state idle', () async {
      final (controller, _) = build(picker: () async => null);
      await controller.selectImage();
      expect(controller.state, DetectionState.idle);
      expect(controller.selectedImage, isNull);
    });

    test('selectImage stores the picked image and clears old result', () async {
      final (controller, _) = build(picker: () async => _leaf);
      await controller.selectImage();
      expect(controller.selectedImage, isNotNull);
      expect(controller.selectedImage!.name, 'leaf.jpg');
      expect(controller.state, DetectionState.idle);
    });

    test('detect without image reports a friendly error', () async {
      final (controller, _) = build(picker: () async => null);
      await controller.detect();
      expect(controller.state, DetectionState.error);
      expect(controller.errorMessage, contains('फोटो'));
    });

    test('MODEL_NOT_CONFIGURED result is a success state, not an error',
        () async {
      final (controller, _) = build(picker: () async => _leaf);
      await controller.selectImage();
      await controller.detect(cropName: 'गेहूँ');
      expect(controller.state, DetectionState.success);
      expect(controller.result, isNotNull);
      expect(controller.result!.isModelNotConfigured, isTrue);
      expect(controller.errorMessage, isNull);
    });

    test('detected pest parses correctly', () async {
      final (controller, _) = build(
        picker: () async => _leaf,
        path: '/api/pest/detect',
        status: 'PEST_DETECTED',
      );
      await controller.selectImage();
      await controller.detect();
      expect(controller.state, DetectionState.success);
      expect(controller.result!.isModelNotConfigured, isFalse);
      expect(controller.result!.pestName, 'sample-name');
      expect(controller.result!.confidence, 0.87);
    });

    test('network failure surfaces connection error', () async {
      final controller = PestController(
        _ThrowingPestApi(ApiClient(
          baseUrl: 'http://test.local',
          httpClient: FakeBackend().client(),
        )),
        () async => _leaf,
      );
      await controller.selectImage();
      await controller.detect();
      expect(controller.state, DetectionState.error);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });
  });
}

class _ThrowingPestApi extends PestDetectionApi {
  _ThrowingPestApi(super.client);

  @override
  Future<PestDetectionResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) async {
    throw ApiException('', isNetwork: true);
  }
}