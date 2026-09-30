import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/errors/api_exception.dart';
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
      block: draft.block,
      country: draft.country,
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
    final fields = _fieldsKey.currentState!;
    final fieldsValid = _formKey.currentState!.validate();
    final locationsValid = fields.validateLocations();
    if (!fieldsValid || !locationsValid) return;
    FocusScope.of(context).unfocus();
    final ok = await widget.controller.createFarm(
      village: fields.village,
      district: fields.district,
      state: fields.state,
      block: fields.block,
      country: fields.country,
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
                    label: AppStrings.villageLabel,
                    value: farm.village,
                  ),
                  _InfoRow(
                    label: AppStrings.tehsilLabel,
                    value: (farm.block == null || farm.block!.isEmpty)
                        ? '—'
                        : farm.block!,
                  ),
                  _InfoRow(
                      label: AppStrings.districtLabel, value: farm.district),
                  _InfoRow(label: AppStrings.stateLabel, value: farm.state),
                  _InfoRow(
                    label: AppStrings.countryLabel,
                    value: farm.country ?? 'India',
                  ),
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
    required this.block,
    this.country,
    this.farmSize,
  });

  factory _FarmDraft.from(Farmer farm) => _FarmDraft(
        village: farm.village,
        district: farm.district,
        state: farm.state,
        block: farm.block ?? '',
        country: farm.country,
        farmSize: farm.farmSize,
      );

  final String village;
  final String district;
  final String state;
  final String block;
  final String? country;
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
  late final TextEditingController _farmSize = TextEditingController(
    text: widget.initial?.farmSize == null
        ? ''
        : _formatNumber(widget.initial!.farmSize!),
  );

  final List<String> _countries = [];
  final List<String> _states = [];
  List<String> _districts = [];
  List<String> _blocks = [];
  List<String> _villages = [];

  String? _selectedCountry;
  String? _selectedState;
  String? _selectedDistrict;
  String? _selectedBlock;
  String? _selectedVillage;

  bool _loadingCountries = true;
  bool _loadingStates = false;
  bool _loadingDistricts = false;
  bool _loadingBlocks = false;
  bool _loadingVillages = false;
  bool _countriesFailed = false;
  bool _statesFailed = false;
  bool _districtsFailed = false;
  bool _blocksFailed = false;
  bool _villagesFailed = false;

  String? _countryError;
  String? _stateError;
  String? _districtError;
  String? _tehsilError;
  String? _villageError;

  bool _initialized = false;

  AppDependencies get _deps => context.read<AppDependencies>();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initialized) return;
    _initialized = true;
    _selectedCountry = _nonEmpty(widget.initial?.country);
    _selectedState = _nonEmpty(widget.initial?.state);
    _selectedDistrict = _nonEmpty(widget.initial?.district);
    _selectedBlock = _nonEmpty(widget.initial?.block);
    _loadingStates = _selectedCountry != null;
    if (_selectedState != null) _loadingDistricts = true;
    if (_selectedState != null && _selectedDistrict != null) {
      _loadingBlocks = true;
    }
    _loadCountries();
  }

  String get village => _selectedVillage ?? _village.text.trim();
  String get district => _selectedDistrict ?? '';
  String get state => _selectedState ?? '';
  String get block => _selectedBlock ?? '';
  String get country => _selectedCountry ?? '';

  double? get farmSize {
    final text = _farmSize.text.trim();
    if (text.isEmpty) return null;
    return double.tryParse(text);
  }

  /// Validates the cascading dropdowns (the `Form` only knows about the text
  /// fields); returns true when country, state, district, tehsil and village
  /// are all chosen.
  bool validateLocations() {
    setState(() {
      _countryError = _selectedCountry == null ? AppStrings.countryRequired : null;
      _stateError = _selectedState == null ? AppStrings.stateRequired : null;
      _districtError =
          _selectedDistrict == null ? AppStrings.districtRequired : null;
      _tehsilError = _selectedBlock == null ? AppStrings.tehsilRequired : null;
      _villageError = village.isEmpty ? AppStrings.villageRequired : null;
    });
    return _countryError == null &&
        _stateError == null &&
        _districtError == null &&
        _tehsilError == null &&
        _villageError == null;
  }

  @override
  void dispose() {
    _village.dispose();
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

  Future<void> _loadCountries() async {
    setState(() {
      _loadingCountries = true;
      _countriesFailed = false;
    });
    try {
      final countries = await _deps.locationApi.fetchCountries();
      if (!mounted) return;
      setState(() {
        _countries
          ..clear()
          ..addAll(countries);
        _loadingCountries = false;
      });
      if (_selectedCountry != null) await _loadStates();
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _loadingCountries = false;
        _countriesFailed = true;
      });
    }
  }

  Future<void> _loadStates() async {
    setState(() {
      _loadingStates = true;
      _statesFailed = false;
    });
    try {
      final states = await _deps.locationApi.fetchStates();
      if (!mounted) return;
      setState(() {
        _states
          ..clear()
          ..addAll(states);
        _loadingStates = false;
      });
      if (_selectedState != null) await _loadDistricts();
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _loadingStates = false;
        _statesFailed = true;
      });
    }
  }

  Future<void> _loadDistricts() async {
    final state = _selectedState;
    if (state == null) return;
    setState(() {
      _loadingDistricts = true;
      _districtsFailed = false;
    });
    try {
      final districts = await _deps.locationApi.fetchDistricts(state);
      if (!mounted) return;
      setState(() {
        _districts
          ..clear()
          ..addAll(districts);
        _loadingDistricts = false;
      });
      if (_selectedDistrict != null) await _loadBlocks();
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _loadingDistricts = false;
        _districtsFailed = true;
      });
    }
  }

  Future<void> _loadBlocks() async {
    final district = _selectedDistrict;
    if (district == null) return;
    setState(() {
      _loadingBlocks = true;
      _blocksFailed = false;
    });
    try {
      final blocks = await _deps.locationApi.fetchBlocks(district);
      if (!mounted) return;
      setState(() {
        _blocks
          ..clear()
          ..addAll(blocks);
        _loadingBlocks = false;
      });
      if (_selectedBlock != null) await _loadVillages();
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _loadingBlocks = false;
        _blocksFailed = true;
      });
    }
  }

  Future<void> _loadVillages() async {
    final tehsil = _selectedBlock;
    if (tehsil == null) return;
    setState(() {
      _loadingVillages = true;
      _villagesFailed = false;
    });
    try {
      final villages = await _deps.locationApi.fetchVillages(tehsil);
      if (!mounted) return;
      // Prefill the dropdown from a matching free-text village on edit.
      String? match;
      final typed = _village.text.trim();
      if (typed.isNotEmpty && villages.contains(typed)) match = typed;
      setState(() {
        _villages
          ..clear()
          ..addAll(villages);
        _loadingVillages = false;
        if (match != null) {
          _selectedVillage = match;
          _village.clear();
        }
      });
    } on ApiException {
      if (!mounted) return;
      setState(() {
        _loadingVillages = false;
        _villagesFailed = true;
      });
    }
  }

  void _selectCountry(String? country) {
    setState(() {
      _selectedCountry = country;
      _selectedState = null;
      _selectedDistrict = null;
      _selectedBlock = null;
      _selectedVillage = null;
      _village.clear();
      _states.clear();
      _districts = [];
      _blocks = [];
      _villages = [];
      _loadingStates = country != null;
      _loadingDistricts = false;
      _loadingBlocks = false;
      _loadingVillages = false;
      _statesFailed = false;
      _districtsFailed = false;
      _blocksFailed = false;
      _villagesFailed = false;
      _countryError = null;
      _stateError = null;
      _districtError = null;
      _tehsilError = null;
      _villageError = null;
    });
    if (country != null) _loadStates();
  }

  void _selectState(String? state) {
    setState(() {
      _selectedState = state;
      _selectedDistrict = null;
      _selectedBlock = null;
      _selectedVillage = null;
      _village.clear();
      _districts = [];
      _blocks = [];
      _villages = [];
      _loadingDistricts = state != null;
      _loadingBlocks = false;
      _loadingVillages = false;
      _districtsFailed = false;
      _blocksFailed = false;
      _villagesFailed = false;
      _stateError = null;
      _districtError = null;
      _tehsilError = null;
      _villageError = null;
    });
    if (state != null) _loadDistricts();
  }

  void _selectDistrict(String? district) {
    setState(() {
      _selectedDistrict = district;
      _selectedBlock = null;
      _selectedVillage = null;
      _village.clear();
      _blocks = [];
      _villages = [];
      _loadingBlocks = district != null;
      _loadingVillages = false;
      _blocksFailed = false;
      _villagesFailed = false;
      _districtError = null;
      _tehsilError = null;
      _villageError = null;
    });
    if (district != null) _loadBlocks();
  }

  void _selectBlock(String? block) {
    setState(() {
      _selectedBlock = block;
      _selectedVillage = null;
      _village.clear();
      _villages = [];
      _loadingVillages = block != null;
      _villagesFailed = false;
      _tehsilError = null;
      _villageError = null;
    });
    if (block != null) _loadVillages();
  }

  void _selectVillage(String? village) {
    setState(() {
      _selectedVillage = village;
      _villageError = null;
      _village.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final showVillageDropdown =
        _loadingVillages || _villagesFailed || _villages.isNotEmpty;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (_countriesFailed)
          _LocationLoadError(onRetry: _loadCountries)
        else
          _LocationDropdown(
            label: AppStrings.countryLabel,
            icon: Icons.public,
            placeholder: AppStrings.selectCountryHint,
            options: _countries,
            value: _selectedCountry,
            loading: _loadingCountries,
            onSelected: _selectCountry,
            errorText: _countryError,
          ),
        const SizedBox(height: 16),
        if (_statesFailed)
          _LocationLoadError(onRetry: _loadStates)
        else
          _LocationDropdown(
            label: AppStrings.stateLabel,
            icon: Icons.map_outlined,
            placeholder: AppStrings.selectStateHint,
            options: _states,
            value: _selectedState,
            enabled: _selectedCountry != null,
            loading: _loadingStates,
            onSelected: _selectState,
            errorText: _stateError,
          ),
        const SizedBox(height: 16),
        if (_districtsFailed)
          _LocationLoadError(onRetry: _loadDistricts)
        else
          _LocationDropdown(
            label: AppStrings.districtLabel,
            icon: Icons.map_outlined,
            placeholder: AppStrings.selectDistrictHint,
            options: _districts,
            value: _selectedDistrict,
            enabled: _selectedState != null,
            loading: _loadingDistricts,
            onSelected: _selectDistrict,
            errorText: _districtError,
          ),
        const SizedBox(height: 16),
        if (_blocksFailed)
          _LocationLoadError(onRetry: _loadBlocks)
        else
          _LocationDropdown(
            label: AppStrings.tehsilLabel,
            icon: Icons.location_city_outlined,
            placeholder: AppStrings.selectTehsilHint,
            options: _blocks,
            value: _selectedBlock,
            enabled: _selectedDistrict != null,
            loading: _loadingBlocks,
            onSelected: _selectBlock,
            errorText: _tehsilError,
          ),
        const SizedBox(height: 16),
        if (showVillageDropdown)
          if (_villagesFailed)
            _LocationLoadError(onRetry: _loadVillages)
          else
            _LocationDropdown(
              label: AppStrings.villageLabel,
              icon: Icons.location_on_outlined,
              placeholder: AppStrings.selectVillageHint,
              options: _villages,
              value: _selectedVillage,
              enabled: _selectedBlock != null,
              loading: _loadingVillages,
              onSelected: _selectVillage,
              errorText: _villageError,
            )
        else
          TextFormField(
            controller: _village,
            enabled: _selectedBlock != null,
            textInputAction: TextInputAction.next,
            onChanged: (_) => setState(() => _villageError = null),
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

String? _nonEmpty(String? value) {
  if (value == null) return null;
  final trimmed = value.trim();
  return trimmed.isEmpty ? null : trimmed;
}

/// A labelled dropdown for one level of the location hierarchy.
///
/// Fully controlled: [value] only renders when present in [options] so a
/// not-yet-loaded selection never causes a dropdown assertion, and it is
/// disabled while loading, when disabled by a missing parent, or when there
/// are no options to choose from.
class _LocationDropdown extends StatelessWidget {
  const _LocationDropdown({
    required this.label,
    required this.icon,
    required this.placeholder,
    required this.options,
    required this.value,
    required this.onSelected,
    this.enabled = true,
    this.loading = false,
    this.errorText,
  });

  final String label;
  final IconData icon;
  final String placeholder;
  final List<String> options;
  final String? value;
  final bool enabled;
  final bool loading;
  final ValueChanged<String?> onSelected;
  final String? errorText;

  @override
  Widget build(BuildContext context) {
    final isDisabled = !enabled || loading || options.isEmpty;
    final hint = !enabled
        ? placeholder
        : (loading
            ? AppStrings.loading
            : (options.isEmpty ? AppStrings.noOptionsAvailable : placeholder));
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        errorText: errorText,
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: options.contains(value) ? value : null,
          isExpanded: true,
          hint: Text(hint),
          items: [
            for (final option in options)
              DropdownMenuItem(value: option, child: Text(option)),
          ],
          onChanged:
              isDisabled ? null : (selected) => onSelected(selected),
        ),
      ),
    );
  }
}

/// Inline error + retry shown when one level of the location hierarchy fails
/// to load.
class _LocationLoadError extends StatelessWidget {
  const _LocationLoadError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          AppStrings.locationsLoadError,
          style: theme.textTheme.bodyMedium
              ?.copyWith(color: theme.colorScheme.error),
        ),
        const SizedBox(height: 4),
        Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text(AppStrings.retry),
          ),
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
    final fields = _fieldsKey.currentState!;
    final fieldsValid = _formKey.currentState!.validate();
    final locationsValid = fields.validateLocations();
    if (!fieldsValid || !locationsValid) return;
    Navigator.of(context).pop(
      _FarmDraft(
        village: fields.village,
        district: fields.district,
        state: fields.state,
        block: fields.block,
        country: fields.country,
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

