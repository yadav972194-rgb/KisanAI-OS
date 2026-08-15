import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../core/image/picked_image.dart';
import '../../models/disease_detection.dart';
import '../../services/disease_detection_api.dart';

enum DiagnosisState { idle, analyzing, success, error }

/// Drives the crop-photo diagnosis flow: pick → preview → detect → result.
class DiagnosisController extends ChangeNotifier {
  DiagnosisController(this._api, this._pickImage);

  final DiseaseDetectionApi _api;
  final ImagePickerFn _pickImage;

  DiagnosisState state = DiagnosisState.idle;
  PickedImage? selectedImage;
  DiseaseDetectionResult? result;
  String? errorMessage;

  Future<void> selectImage() async {
    final picked = await _pickImage();
    if (picked == null) return;
    selectedImage = picked;
    result = null;
    errorMessage = null;
    state = DiagnosisState.idle;
    notifyListeners();
  }

  Future<void> detect({String? cropName}) async {
    final image = selectedImage;
    if (image == null) {
      errorMessage = AppStrings.noImageSelected;
      state = DiagnosisState.error;
      notifyListeners();
      return;
    }
    state = DiagnosisState.analyzing;
    errorMessage = null;
    notifyListeners();
    try {
      result = await _api.detect(
        imageBytes: image.bytes,
        imageName: image.name,
        cropName: cropName,
      );
      state = DiagnosisState.success;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = DiagnosisState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = DiagnosisState.error;
    }
    notifyListeners();
  }
}
