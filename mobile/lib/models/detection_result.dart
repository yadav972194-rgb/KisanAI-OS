/// Common contract for crop-health detection results so the shared
/// [DetectionScreen] state machine can render without knowing the concrete
/// detector payload.
abstract class DetectionResultModel {
  /// True when the backend reports no bundled model. Must never be confused
  /// with "healthy", "no pest", or a real identification.
  bool get isModelNotConfigured;

  /// Model confidence, when a bundled model produced a result.
  double? get confidence;

  /// Backend-provided human-readable message, when present.
  String? get message;
}