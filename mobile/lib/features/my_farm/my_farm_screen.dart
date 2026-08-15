import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/common_views.dart';
import '../../dependencies.dart';
import '../../models/crop.dart';
import '../../models/farmer.dart';
import 'my_farm_controller.dart';

String _formatNumber(num value) =>
    value == value.roundToDouble() ? value.toInt().toString() : value.toString();

/// Self-service screen for the farmer's own farm.
///
/// Shows the create form when no farm exists, otherwise the farm profile
/// plus its planted crops (add/edit/delete).
class MyFarmScreen extends StatefulWidget {
  const MyFarmScreen({super.key});

  @override
  State<MyFarmScreen> createState() => _MyFarmScreenState();
}

class _MyFarmScreenState extends State<MyFarmScreen> {
  MyFarmController? _controller;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final controller = context.read<AppDependencies>().myFarmController;
    if (!identical(controller, _controller)) {
      _controller = controller;
      controller.load();
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _confirmDelete({
    required String title,
    required String message,
    required Future<bool> Function() action,
    required String successMessage,
  }) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text(AppStrings.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text(AppStrings.delete),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    final ok = await action();
    if (ok) _showMessage(successMessage);
  }

  Future<void> _editFarm(MyFarmController controller, Farmer farm) async {
    final draft = await _FarmFormSheet.show(
      context,
      initial: _FarmDraft.from(farm),
    );
    if (draft == null || !mounted) return;
    final ok = await controller.updateFarm(
      village: draft.village,
      district: draft.district,
      state: draft.state,
      farmSize: draft.farmSize,
    );
    if (ok) _showMessage(AppStrings.farmUpdated);
  }

  Future<void> _addCrop(MyFarmController controller) async {
    final draft = await _CropFormSheet.show(context);
    if (draft == null || !mounted) return;
    final ok = await controller.addCrop(
      cropName: draft.cropName,
      season: draft.season,
      durationDays: draft.durationDays,
      waterRequirement: draft.waterRequirement,
    );
    if (ok) _showMessage(AppStrings.cropAdded);
  }

  Future<void> _editCrop(MyFarmController controller, Crop crop) async {
    final draft = await _CropFormSheet.show(
      context,
      initial: _CropDraft.from(crop),
    );
    if (draft == null || !mounted) return;
    final ok = await controller.updateCrop(
      crop,
      cropName: draft.cropName,
      season: draft.season,
      durationDays: draft.durationDays,
      waterRequirement: draft.waterRequirement,
    );
    if (ok) _showMessage(AppStrings.cropUpdated);
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.read<AppDependencies>().myFarmController;
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(title: const Text(AppStrings.myFarmTitle)),
          floatingActionButton: controller.hasFarm
              ? FloatingActionButton.extended(
                  onPressed: controller.busy ? null : () => _addCrop(controller),
                  icon: const Icon(Icons.add),
                  label: const Text(AppStrings.addCropButton),
                )
              : null,
          body: Builder(
            builder: (context) {
              switch (controller.state) {
                case MyFarmState.initial:
                case MyFarmState.loading:
                  return const LoadingView();
                case MyFarmState.error:
                  return ErrorView(
                    message: controller.errorMessage,
                    onRetry: controller.load,
                  );
                case MyFarmState.ready:
                  if (!controller.hasFarm) {
                    return _CreateFarmForm(
                      controller: controller,
                      onMessage: _showMessage,
                    );
                  }
                  return _FarmDetails(
                    controller: controller,
                    onEdit: () => _editFarm(controller, controller.farm!),
                    onDelete: () => _confirmDelete(
                      title: AppStrings.myFarmTitle,
                      message: AppStrings.deleteFarmConfirm,
                      action: controller.deleteFarm,
                      successMessage: AppStrings.farmDeleted,
                    ),
                    onEditCrop: (crop) => _editCrop(controller, crop),
                    onDeleteCrop: (crop) => _confirmDelete(
                      title: crop.cropName,
                      message: AppStrings.deleteCropConfirm,
                      action: () => controller.deleteCrop(crop),
                      successMessage: AppStrings.cropDeleted,
                    ),
                  );
              }
            },
          ),
        );
      },
    );
  }
}

