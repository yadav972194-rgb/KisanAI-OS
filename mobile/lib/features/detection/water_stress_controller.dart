import '../../core/image/picked_image.dart';
import '../../models/water_stress.dart';
import '../../services/water_stress_api.dart';
import 'detection_controller.dart';

/// Crop-water-stress detection controller bound to
/// `POST /api/water-stress/detect`.
class WaterStressController extends DetectionController<WaterStressResult> {
  WaterStressController(WaterStressApi api, ImagePickerFn pickImage)
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