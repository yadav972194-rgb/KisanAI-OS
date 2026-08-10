import '../../core/network/api_client.dart';
import '../../models/disease_detection.dart';

/// Disease-detection endpoint (`POST /api/disease-detection`).
///
/// The image is sent as multipart `file` (JPG/JPEG/PNG, max 5 MB) with an
/// optional `crop_name` form field.
class DiseaseDetectionApi {
  DiseaseDetectionApi(this._client);

  final ApiClient _client;

  Future<DiseaseDetectionResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) {
    return _client.postMultipart(
      '/api/disease-detection',
      field: 'file',
      bytes: imageBytes,
      filename: imageName,
      fields: {
        if (cropName != null && cropName.trim().isNotEmpty)
          'crop_name': cropName.trim(),
      },
      parse: DiseaseDetectionResult.fromJson,
    );
  }
}
