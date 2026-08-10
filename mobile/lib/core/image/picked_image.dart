/// A user-selected image held in memory (never written to local disk).
class PickedImage {
  const PickedImage({required this.name, required this.bytes});

  final String name;
  final List<int> bytes;
}

/// Signature for the gallery picker so controllers stay testable without
/// touching the platform plugin.
typedef ImagePickerFn = Future<PickedImage?> Function();
