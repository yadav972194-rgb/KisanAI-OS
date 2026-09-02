import '../../core/network/api_client.dart';
import '../../models/pest_detection.dart';

/// Pest-detection endpoint (`POST /api/pest/detect`).
///
/// The image is sent as multipart `file` (JPG/JPEG/PNG, max 5 MB) with an
/// optional `crop_name` form field.
class PestDetectionApi {
  PestDetectionApi(this._client);

  final ApiClient _client;

  Future<PestDetectionResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) {
    return _client.postMultipart(
      '/api/pest/detect',
      field: 'file',
      bytes: imageBytes,
      filename: imageName,
      fields: {
        if (cropName != null && cropName.trim().isNotEmpty)
          'crop_name': cropName.trim(),
      },
      parse: PestDetectionResult.fromJson,
    );
  }
}