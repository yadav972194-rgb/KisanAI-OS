import '../../core/network/api_client.dart';
import '../../models/weed_detection.dart';

/// Weed-detection endpoint (`POST /api/weed/detect`).
///
/// The image is sent as multipart `file` (JPG/JPEG/PNG, max 5 MB) with an
/// optional `crop_name` form field.
class WeedDetectionApi {
  WeedDetectionApi(this._client);

  final ApiClient _client;

  Future<WeedDetectionResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) {
    return _client.postMultipart(
      '/api/weed/detect',
      field: 'file',
      bytes: imageBytes,
      filename: imageName,
      fields: {
        if (cropName != null && cropName.trim().isNotEmpty)
          'crop_name': cropName.trim(),
      },
      parse: WeedDetectionResult.fromJson,
    );
  }
}