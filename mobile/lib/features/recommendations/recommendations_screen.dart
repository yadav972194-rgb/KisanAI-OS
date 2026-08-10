import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/common_views.dart';
import '../../models/recommendation.dart';
import 'recommendations_controller.dart';

/// AI सलाह — collects verified context and calls the recommendation engine.
class RecommendationsScreen extends StatefulWidget {
  const RecommendationsScreen({super.key});

  @override
  State<RecommendationsScreen> createState() => _RecommendationsScreenState();
}

class _RecommendationsScreenState extends State<RecommendationsScreen> {
  final _cropController = TextEditingController();
  final _phController = TextEditingController();
  final _moistureController = TextEditingController();
  final _nitrogenController = TextEditingController();
  final _phosphorusController = TextEditingController();
  final _potassiumController = TextEditingController();
  final _temperatureController = TextEditingController();
  final _humidityController = TextEditingController();
  final _diseaseNameController = TextEditingController();
  String? _severity;

  @override
  void dispose() {
    _cropController.dispose();
    _phController.dispose();
    _moistureController.dispose();
    _nitrogenController.dispose();
    _phosphorusController.dispose();
    _potassiumController.dispose();
    _temperatureController.dispose();
    _humidityController.dispose();
    _diseaseNameController.dispose();
    super.dispose();
  }

  RecommendationInput? _readInput() {
    final cropName = _cropController.text.trim();
    if (cropName.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text(AppStrings.cropNameEmptyError)),
      );
      return null;
    }

    final double? ph = _doubleOrNull(_phController.text);
    if (ph != null && (ph < 0 || ph > 14)) {
      _showRangeError(AppStrings.phRangeError);
      return null;
    }
    final double? moisture = _doubleOrNull(_moistureController.text);
    if (moisture != null && (moisture < 0 || moisture > 100)) {
      _showRangeError(AppStrings.moistureRangeError);
      return null;
    }

    final int? humidity = _intOrNull(_humidityController.text);
    if (humidity != null && (humidity < 0 || humidity > 100)) {
      _showRangeError(AppStrings.moistureRangeError);
      return null;
    }

    return RecommendationInput(
      cropName: cropName,
      ph: ph,
      moisture: moisture,
      nitrogen: _intOrNull(_nitrogenController.text),
      phosphorus: _intOrNull(_phosphorusController.text),
      potassium: _intOrNull(_potassiumController.text),
      temperature: _doubleOrNull(_temperatureController.text),
      humidity: humidity,
      diseaseName: _diseaseNameController.text.trim().isEmpty
          ? null
          : _diseaseNameController.text.trim(),
      severity: _severity,
    );
  }

  double? _doubleOrNull(String text) {
    final value = double.tryParse(text.trim());
    return value;
  }

  int? _intOrNull(String text) => int.tryParse(text.trim());

  void _showRangeError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _submit(BuildContext context) async {
    final input = _readInput();
    if (input == null) return;
    FocusScope.of(context).unfocus();
    await context.read<RecommendationsController>().submit(input);
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<RecommendationsController>();
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.recommendationsTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const SectionHeader(
            title: AppStrings.recommendationsTitle,
            subtitle: AppStrings.recommendationsSubtitle,
          ),
          TextField(
            controller: _cropController,
            decoration: const InputDecoration(
              labelText: AppStrings.cropField,
              prefixIcon: Icon(Icons.grass),
            ),
          ),
          const SizedBox(height: 12),
          const SectionHeader(title: 'मिट्टी (वैकल्पिक)'),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _phController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: AppStrings.phField),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _moistureController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration:
                      const InputDecoration(labelText: AppStrings.moistureField),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _nitrogenController,
                  keyboardType: TextInputType.number,
                  decoration:
                      const InputDecoration(labelText: AppStrings.nitrogenField),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _phosphorusController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: AppStrings.phosphorusField),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _potassiumController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: AppStrings.potassiumField),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const SectionHeader(title: 'मौसम (वैकल्पिक)'),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _temperatureController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration:
                      const InputDecoration(labelText: AppStrings.temperatureField),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _humidityController,
                  keyboardType: TextInputType.number,
                  decoration:
                      const InputDecoration(labelText: AppStrings.humidityField),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const SectionHeader(title: 'रोग (वैकल्पिक)'),
          TextField(
            controller: _diseaseNameController,
            decoration:
                const InputDecoration(labelText: AppStrings.diseaseNameField),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _severity,
            decoration: const InputDecoration(labelText: AppStrings.severityField),
            items: const [
              DropdownMenuItem(value: 'Low', child: Text(AppStrings.severityLow)),
              DropdownMenuItem(
                  value: 'Medium', child: Text(AppStrings.severityMedium)),
              DropdownMenuItem(
                  value: 'High', child: Text(AppStrings.severityHigh)),
            ],
            onChanged: (value) => setState(() => _severity = value),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: controller.state == RecommendationState.loading
                ? null
                : () => _submit(context),
            icon: const Icon(Icons.auto_awesome),
            label: Text(controller.state == RecommendationState.loading
                ? AppStrings.loadingRecommendations
                : AppStrings.getRecommendations),
          ),
          const SizedBox(height: 24),
          _buildResult(context, controller),
        ],
      ),
    );
  }

  Widget _buildResult(BuildContext context, RecommendationsController controller) {
    switch (controller.state) {
      case RecommendationState.loading:
        return const LoadingView(label: AppStrings.loadingRecommendations);
      case RecommendationState.error:
        return ErrorView(message: controller.errorMessage);
      case RecommendationState.idle:
        return const SizedBox.shrink();
      case RecommendationState.success:
        final result = controller.result;
        if (result == null) return const SizedBox.shrink();
        return _RecommendationResultView(result: result);
    }
  }
}

