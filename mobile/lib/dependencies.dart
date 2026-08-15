import 'core/config/app_config.dart';
import 'core/controllers/list_controller.dart';
import 'core/image/gallery_image_picker.dart';
import 'core/image/picked_image.dart';
import 'core/network/api_client.dart';
import 'core/storage/token_storage.dart';
import 'features/auth/auth_controller.dart';
import 'features/auth/forgot_password_controller.dart';
import 'features/assistant/assistant_controller.dart';
import 'features/diagnosis/diagnosis_controller.dart';
import 'features/my_farm/my_farm_controller.dart';
import 'features/recommendations/recommendations_controller.dart';
import 'features/weather/weather_controller.dart';
import 'models/crop.dart';
import 'models/disease.dart';
import 'models/farmer.dart';
import 'models/soil.dart';
import 'services/auth_api.dart';
import 'services/assistant_api.dart';
import 'services/crops_api.dart';
import 'services/disease_detection_api.dart';
import 'services/diseases_api.dart';
import 'services/farmers_api.dart';
import 'services/my_farm_api.dart';
import 'services/recommendations_api.dart';
import 'services/soils_api.dart';
import 'services/weather_api.dart';

/// Composition root for the app.
///
/// Tests construct this with an injected [ApiClient] (e.g. backed by
/// `package:http/testing`'s `MockClient`) and an [InMemoryTokenStorage], so
/// the whole app runs without a device or a live backend.
class AppDependencies {
  AppDependencies({ApiClient? apiClient, TokenStorage? tokenStorage})
      : tokenStorage = tokenStorage ?? SecureTokenStorage() {
    this.apiClient = apiClient ??
        ApiClient(
          baseUrl: AppConfig.apiBaseUrl,
          tokenProvider: this.tokenStorage.read,
          onUnauthorized: () => authController.logout(),
        );
  }

  final TokenStorage tokenStorage;
  late final ApiClient apiClient;

  late final AuthApi authApi = AuthApi(apiClient);
  late final WeatherApi weatherApi = WeatherApi(apiClient);
  late final CropsApi cropsApi = CropsApi(apiClient);
  late final SoilsApi soilsApi = SoilsApi(apiClient);
  late final FarmersApi farmersApi = FarmersApi(apiClient);
  late final DiseasesApi diseasesApi = DiseasesApi(apiClient);
  late final DiseaseDetectionApi diseaseDetectionApi =
      DiseaseDetectionApi(apiClient);
  late final MyFarmApi myFarmApi = MyFarmApi(apiClient);
  late final RecommendationsApi recommendationsApi =
      RecommendationsApi(apiClient);
  late final AssistantApi assistantApi = AssistantApi(apiClient);

  late final ImagePickerFn imagePicker = pickImageFromGallery;

  late final AuthController authController = AuthController(authApi, tokenStorage);
  late final ForgotPasswordController forgotPasswordController =
      ForgotPasswordController(authApi);
  late final WeatherController weatherController = WeatherController(weatherApi);
  late final ListController<Crop> cropsController =
      ListController<Crop>(cropsApi.fetchCrops);
  late final ListController<Soil> soilsController =
      ListController<Soil>(soilsApi.fetchSoils);
  late final ListController<Farmer> farmersController =
      ListController<Farmer>(farmersApi.fetchFarmers);
  late final ListController<Disease> diseasesController =
      ListController<Disease>(diseasesApi.fetchDiseases);
  late final DiagnosisController diagnosisController =
      DiagnosisController(diseaseDetectionApi, imagePicker);
  late final RecommendationsController recommendationsController =
      RecommendationsController(recommendationsApi);
  late final AssistantController assistantController =
      AssistantController(assistantApi);
  late final MyFarmController myFarmController = MyFarmController(myFarmApi);
}