// ==========================================================
// Create form (no farm yet)
// ==========================================================

class _CreateFarmForm extends StatefulWidget {
  const _CreateFarmForm({required this.controller, required this.onMessage});

  final MyFarmController controller;
  final ValueChanged<String> onMessage;

  @override
  State<_CreateFarmForm> createState() => _CreateFarmFormState();
}

class _CreateFarmFormState extends State<_CreateFarmForm> {
  final _formKey = GlobalKey<FormState>();
  final _fieldsKey = GlobalKey<_FarmFormFieldsState>();

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    final fields = _fieldsKey.currentState!;
    final ok = await widget.controller.createFarm(
      village: fields.village,
      district: fields.district,
      state: fields.state,
      farmSize: fields.farmSize,
    );
    if (ok) widget.onMessage(AppStrings.farmCreated);
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.agriculture,
                      size: 56, color: AppTheme.primaryGreen),
                  const SizedBox(height: 12),
                  Text(
                    AppStrings.noFarmHint,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 24),
                  if (widget.controller.errorMessage != null) ...[
                    ErrorBanner(message: widget.controller.errorMessage!),
                    const SizedBox(height: 16),
                  ],
                  _FarmFormFields(key: _fieldsKey),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: widget.controller.busy ? null : _submit,
                    child: widget.controller.busy
                        ? const SizedBox(
                            height: 22,
                            width: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : const Text(AppStrings.createFarmButton),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ==========================================================
// Farm profile + crops (farm exists)
// ==========================================================

class _FarmDetails extends StatelessWidget {
  const _FarmDetails({
    required this.controller,
    required this.onEdit,
    required this.onDelete,
    required this.onEditCrop,
    required this.onDeleteCrop,
  });

  final MyFarmController controller;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final void Function(Crop crop) onEditCrop;
  final void Function(Crop crop) onDeleteCrop;

  @override
  Widget build(BuildContext context) {
    final farm = controller.farm!;
    return RefreshIndicator(
      onRefresh: controller.load,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          if (controller.errorMessage != null) ...[
            ErrorBanner(message: controller.errorMessage!),
            const SizedBox(height: 16),
          ],
          Card(
            clipBehavior: Clip.antiAlias,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.agriculture,
                          size: 40, color: AppTheme.primaryGreen),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          farm.name,
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                      ),
                      IconButton(
                        tooltip: AppStrings.editFarmButton,
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: onEdit,
                      ),
                      IconButton(
                        tooltip: AppStrings.deleteFarmButton,
                        icon: const Icon(Icons.delete_outline),
                        onPressed: onDelete,
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _InfoRow(label: AppStrings.mobileLabel, value: farm.mobile),
                  _InfoRow(
                      label: AppStrings.villageLabel, value: farm.village),
                  _InfoRow(
                      label: AppStrings.districtLabel, value: farm.district),
                  _InfoRow(label: AppStrings.stateLabel, value: farm.state),
                  _InfoRow(
                    label: AppStrings.farmSizeLabel,
                    value: farm.farmSize == null
                        ? '—'
                        : '${_formatNumber(farm.farmSize!)} ${AppStrings.farmSizeUnit}',
                  ),
                ],
              ),
            ),
          ),
          SectionHeader(
            title: AppStrings.myCropsTitle,
            subtitle: '${controller.crops.length} ${AppStrings.cropsCountLabel}',
          ),
          if (controller.crops.isEmpty)
            const EmptyView(message: AppStrings.noCropsYet)
          else
            for (final crop in controller.crops)
              _CropTile(
                crop: crop,
                onEdit: () => onEditCrop(crop),
                onDelete: () => onDeleteCrop(crop),
              ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: theme.textTheme.bodyMedium
                  ?.copyWith(color: theme.colorScheme.outline),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: theme.textTheme.bodyMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

class _CropTile extends StatelessWidget {
  const _CropTile({
    required this.crop,
    required this.onEdit,
    required this.onDelete,
  });

  final Crop crop;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: const Icon(Icons.eco_outlined, color: AppTheme.primaryGreen),
        title: Text(crop.cropName),
        subtitle: Text(
          '${crop.season} • ${crop.durationDays} दिन\n'
          '${AppStrings.waterRequirementLabel}: ${crop.waterRequirement}',
        ),
        isThreeLine: true,
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              tooltip: AppStrings.editCropButton,
              icon: const Icon(Icons.edit_outlined),
              onPressed: onEdit,
            ),
            IconButton(
              tooltip: AppStrings.delete,
              icon: const Icon(Icons.delete_outline),
              onPressed: onDelete,
            ),
          ],
        ),
      ),
    );
  }
}