class _RecommendationResultView extends StatelessWidget {
  const _RecommendationResultView({required this.result});

  final RecommendationResult result;

  @override
  Widget build(BuildContext context) {
    if (result.isInsufficientData) {
      return const _InfoCard(
        icon: Icons.help_outline,
        color: Colors.orange,
        title: AppStrings.insufficientData,
        hint: AppStrings.insufficientDataHint,
      );
    }
    if (result.isModelNotConfigured) {
      return _InfoCard(
        icon: Icons.info_outline,
        color: Colors.blueGrey,
        title: AppStrings.modelNotConfigured,
        hint: result.message ?? '',
      );
    }
    if (result.isProviderUnavailable) {
      return _InfoCard(
        icon: Icons.cloud_off_outlined,
        color: Colors.orange,
        title: 'सेवा अनुपलब्ध',
        hint: result.message ?? '',
      );
    }
    if (result.recommendations.isEmpty) {
      return const _InfoCard(
        icon: Icons.inbox_outlined,
        color: Colors.grey,
        title: AppStrings.noRecommendations,
        hint: '',
      );
    }

    final theme = Theme.of(context);
    final grouped = <String, List<RecommendationItem>>{};
    for (final item in result.recommendations) {
      grouped.putIfAbsent(item.category, () => []).add(item);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          AppStrings.recommendationAvailable,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
            color: theme.colorScheme.primary,
          ),
        ),
        const SizedBox(height: 8),
        for (final entry in grouped.entries) ...[
          SectionHeader(title: entry.key),
          for (final item in entry.value) _RecommendationTile(item: item),
        ],
        if (result.warnings.isNotEmpty) ...[
          const SizedBox(height: 8),
          const SectionHeader(title: AppStrings.warningsLabel),
          for (final warning in result.warnings) _WarningChip(text: warning),
        ],
        if (result.confidence != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              '${AppStrings.confidenceLabel}: '
              '${(result.confidence! * 100).toStringAsFixed(0)}%',
              style: theme.textTheme.bodySmall,
            ),
          ),
      ],
    );
  }
}

class _RecommendationTile extends StatelessWidget {
  const _RecommendationTile({required this.item});

  final RecommendationItem item;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item.text),
            if (item.reason != null && item.reason!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                '${AppStrings.reasonLabel}: ${item.reason}',
                style: theme.textTheme.bodySmall
                    ?.copyWith(color: theme.colorScheme.outline),
              ),
            ],
            if (item.source != null && item.source!.isNotEmpty) ...[
              const SizedBox(height: 2),
              Text(
                '${AppStrings.sourceLabel}: ${item.source}',
                style: theme.textTheme.bodySmall
                    ?.copyWith(color: theme.colorScheme.outline),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _WarningChip extends StatelessWidget {
  const _WarningChip({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8E1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber, size: 18, color: Colors.orange),
          const SizedBox(width: 8),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.icon,
    required this.color,
    required this.title,
    required this.hint,
  });

  final IconData icon;
  final Color color;
  final String title;
  final String hint;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      color: color.withValues(alpha: 0.08),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, size: 40, color: color),
            const SizedBox(height: 8),
            Text(
              title,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
                color: color,
              ),
            ),
            if (hint.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(hint, textAlign: TextAlign.center),
            ],
          ],
        ),
      ),
    );
  }
}
