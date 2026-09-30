import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../models/admin_models.dart';
import '../../models/crop.dart';
import '../../models/farmer.dart';
import '../../models/soil.dart';
import '../../services/admin_api.dart';

/// Load state of the primary screen being shown inside the admin module.
enum AdminViewState { initial, loading, ready, error }

/// Owns the admin module: summary, farmer directory, farmer profile,
/// problems/contacts, notifications and the audit trail.
///
/// Write operations return `true` on success (and refresh the affected
/// collection); failures are surfaced through [errorMessage].
class AdminController extends ChangeNotifier {
  AdminController(this._api);

  final AdminApi _api;

  AdminViewState summaryState = AdminViewState.initial;
  AdminViewState directoryState = AdminViewState.initial;
  AdminViewState profileState = AdminViewState.initial;
  AdminViewState problemsState = AdminViewState.initial;
  AdminViewState notificationsState = AdminViewState.initial;
  AdminViewState auditState = AdminViewState.initial;

  AdminSummary? summary;
  String? profileVillage;

  List<Farmer> farmers = const [];
  FarmerProfile? profile;
  List<FeedbackItem> problems = const [];
  List<ContactRecord> contacts = const [];
  List<NotificationItem> notifications = const [];
  List<AuditEntry> audit = const [];

  String searchQuery = '';
  String errorMessage = '';
  bool busy = false;

  bool get isSuperAdmin => summary?.isSuperAdmin ?? false;

  Future<void> loadSummary() async {
    summaryState = AdminViewState.loading;
    _clearError();
    notifyListeners();
    try {
      summary = await _api.fetchSummary();
      summaryState = AdminViewState.ready;
    } catch (e) {
      summaryState = AdminViewState.error;
      errorMessage = _messageFor(e);
    }
    notifyListeners();
  }

  Future<void> loadFarmers({String? query}) async {
    directoryState = AdminViewState.loading;
    searchQuery = query ?? searchQuery;
    notifyListeners();
    try {
      farmers = await _api.searchFarmers(query: searchQuery);
      directoryState = AdminViewState.ready;
    } catch (e) {
      directoryState = AdminViewState.error;
      errorMessage = _messageFor(e);
    }
    notifyListeners();
  }

  Future<void> openFarmer(int farmerId) async {
    profileState = AdminViewState.loading;
    _clearError();
    notifyListeners();
    try {
      profile = await _api.fetchFarmerProfile(farmerId);
      contacts = await _api.listFarmerContacts(farmerId);
      problems = await _api.listFarmerFeedback(farmerId);
      profileVillage = profile?.farmer.village;
      profileState = AdminViewState.ready;
    } catch (e) {
      profileState = AdminViewState.error;
      errorMessage = _messageFor(e);
    }
    notifyListeners();
  }

  Future<bool> updateFarmerProfile({
    required String name,
    required String mobile,
    required String village,
    String? block,
    required String district,
    required String state,
    double? farmSize,
  }) {
    return _save(
      () => _api.updateFarmerProfile(
        _requiredProfile.farmer.farmerId,
        name: name,
        mobile: mobile,
        village: village,
        block: block,
        district: district,
        state: state,
        farmSize: farmSize,
      ),
      reload: () async {
        await openFarmer(_requiredProfile.farmer.farmerId);
      },
    );
  }

  Future<bool> updateCrop(
    Crop crop, {
    required String cropName,
    required String season,
    required int durationDays,
    required String waterRequirement,
  }) {
    final farmerId = _requiredProfile.farmer.farmerId;
    return _save(
      () => _api.updateCrop(
        farmerId,
        crop.cropId,
        cropName: cropName,
        season: season,
        durationDays: durationDays,
        waterRequirement: waterRequirement,
      ),
      reload: () => openFarmer(farmerId),
    );
  }

  Future<bool> updateSoil(
    Soil soil, {
    required String soilType,
    required double ph,
    required double moisture,
    required int nitrogen,
    required int phosphorus,
    required int potassium,
  }) {
    final farmerId = _requiredProfile.farmer.farmerId;
    return _save(
      () => _api.updateSoil(
        farmerId,
        soil.soilId,
        soilType: soilType,
        ph: ph,
        moisture: moisture,
        nitrogen: nitrogen,
        phosphorus: phosphorus,
        potassium: potassium,
      ),
      reload: () => openFarmer(farmerId),
    );
  }

  Future<bool> recordContact({
    required String channel,
    String? reason,
    String? note,
  }) {
    final farmerId = _requiredProfile.farmer.farmerId;
    return _save(
      () => _api.recordContact(
        farmerId,
        channel: channel,
        reason: reason,
        note: note,
      ),
      reload: () async {
        contacts = await _api.listFarmerContacts(farmerId);
      },
    );
  }

