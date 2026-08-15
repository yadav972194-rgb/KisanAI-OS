import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../models/crop.dart';
import '../../models/farmer.dart';
import '../../services/my_farm_api.dart';

/// Load state of a [MyFarmController].
enum MyFarmState { initial, loading, ready, error }

/// Owns the current user's farm: profile fields plus planted crops.
///
/// `farm` is null until the user creates one; the UI then shows the create
/// form. Write operations return `true` on success and refresh the loaded
/// data; failures are surfaced through [errorMessage].
class MyFarmController extends ChangeNotifier {
  MyFarmController(this._api);

  final MyFarmApi _api;

  MyFarmState state = MyFarmState.initial;
  Farmer? farm;
  List<Crop> crops = const [];
  String? errorMessage;
  bool busy = false;

  bool get hasFarm => farm != null;

  Future<void> load() async {
    state = MyFarmState.loading;
    errorMessage = null;
    notifyListeners();
    try {
      farm = await _api.fetchFarm();
      crops = farm == null ? const [] : await _api.fetchCrops();
      state = MyFarmState.ready;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = MyFarmState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = MyFarmState.error;
    }
    notifyListeners();
  }

  Future<bool> createFarm({
    required String village,
    required String district,
    required String state,
    double? farmSize,
  }) {
    return _save(
      () => _api.createFarm(
        village: village,
        district: district,
        state: state,
        farmSize: farmSize,
      ),
      reload: true,
    );
  }

  Future<bool> updateFarm({
    required String village,
    required String district,
    required String state,
    double? farmSize,
  }) {
    return _save(
      () => _api.updateFarm(
        village: village,
        district: district,
        state: state,
        farmSize: farmSize,
      ),
      reload: true,
    );
  }

  Future<bool> deleteFarm() {
    return _save(_api.deleteFarm, reload: true);
  }

  Future<bool> addCrop({
    required String cropName,
    required String season,
    required int durationDays,
    required String waterRequirement,
  }) {
    return _save(
      () => _api.addCrop(
        cropName: cropName,
        season: season,
        durationDays: durationDays,
        waterRequirement: waterRequirement,
      ),
      reload: true,
    );
  }

  Future<bool> updateCrop(
    Crop crop, {
    required String cropName,
    required String season,
    required int durationDays,
    required String waterRequirement,
  }) {
    return _save(
      () => _api.updateCrop(
        crop.cropId,
        cropName: cropName,
        season: season,
        durationDays: durationDays,
        waterRequirement: waterRequirement,
      ),
      reload: true,
    );
  }

  Future<bool> deleteCrop(Crop crop) {
    return _save(() => _api.deleteCrop(crop.cropId), reload: true);
  }

  Future<bool> _save(
    Future<void> Function() action, {
    bool reload = false,
  }) async {
    busy = true;
    errorMessage = null;
    notifyListeners();
    try {
      await action();
      if (reload) {
        await load();
      }
      return true;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      return false;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      return false;
    } finally {
      busy = false;
      notifyListeners();
    }
  }
}
