import '../../core/network/api_client.dart';
import '../../models/growth_stage.dart';

/// Crop-growth-stage detection endpoint (`POST /api/growth-stage/detect`).
///
/// The image is sent as multipart `file` (JPG/JPEG/PNG, max 5 MB) with an
/// optional `crop_name` form field.
class GrowthStageApi {
  GrowthStageApi(this._client);

  final ApiClient _client;

  Future<GrowthStageResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) {
    return _client.postMultipart(
      '/api/growth-stage/detect',
      field: 'file',
      bytes: imageBytes,
      filename: imageName,
      fields: {
        if (cropName != null && cropName.trim().isNotEmpty)
          'crop_name': cropName.trim(),
      },
      parse: GrowthStageResult.fromJson,
    );
  }
}