  Future<bool> createProblem({
    int? farmerId,
    required String subject,
    required String description,
    String priority = 'medium',
  }) {
    return _save(
      () => _api.createProblem(
        farmerId: farmerId,
        subject: subject,
        description: description,
        priority: priority,
      ),
      reload: () async {
        problems = await _api.listFeedback();
        if (farmerId != null) {
          await openFarmer(farmerId);
        }
      },
    );
  }

  Future<bool> transitionStatus(int feedbackId, String status) {
    return _save(
      () => _api.transitionProblemStatus(feedbackId, status),
      reload: () async {
        problems = await _api.listFeedback();
      },
    );
  }

  Future<void> loadProblems() async {
    problemsState = AdminViewState.loading;
    _clearError();
    notifyListeners();
    try {
      problems = await _api.listFeedback();
      problemsState = AdminViewState.ready;
    } catch (e) {
      problemsState = AdminViewState.error;
      errorMessage = _messageFor(e);
    }
    notifyListeners();
  }

  Future<void> loadNotifications() async {
    notificationsState = AdminViewState.loading;
    _clearError();
    notifyListeners();
    try {
      notifications = await _api.listNotifications();
      notificationsState = AdminViewState.ready;
    } catch (e) {
      notificationsState = AdminViewState.error;
      errorMessage = _messageFor(e);
    }
    notifyListeners();
  }

  Future<bool> createNotification({
    required String category,
    required String title,
    required String message,
  }) {
    return _save(
      () => _api.createNotification(
        category: category,
        title: title,
        message: message,
      ),
      reload: loadNotifications,
    );
  }

  Future<bool> deliverNotification(int notificationId) {
    return _save(
      () => _api.deliverNotification(notificationId),
      reload: loadNotifications,
    );
  }

  Future<void> loadAudit() async {
    auditState = AdminViewState.loading;
    _clearError();
    notifyListeners();
    try {
      audit = await _api.listAudit();
      auditState = AdminViewState.ready;
    } catch (e) {
      auditState = AdminViewState.error;
      errorMessage = _messageFor(e);
    }
    notifyListeners();
  }

  // ==========================================================
  // Account controls (deactivate/restore/delete)
  // ==========================================================

  Future<bool> deactivateFarmer(int farmerId) {
    return _save(
      () => _api.deactivateFarmer(farmerId),
      reload: () async {
        final current = _requiredProfile.farmer.farmerId;
        if (current == farmerId) {
          await openFarmer(farmerId);
        }
      },
    );
  }

  Future<bool> restoreFarmer(int farmerId) {
    return _save(
      () => _api.restoreFarmer(farmerId),
      reload: () async {
        final current = _requiredProfile.farmer.farmerId;
        if (current == farmerId) {
          await openFarmer(farmerId);
        }
      },
    );
  }

  Future<bool> deactivateUser(int userId) {
    return _save(() => _api.deactivateUser(userId));
  }

  Future<bool> restoreUser(int userId) {
    return _save(() => _api.restoreUser(userId));
  }

  Future<bool> deleteUser(int userId) {
    return _save(() => _api.deleteUser(userId));
  }

  Future<bool> setSuperAdmin(int userId, bool enabled) {
    return _save(() => _api.setSuperAdmin(userId, enabled));
  }

  Future<bool> deleteFarmer(int farmerId, {required bool confirm}) {
    if (!confirm) return Future.value(true);
    return _save(() => _api.deleteFarmer(farmerId));
  }

  Future<DeletePreview?> fetchDeletePreview(int farmerId) async {
    try {
      return await _api.deleteFarmerPreview(farmerId);
    } catch (e) {
      errorMessage = _messageFor(e);
      notifyListeners();
      return null;
    }
  }

  FarmerProfile get _requiredProfile {
    final current = profile;
    if (current == null) {
      throw StateError('no farmer profile loaded');
    }
    return current;
  }

  Future<bool> _save(
    Future<void> Function() action, {
    Future<void> Function()? reload,
  }) async {
    busy = true;
    errorMessage = '';
    notifyListeners();
    try {
      await action();
      if (reload != null) {
        await reload();
      }
      return true;
    } catch (e) {
      errorMessage = _messageFor(e);
      return false;
    } finally {
      busy = false;
      notifyListeners();
    }
  }

  String _messageFor(Object error) {
    if (error is ApiException) return errorMessageFor(error);
    return AppStrings.genericError;
  }

  void _clearError() {
    errorMessage = '';
  }
}