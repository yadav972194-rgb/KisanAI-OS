/// Assistant response model (`AssistantOut` from `POST /api/assistant`).
library;

class AssistantResponse {
  const AssistantResponse({
    required this.intent,
    required this.status,
    required this.message,
    this.data,
  });

  final String intent;
  final String status;
  final String message;
  final Map<String, dynamic>? data;

  bool get isOk => status == 'OK';
  bool get isInsufficientData => status == 'INSUFFICIENT_DATA';

  factory AssistantResponse.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return AssistantResponse(
      intent: map['intent'] as String? ?? '',
      status: map['status'] as String? ?? '',
      message: map['message'] as String? ?? '',
      data: map['data'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(map['data'] as Map)
          : null,
    );
  }
}
