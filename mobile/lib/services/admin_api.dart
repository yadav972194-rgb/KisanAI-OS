import '../../core/network/api_client.dart';
import '../../models/admin_models.dart';
import '../../models/farmer.dart';

/// Admin Control & Farmer Support endpoints (`/api/admin/*`).
///
/// Every call is authenticated; super-admin-only actions (delete,
/// privilege assignment) simply return 403 for base admins.
class AdminApi {
  AdminApi(this._client);

  final ApiClient _client;

  Future<AdminSummary> fetchSummary() {
    return _client.getJson('/api/admin/me', AdminSummary.fromJson);
  }

  Future<List<Farmer>> searchFarmers({String? query}) {
    final q = query == null || query.trim().isEmpty
        ? ''
        : '?q=${Uri.encodeQueryComponent(query.trim())}';
    return _client.getJson(
      '/api/admin/farmers$q',
      (json) => _parseItems(json, Farmer.fromJson),
    );
  }

  Future<FarmerProfile> fetchFarmerProfile(int farmerId) {
    return _client.getJson(
      '/api/admin/farmers/$farmerId',
      FarmerProfile.fromJson,
    );
  }

  Future<void> updateFarmerProfile(
    int farmerId, {
    required String name,
    required String mobile,
    required String village,
    String? block,
    required String district,
    required String state,
    double? farmSize,
  }) async {
    await _client.putJson(
      '/api/admin/farmers/$farmerId',
      {
        'name': name,
        'mobile': mobile,
        'village': village,
        'block': ?block,
        'district': district,
        'state': state,
        'farm_size': ?farmSize,
      },
      _noop,
    );
  }

  Future<void> updateCrop(
    int farmerId,
    int cropId, {
    required String cropName,
    required String season,
    required int durationDays,
    required String waterRequirement,
  }) async {
    await _client.putJson(
      '/api/admin/farmers/$farmerId/crops/$cropId',
      {
        'crop_name': cropName,
        'season': season,
        'duration_days': durationDays,
        'water_requirement': waterRequirement,
      },
      _noop,
    );
  }

  Future<void> updateSoil(
    int farmerId,
    int soilId, {
    required String soilType,
    required double ph,
    required double moisture,
    required int nitrogen,
    required int phosphorus,
    required int potassium,
  }) async {
    await _client.putJson(
      '/api/admin/farmers/$farmerId/soils/$soilId',
      {
        'soil_type': soilType,
        'ph': ph,
        'moisture': moisture,
        'nitrogen': nitrogen,
        'phosphorus': phosphorus,
        'potassium': potassium,
      },
      _noop,
    );
  }

  Future<DeletePreview> deleteFarmerPreview(int farmerId) {
    return _client.postJson(
      '/api/admin/farmers/$farmerId/delete/preview',
      const {},
      DeletePreview.fromJson,
    );
  }

  Future<String> deleteFarmer(int farmerId) {
    return _client.deleteJson(
      '/api/admin/farmers/$farmerId?confirm=true',
      _message,
    );
  }

  Future<void> deactivateFarmer(int farmerId) async {
    await _client.postJson(
      '/api/admin/farmers/$farmerId/deactivate',
      const {},
      _noop,
    );
  }

  Future<void> restoreFarmer(int farmerId) async {
    await _client.postJson(
      '/api/admin/farmers/$farmerId/restore',
      const {},
      _noop,
    );
  }

  Future<void> deactivateUser(int userId) async {
    await _client.postJson(
      '/api/admin/users/$userId/deactivate',
      const {},
      _noop,
    );
  }

  Future<void> restoreUser(int userId) async {
    await _client.postJson(
      '/api/admin/users/$userId/restore',
      const {},
      _noop,
    );
  }

  Future<String> deleteUser(int userId) {
    return _client.deleteJson(
      '/api/admin/users/$userId?confirm=true',
      _message,
    );
  }

