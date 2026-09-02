import '../../core/network/api_client.dart';
import '../../models/water_stress.dart';

/// Crop-water-stress detection endpoint (`POST /api/water-stress/detect`).
///
/// The image is sent as multipart `file` (JPG/JPEG/PNG, max 5 MB) with an
/// optional `crop_name` form field.
class WaterStressApi {
  WaterStressApi(this._client);

  final ApiClient _client;

  Future<WaterStressResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) {
    return _client.postMultipart(
      '/api/water-stress/detect',
      field: 'file',
      bytes: imageBytes,
      filename: imageName,
      fields: {
        if (cropName != null && cropName.trim().isNotEmpty)
          'crop_name': cropName.trim(),
      },
      parse: WaterStressResult.fromJson,
    );
  }
}