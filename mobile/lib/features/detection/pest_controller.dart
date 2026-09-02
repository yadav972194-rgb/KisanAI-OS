import '../../core/image/picked_image.dart';
import '../../models/pest_detection.dart';
import '../../services/pest_detection_api.dart';
import 'detection_controller.dart';

/// Pest-detection controller bound to `POST /api/pest/detect`.
class PestController extends DetectionController<PestDetectionResult> {
  PestController(PestDetectionApi api, ImagePickerFn pickImage)
      : super(
          runner: ({
            required List<int> imageBytes,
            required String imageName,
            String? cropName,
          }) =>
              api.detect(
                imageBytes: imageBytes,
                imageName: imageName,
                cropName: cropName,
              ),
          pickImage: pickImage,
        );
}