// ==========================================================
// Shared farm form fields
// ==========================================================

class _FarmDraft {
  const _FarmDraft({
    required this.village,
    required this.district,
    required this.state,
    this.farmSize,
  });

  factory _FarmDraft.from(Farmer farm) => _FarmDraft(
        village: farm.village,
        district: farm.district,
        state: farm.state,
        farmSize: farm.farmSize,
      );

  final String village;
  final String district;
  final String state;
  final double? farmSize;
}

class _FarmFormFields extends StatefulWidget {
  const _FarmFormFields({super.key, this.initial});

  final _FarmDraft? initial;

  @override
  State<_FarmFormFields> createState() => _FarmFormFieldsState();
}

class _FarmFormFieldsState extends State<_FarmFormFields> {
  late final TextEditingController _village =
      TextEditingController(text: widget.initial?.village ?? '');
  late final TextEditingController _district =
      TextEditingController(text: widget.initial?.district ?? '');
  late final TextEditingController _state =
      TextEditingController(text: widget.initial?.state ?? '');
  late final TextEditingController _farmSize = TextEditingController(
    text: widget.initial?.farmSize == null
        ? ''
        : _formatNumber(widget.initial!.farmSize!),
  );

  String get village => _village.text.trim();
  String get district => _district.text.trim();
  String get state => _state.text.trim();
  double? get farmSize {
    final text = _farmSize.text.trim();
    if (text.isEmpty) return null;
    return double.tryParse(text);
  }

  @override
  void dispose() {
    _village.dispose();
    _district.dispose();
    _state.dispose();
    _farmSize.dispose();
    super.dispose();
  }

  String? _validateFarmSize(String? value) {
    final text = (value ?? '').trim();
    if (text.isEmpty) return null;
    final parsed = double.tryParse(text);
    if (parsed == null || parsed < 0) return AppStrings.farmSizeInvalid;
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextFormField(
          controller: _village,
          textInputAction: TextInputAction.next,
          decoration: const InputDecoration(
            labelText: AppStrings.villageLabel,
            prefixIcon: Icon(Icons.location_on_outlined),
          ),
          validator: (value) => (value == null || value.trim().isEmpty)
              ? AppStrings.villageRequired
              : null,
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _district,
          textInputAction: TextInputAction.next,
          decoration: const InputDecoration(
            labelText: AppStrings.districtLabel,
            prefixIcon: Icon(Icons.map_outlined),
          ),
          validator: (value) => (value == null || value.trim().isEmpty)
              ? AppStrings.districtRequired
              : null,
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _state,
          textInputAction: TextInputAction.next,
          decoration: const InputDecoration(
            labelText: AppStrings.stateLabel,
            prefixIcon: Icon(Icons.public),
          ),
          validator: (value) => (value == null || value.trim().isEmpty)
              ? AppStrings.stateRequired
              : null,
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _farmSize,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          textInputAction: TextInputAction.done,
          decoration: const InputDecoration(
            labelText: AppStrings.farmSizeLabel,
            hintText: AppStrings.farmSizeHint,
            prefixIcon: Icon(Icons.straighten),
          ),
          validator: _validateFarmSize,
        ),
      ],
    );
  }
}

/// Modal bottom sheet wrapping [_FarmFormFields] for editing an existing farm.
class _FarmFormSheet extends StatefulWidget {
  const _FarmFormSheet({this.initial});

  final _FarmDraft? initial;

  static Future<_FarmDraft?> show(BuildContext context, {_FarmDraft? initial}) {
    return showModalBottomSheet<_FarmDraft>(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: _FarmFormSheet(initial: initial),
      ),
    );
  }

  @override
  State<_FarmFormSheet> createState() => _FarmFormSheetState();
}

