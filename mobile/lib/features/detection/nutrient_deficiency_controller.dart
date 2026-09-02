import '../../core/image/picked_image.dart';
import '../../models/nutrient_deficiency.dart';
import '../../services/nutrient_deficiency_api.dart';
import 'detection_controller.dart';

/// Nutrient-deficiency detection controller bound to
/// `POST /api/nutrient-deficiency/detect`.
class NutrientDeficiencyController
    extends DetectionController<NutrientDeficiencyResult> {
  NutrientDeficiencyController(NutrientDeficiencyApi api, ImagePickerFn pickImage)
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