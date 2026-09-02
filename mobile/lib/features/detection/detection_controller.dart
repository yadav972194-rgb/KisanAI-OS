import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../core/image/picked_image.dart';

enum DetectionState { idle, analyzing, success, error }

/// Drives any crop-photo detection flow: pick → preview → detect → result.
///
/// Generic over the concrete detection result type so the single
/// pick/detect/error state machine is shared by every detector (pest, weed,
/// nutrient deficiency, growth stage, water stress) without duplicating
/// business logic.
class DetectionController<R> extends ChangeNotifier {
  DetectionController({
    required this.runner,
    required this.pickImage,
  });

  /// Performs the actual detection request for the concrete model.
  final Future<R> Function({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) runner;

  final ImagePickerFn pickImage;

  DetectionState state = DetectionState.idle;
  PickedImage? selectedImage;
  R? result;
  String? errorMessage;

  Future<void> selectImage() async {
    final picked = await pickImage();
    if (picked == null) return;
    selectedImage = picked;
    result = null;
    errorMessage = null;
    state = DetectionState.idle;
    notifyListeners();
  }

  Future<void> detect({String? cropName}) async {
    final image = selectedImage;
    if (image == null) {
      errorMessage = AppStrings.noImageSelected;
      state = DetectionState.error;
      notifyListeners();
      return;
    }
    state = DetectionState.analyzing;
    errorMessage = null;
    notifyListeners();
    try {
      result = await runner(
        imageBytes: image.bytes,
        imageName: image.name,
        cropName: cropName,
      );
      state = DetectionState.success;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = DetectionState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = DetectionState.error;
    }
    notifyListeners();
  }
}