class _FarmFormSheetState extends State<_FarmFormSheet> {
  final _formKey = GlobalKey<FormState>();
  final _fieldsKey = GlobalKey<_FarmFormFieldsState>();

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    final fields = _fieldsKey.currentState!;
    Navigator.of(context).pop(
      _FarmDraft(
        village: fields.village,
        district: fields.district,
        state: fields.state,
        farmSize: fields.farmSize,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  AppStrings.editFarmButton,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 16),
                _FarmFormFields(key: _fieldsKey, initial: widget.initial),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _save,
                  icon: const Icon(Icons.check),
                  label: const Text(AppStrings.updateFarmButton),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ==========================================================
// Crop form sheet
// ==========================================================

class _CropDraft {
  const _CropDraft({
    required this.cropName,
    required this.season,
    required this.durationDays,
    required this.waterRequirement,
  });

  factory _CropDraft.from(Crop crop) => _CropDraft(
        cropName: crop.cropName,
        season: crop.season,
        durationDays: crop.durationDays,
        waterRequirement: crop.waterRequirement,
      );

  final String cropName;
  final String season;
  final int durationDays;
  final String waterRequirement;
}

/// Modal bottom sheet with the crop add/edit form.
class _CropFormSheet extends StatefulWidget {
  const _CropFormSheet({this.initial});

  final _CropDraft? initial;

  static Future<_CropDraft?> show(BuildContext context, {_CropDraft? initial}) {
    return showModalBottomSheet<_CropDraft>(
      context: context,
      isScrollControlled: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: _CropFormSheet(initial: initial),
      ),
    );
  }

  @override
  State<_CropFormSheet> createState() => _CropFormSheetState();
}

class _CropFormSheetState extends State<_CropFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _cropName =
      TextEditingController(text: widget.initial?.cropName ?? '');
  late final TextEditingController _season =
      TextEditingController(text: widget.initial?.season ?? '');
  late final TextEditingController _durationDays = TextEditingController(
    text: widget.initial == null ? '' : '${widget.initial!.durationDays}',
  );
  late final TextEditingController _waterRequirement =
      TextEditingController(text: widget.initial?.waterRequirement ?? '');

  @override
  void dispose() {
    _cropName.dispose();
    _season.dispose();
    _durationDays.dispose();
    _waterRequirement.dispose();
    super.dispose();
  }

  String? _validateDuration(String? value) {
    final parsed = int.tryParse((value ?? '').trim());
    if (parsed == null || parsed <= 0) return AppStrings.durationDaysInvalid;
    return null;
  }

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.of(context).pop(
      _CropDraft(
        cropName: _cropName.text.trim(),
        season: _season.text.trim(),
        durationDays: int.parse(_durationDays.text.trim()),
        waterRequirement: _waterRequirement.text.trim(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  widget.initial == null
                      ? AppStrings.addCropButton
                      : AppStrings.editCropButton,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _cropName,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: AppStrings.cropNameLabel,
                    prefixIcon: Icon(Icons.eco_outlined),
                  ),
                  validator: (value) =>
                      (value == null || value.trim().isEmpty)
                          ? AppStrings.cropNameRequired
                          : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _season,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: AppStrings.seasonLabel,
                    prefixIcon: Icon(Icons.calendar_month_outlined),
                  ),
                  validator: (value) =>
                      (value == null || value.trim().isEmpty)
                          ? AppStrings.seasonRequired
                          : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _durationDays,
                  keyboardType: TextInputType.number,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: AppStrings.durationDaysLabel,
                    prefixIcon: Icon(Icons.timer_outlined),
                  ),
                  validator: _validateDuration,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _waterRequirement,
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _save(),
                  decoration: const InputDecoration(
                    labelText: AppStrings.waterRequirementLabel,
                    prefixIcon: Icon(Icons.water_drop_outlined),
                  ),
                  validator: (value) =>
                      (value == null || value.trim().isEmpty)
                          ? AppStrings.waterRequirementRequired
                          : null,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _save,
                  icon: const Icon(Icons.check),
                  label: const Text(AppStrings.saveCropButton),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

