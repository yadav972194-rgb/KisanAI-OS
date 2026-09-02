import '../../core/image/picked_image.dart';
import '../../models/growth_stage.dart';
import '../../services/growth_stage_api.dart';
import 'detection_controller.dart';

/// Crop-growth-stage detection controller bound to
/// `POST /api/growth-stage/detect`.
class GrowthStageController extends DetectionController<GrowthStageResult> {
  GrowthStageController(GrowthStageApi api, ImagePickerFn pickImage)
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