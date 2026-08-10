import 'package:image_picker/image_picker.dart';

import 'picked_image.dart';

/// Production gallery picker backed by the `image_picker` plugin.
Future<PickedImage?> pickImageFromGallery() async {
  final picker = ImagePicker();
  final file = await picker.pickImage(
    source: ImageSource.gallery,
    imageQuality: 85,
  );
  if (file == null) return null;
  final bytes = await file.readAsBytes();
  return PickedImage(name: file.name, bytes: bytes);
}
