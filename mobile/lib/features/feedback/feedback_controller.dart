import 'package:flutter/foundation.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
import '../../core/errors/error_messages.dart';
import '../../models/admin_models.dart';
import '../../services/feedback_api.dart';

/// Load state of a [FeedbackController].
enum FeedbackViewState { initial, loading, ready, error }

/// Owns the current user's farmer feedback ("Kisan ki Baat"): the form
/// submission plus the read-back of the user's own records.
///
/// Mirrors the [MyFarmController] lifecycle: `load()` fetches the history,
/// `submit()` posts a record (with the busy flag) and refreshes the list on
/// success. Ownership is bound server-side from the token, so the controller
/// never carries a `farmer_id`/`user_id`.
class FeedbackController extends ChangeNotifier {
  FeedbackController(this._api);

  final FeedbackApi _api;

  FeedbackViewState state = FeedbackViewState.initial;
  List<FeedbackItem> items = const [];
  String? errorMessage;
  bool busy = false;

  Future<void> load() async {
    state = FeedbackViewState.loading;
    errorMessage = null;
    notifyListeners();
    try {
      items = await _api.fetchMine();
      state = FeedbackViewState.ready;
    } on ApiException catch (e) {
      errorMessage = errorMessageFor(e);
      state = FeedbackViewState.error;
    } catch (_) {
      errorMessage = AppStrings.genericError;
      state = FeedbackViewState.error;
    }
    notifyListeners();
  }

  Future<bool> submit({
    required String subject,
    required String description,
    String priority = 'medium',
  }) async {
    busy = true;
    errorMessage = null;
    notifyListeners();
    try {
      await _api.submit(
        subject: subject,
        description: description,
        priority: priority,
      );
      await load();
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