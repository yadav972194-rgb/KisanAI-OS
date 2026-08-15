import '../../core/network/api_client.dart';
import '../../models/assistant.dart';

/// Assistant endpoint (`POST /api/assistant`).
class AssistantApi {
  AssistantApi(this._client);

  final ApiClient _client;

  /// Sends a free-text farmer query and returns the honest answer.
  Future<AssistantResponse> ask(String text, {Map<String, dynamic>? soil}) {
    return _client.postJson(
      '/api/assistant',
      {
        'text': text,
        if (soil != null && soil.isNotEmpty) 'soil': soil,
      },
      AssistantResponse.fromJson,
    );
  }
}
