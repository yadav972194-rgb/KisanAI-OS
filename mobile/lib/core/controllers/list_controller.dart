import 'package:flutter/material.dart';

import '../constants/app_strings.dart';
import '../errors/api_exception.dart';
import '../errors/error_messages.dart';

/// Load state of a [ListController].
enum ListLoadState { initial, loading, success, error }

/// Generic read-only list controller shared by the farmer/crop/soil/disease
/// screens. Keeps feature code focused while giving every list the same
/// loading / error / empty behaviour.
class ListController<T> extends ChangeNotifier {
  ListController(this._loader);

  final Future<List<T>> Function() _loader;

  ListLoadState state = ListLoadState.initial;
  List<T> items = const [];
  String? errorMessage;

  Future<void> load() async {
    state = ListLoadState.loading;
    errorMessage = null;
    notifyListeners();
    try {
      items = await _loader();
      state = ListLoadState.success;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = ListLoadState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = ListLoadState.error;
    }
    notifyListeners();
  }
}
