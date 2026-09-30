import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/common_views.dart';
import '../../models/prediction.dart';
import 'predictions_controller.dart';

/// AI भविष्यवाणी — collects verified crop/soil/weather context and calls
/// the prediction engine.
class PredictionsScreen extends StatefulWidget {
  const PredictionsScreen({super.key});

  @override
  State<PredictionsScreen> createState() => _PredictionsScreenState();
}

class _PredictionsScreenState extends State<PredictionsScreen> {
  final _cropController = TextEditingController();
  final _soilTypeController = TextEditingController();
  final _phController = TextEditingController();
  final _moistureController = TextEditingController();
  final _nitrogenController = TextEditingController();
  final _phosphorusController = TextEditingController();
  final _potassiumController = TextEditingController();
  final _temperatureController = TextEditingController();
  final _humidityController = TextEditingController();
  final _conditionController = TextEditingController();
  final _windSpeedController = TextEditingController();
  String _predictionType = PredictionInput.typeCropYield;

  @override
  void dispose() {
    _cropController.dispose();
    _soilTypeController.dispose();
    _phController.dispose();
    _moistureController.dispose();
    _nitrogenController.dispose();
    _phosphorusController.dispose();
    _potassiumController.dispose();
    _temperatureController.dispose();
    _humidityController.dispose();
    _conditionController.dispose();
    _windSpeedController.dispose();
    super.dispose();
  }

  PredictionInput? _readInput() {
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

    final double? windSpeed = _doubleOrNull(_windSpeedController.text);
    if (windSpeed != null && windSpeed < 0) {
      _showRangeError(AppStrings.windSpeedRangeError);
      return null;
    }

    final PredictionSoilContext soil = PredictionSoilContext(
      soilType: _soilTypeController.text.trim().isEmpty
          ? null
          : _soilTypeController.text.trim(),
      ph: ph,
      moisture: moisture,
      nitrogen: _intOrNull(_nitrogenController.text),
      phosphorus: _intOrNull(_phosphorusController.text),
      potassium: _intOrNull(_potassiumController.text),
    );
    final PredictionWeatherContext weather = PredictionWeatherContext(
      temperature: _doubleOrNull(_temperatureController.text),
      humidity: humidity,
      condition: _conditionController.text.trim().isEmpty
          ? null
          : _conditionController.text.trim(),
      windSpeed: windSpeed,
    );

    return PredictionInput(
      predictionType: _predictionType,
      cropName: cropName,
      soil: soil,
      weather: weather,
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
    await context.read<PredictionsController>().submit(input);
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<PredictionsController>();
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.predictionsTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const SectionHeader(
            title: AppStrings.predictionsTitle,
            subtitle: AppStrings.predictionsSubtitle,
          ),
          DropdownButtonFormField<String>(
            initialValue: _predictionType,
            decoration:
                const InputDecoration(labelText: AppStrings.predictionTypeLabel),
            items: const [
              DropdownMenuItem(
                value: PredictionInput.typeCropYield,
                child: Text(AppStrings.cropYieldLabel),
              ),
              DropdownMenuItem(
                value: PredictionInput.typeSoilAnalysis,
                child: Text(AppStrings.soilAnalysisLabel),
              ),
            ],
            onChanged: (value) =>
                setState(() => _predictionType = value ?? _predictionType),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _cropController,
            decoration: const InputDecoration(
              labelText: AppStrings.cropField,
              prefixIcon: Icon(Icons.grass),
            ),
          ),
          const SizedBox(height: 12),
          const SectionHeader(title: 'मिट्टी (वैकल्पिक)'),
          TextField(
            controller: _soilTypeController,
            decoration: const InputDecoration(labelText: AppStrings.soilTypeField),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _phController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration:
                      const InputDecoration(labelText: AppStrings.phField),
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
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _conditionController,
                  decoration:
                      const InputDecoration(labelText: AppStrings.conditionLabel),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _windSpeedController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: AppStrings.windLabel),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: controller.state == PredictionState.loading
                ? null
                : () => _submit(context),
            icon: const Icon(Icons.trending_up),
            label: Text(controller.state == PredictionState.loading
                ? AppStrings.loadingPredictions
                : AppStrings.getPredictions),
          ),
          const SizedBox(height: 24),
          _buildResult(context, controller),
        ],
      ),
    );
  }

  Widget _buildResult(BuildContext context, PredictionsController controller) {
    switch (controller.state) {
      case PredictionState.loading:
        return const LoadingView(label: AppStrings.loadingPredictions);
      case PredictionState.error:
        return ErrorView(message: controller.errorMessage);
      case PredictionState.idle:
        return const SizedBox.shrink();
      case PredictionState.success:
        final result = controller.result;
        if (result == null) return const SizedBox.shrink();
        return _PredictionResultView(result: result);
    }
  }
}

class _PredictionResultView extends StatelessWidget {
  const _PredictionResultView({required this.result});

  final PredictionResult result;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // A "no model configured" backend response must never be shown as a
    // real prediction.
    if (result.isModelNotConfigured) {
      return _InfoCard(
        icon: Icons.info_outline,
        color: Colors.blueGrey,
        title: AppStrings.modelNotConfigured,
        hint: result.message ?? '',
      );
    }
    if (result.result == null) {
      return const _InfoCard(
        icon: Icons.inbox_outlined,
        color: Colors.grey,
        title: AppStrings.noPrediction,
        hint: '',
      );
    }

    final entries = result.result!.entries.toList()..sort((a, b) {
        final ai = a.key.toLowerCase();
        final bi = b.key.toLowerCase();
        return ai.compareTo(bi);
      });

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              AppStrings.predictionAvailable,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
                color: theme.colorScheme.primary,
              ),
            ),
            const SizedBox(height: 8),
            for (final entry in entries)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('${entry.key}: ${entry.value}'),
              ),
            if (result.confidence != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  '${AppStrings.confidenceLabel}: '
                  '${(result.confidence! * 100).toStringAsFixed(0)}%',
                  style: theme.textTheme.bodySmall,
                ),
              ),
            if (result.model != null && result.model!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  '${AppStrings.modelLabel}: ${result.model}',
                  style: theme.textTheme.bodySmall,
                ),
              ),
          ],
        ),
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