  Future<void> setSuperAdmin(int userId, bool enabled) async {
    await _client.postJson(
      '/api/admin/users/$userId/super-admin',
      {'super_admin': enabled},
      _noop,
    );
  }

  Future<List<FeedbackItem>> listFeedback({String? status, String? priority}) {
    final params = <String>[];
    if (status != null && status.isNotEmpty) {
      params.add('status=${Uri.encodeQueryComponent(status)}');
    }
    if (priority != null && priority.isNotEmpty) {
      params.add('priority=${Uri.encodeQueryComponent(priority)}');
    }
    final suffix = params.isEmpty ? '' : '?${params.join('&')}';
    return _client.getJson(
      '/api/admin/problems$suffix',
      (json) => _parseItems(json, FeedbackItem.fromJson),
    );
  }

  Future<List<FeedbackItem>> listFarmerFeedback(int farmerId) {
    return _client.getJson(
      '/api/admin/farmers/$farmerId/problems',
      (json) => _parseItems(json, FeedbackItem.fromJson),
    );
  }

  Future<FeedbackItem> createProblem({
    int? farmerId,
    required String subject,
    required String description,
    String priority = 'medium',
  }) async {
    return _client.postJson(
      '/api/admin/problems',
      {
        'farmer_id': ?farmerId,
        'subject': subject,
        'description': description,
        'priority': priority,
      },
      FeedbackItem.fromJson,
    );
  }

  Future<FeedbackItem> updateProblem(
    int feedbackId, {
    String? subject,
    String? description,
    String? priority,
  }) async {
    return _client.putJson(
      '/api/admin/problems/$feedbackId',
      {
        'subject': ?subject,
        'description': ?description,
        'priority': ?priority,
      },
      FeedbackItem.fromJson,
    );
  }

  Future<FeedbackItem> transitionProblemStatus(int feedbackId, String status) {
    return _client.patchJson(
      '/api/admin/problems/$feedbackId/status',
      {'status': status},
      FeedbackItem.fromJson,
    );
  }

  Future<List<ContactRecord>> listFarmerContacts(int farmerId) {
    return _client.getJson(
      '/api/admin/farmers/$farmerId/contacts',
      (json) => _parseItems(json, ContactRecord.fromJson),
    );
  }

  Future<ContactRecord> recordContact(
    int farmerId, {
    required String channel,
    String? reason,
    String? note,
  }) async {
    return _client.postJson(
      '/api/admin/farmers/$farmerId/contacts',
      {
        'channel': channel,
        'reason': ?reason,
        'note': ?note,
      },
      ContactRecord.fromJson,
    );
  }

  Future<List<NotificationItem>> listNotifications() {
    return _client.getJson(
      '/api/admin/notifications',
      (json) => _parseItems(json, NotificationItem.fromJson),
    );
  }

  Future<NotificationItem> createNotification({
    required String category,
    required String title,
    required String message,
  }) async {
    return _client.postJson(
      '/api/admin/notifications',
      {
        'category': category,
        'title': title,
        'message': message,
      },
      NotificationItem.fromJson,
    );
  }

  Future<String> deliverNotification(int notificationId) {
    return _client.postJson(
      '/api/admin/notifications/$notificationId/deliver',
      const {},
      _message,
    );
  }

  Future<List<AuditEntry>> listAudit() {
    return _client.getJson(
      '/api/admin/audit',
      (json) => _parseItems(json, AuditEntry.fromJson),
    );
  }

  static List<T> _parseItems<T>(
    Object? json,
    T Function(Object?) fromJson,
  ) {
    if (json is! Map<String, dynamic>) return const [];
    final items = json['items'];
    if (items is! List) return const [];
    return items.whereType<Map<String, dynamic>>().map(fromJson).toList();
  }

  static Object? _noop(Object? json) => null;

  static String _message(Object? json) {
    if (json is Map<String, dynamic>) {
      final message = json['message'];
      if (message is String && message.isNotEmpty) return message;
    }
    return '';
  }
}