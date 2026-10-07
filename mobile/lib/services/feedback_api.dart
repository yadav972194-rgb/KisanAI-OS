import '../../core/network/api_client.dart';
import '../../models/admin_models.dart';

/// Farmer self-service feedback endpoints (`/api/feedback`).
///
/// Mirrors the FastAPI contract for "Kisan ki Baat": a farmer raises a
/// problem/suggestion with their own authenticated session and reads back
/// only their own records.
///
/// Ownership is bound server-side from the bearer token: this client never
/// sends a `farmer_id` or `user_id`, so the UI cannot file feedback as (or
/// read feedback belonging to) another farmer.
class FeedbackApi {
  FeedbackApi(this._client);

  final ApiClient _client;

  /// Raises a feedback/problem record for the logged-in user.
  Future<FeedbackItem> submit({
    required String subject,
    required String description,
    String priority = 'medium',
  }) {
    return _client.postJson(
      '/api/feedback',
      {
        'subject': subject,
        'description': description,
        'priority': priority,
      },
      FeedbackItem.fromJson,
    );
  }

  /// Lists only the logged-in user's own feedback, newest first.
  Future<List<FeedbackItem>> fetchMine({int page = 1, int size = 20}) {
    return _client.getJson(
      '/api/feedback?page=$page&size=$size',
      _parseItems,
    );
  }

  static List<FeedbackItem> _parseItems(Object? json) {
    if (json is! Map<String, dynamic>) return const [];
    final items = json['items'];
    if (items is! List) return const [];
    return items
        .whereType<Map<String, dynamic>>()
        .map(FeedbackItem.fromJson)
        .toList();
  }
}