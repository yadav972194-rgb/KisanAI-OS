import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/common_views.dart';
import '../../models/weather.dart';
import 'weather_controller.dart';

/// Live weather from the real `/api/weather` endpoint.
class WeatherScreen extends StatefulWidget {
  const WeatherScreen({super.key});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<WeatherController>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<WeatherController>();
    return Scaffold(
      appBar: AppBar(
        title: const Text(AppStrings.weatherTitle),
        actions: [
          IconButton(
            tooltip: AppStrings.refreshWeather,
            icon: const Icon(Icons.refresh),
            onPressed: controller.isLoading ? null : controller.load,
          ),
        ],
      ),
      body: _buildBody(context, controller),
    );
  }

  Widget _buildBody(BuildContext context, WeatherController controller) {
    if (controller.isLoading && controller.weather == null) {
      return const LoadingView();
    }
    if (controller.errorMessage != null) {
      return ErrorView(
        message: controller.errorMessage,
        onRetry: controller.load,
      );
    }
    final weather = controller.weather;
    if (weather == null) {
      return ErrorView(message: AppStrings.genericError, onRetry: controller.load);
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _WeatherHero(weather: weather),
        const SizedBox(height: 16),
        Row(
          children: [
            _MetricCard(
              icon: Icons.thermostat,
              label: AppStrings.temperatureLabel,
              value: '${weather.temperature.toStringAsFixed(1)}°C',
            ),
            const SizedBox(width: 12),
            _MetricCard(
              icon: Icons.water_drop_outlined,
              label: AppStrings.humidityLabel,
              value: '${weather.humidity}%',
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            _MetricCard(
              icon: Icons.air,
              label: AppStrings.windLabel,
              value: '${weather.windSpeed.toStringAsFixed(1)} km/h',
            ),
            const SizedBox(width: 12),
            _MetricCard(
              icon: Icons.cloud_outlined,
              label: AppStrings.conditionLabel,
              value: weather.condition,
            ),
          ],
        ),
        const SizedBox(height: 16),
        Center(
          child: Text(
            '${AppStrings.updatedLabel}: ${weather.updatedAt}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ),
      ],
    );
  }
}

class _WeatherHero extends StatelessWidget {
  const _WeatherHero({required this.weather});

  final Weather weather;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2E7D32), Color(0xFF66BB6A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          const Icon(Icons.wb_sunny, size: 56, color: Colors.white),
          const SizedBox(height: 8),
          Text(
            '${weather.temperature.toStringAsFixed(1)}°C',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 44,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            weather.condition,
            style: const TextStyle(color: Colors.white, fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(
            weather.location,
            style: theme.textTheme.bodySmall?.copyWith(color: Colors.white70),
          ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 6),
              Text(label, style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 2),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
