import '../../core/network/api_client.dart';
import '../../models/nutrient_deficiency.dart';

/// Nutrient-deficiency detection endpoint (`POST /api/nutrient-deficiency/detect`).
///
/// The image is sent as multipart `file` (JPG/JPEG/PNG, max 5 MB) with an
/// optional `crop_name` form field.
class NutrientDeficiencyApi {
  NutrientDeficiencyApi(this._client);

  final ApiClient _client;

  Future<NutrientDeficiencyResult> detect({
    required List<int> imageBytes,
    required String imageName,
    String? cropName,
  }) {
    return _client.postMultipart(
      '/api/nutrient-deficiency/detect',
      field: 'file',
      bytes: imageBytes,
      filename: imageName,
      fields: {
        if (cropName != null && cropName.trim().isNotEmpty)
          'crop_name': cropName.trim(),
      },
      parse: NutrientDeficiencyResult.fromJson,
    );
  }
}