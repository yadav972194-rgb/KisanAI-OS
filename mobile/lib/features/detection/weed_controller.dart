import '../../core/image/picked_image.dart';
import '../../models/weed_detection.dart';
import '../../services/weed_detection_api.dart';
import 'detection_controller.dart';

/// Weed-detection controller bound to `POST /api/weed/detect`.
class WeedController extends DetectionController<WeedDetectionResult> {
  WeedController(WeedDetectionApi api, ImagePickerFn pickImage)
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