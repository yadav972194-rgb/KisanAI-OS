import 'package:flutter/material.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../diagnosis/diagnosis_screen.dart';
import '../detection/growth_stage_screen.dart';
import '../detection/nutrient_deficiency_screen.dart';
import '../detection/pest_screen.dart';
import '../detection/water_stress_screen.dart';
import '../detection/weed_screen.dart';

/// Entry point for the crop-health diagnosis suite.
///
/// Lists every image-based detector: disease (existing) plus pest, weed,
/// nutrient deficiency, growth stage and water stress. Tile labels match the
/// backend assistant pointers so a farmer can reach the exact screen the
/// assistant recommends.
class DetectionHubScreen extends StatelessWidget {
  const DetectionHubScreen({super.key});

  void _open(BuildContext context, Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }

  @override
  Widget build(BuildContext context) {
    final titles = <_HubEntry>[
      _HubEntry(
        icon: Icons.healing_outlined,
        label: AppStrings.diagnosisTitle,
        screen: const DiagnosisScreen(),
      ),
      _HubEntry(
        icon: Icons.bug_report_outlined,
        label: AppStrings.pestTitle,
        screen: const PestScreen(),
      ),
      _HubEntry(
        icon: Icons.grass,
        label: AppStrings.weedTitle,
        screen: const WeedScreen(),
      ),
      _HubEntry(
        icon: Icons.science_outlined,
        label: AppStrings.nutrientTitle,
        screen: const NutrientDeficiencyScreen(),
      ),
      _HubEntry(
        icon: Icons.timeline_outlined,
        label: AppStrings.growthStageTitle,
        screen: const GrowthStageScreen(),
      ),
      _HubEntry(
        icon: Icons.water_drop_outlined,
        label: AppStrings.waterStressTitle,
        screen: const WaterStressScreen(),
      ),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.detectionHubTitle)),
      body: GridView.count(
        padding: const EdgeInsets.all(16),
        crossAxisCount: 2,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 1.15,
        children: [
          for (final entry in titles)
            _HubTile(
              icon: entry.icon,
              label: entry.label,
              onTap: () => _open(context, entry.screen),
            ),
        ],
      ),
    );
  }
}

class _HubEntry {
  const _HubEntry({
    required this.icon,
    required this.label,
    required this.screen,
  });

  final IconData icon;
  final String label;
  final Widget screen;
}

class _HubTile extends StatelessWidget {
  const _HubTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 40,
                color: _tileColor(theme),
              ),
              const SizedBox(height: 8),
              Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.darkGreen,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _tileColor(ThemeData theme) {
    return switch (label) {
      AppStrings.pestTitle => Colors.brown,
      AppStrings.weedTitle => Colors.green,
      AppStrings.nutrientTitle => Colors.orange,
      AppStrings.growthStageTitle => Colors.blue,
      AppStrings.waterStressTitle => Colors.cyan,
      _ => theme.colorScheme.primary,
    };
  }
}