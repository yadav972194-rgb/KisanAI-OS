import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../auth/auth_controller.dart';
import '../crops/crops_screen.dart';
import '../diagnosis/diagnosis_screen.dart';
import '../diseases/diseases_screen.dart';
import '../farmers/farmers_screen.dart';
import '../profile/profile_screen.dart';
import '../recommendations/recommendations_screen.dart';
import '../soils/soils_screen.dart';
import '../weather/weather_screen.dart';

/// Landmark screen reached after login. Shows bilingual quick-access cards.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  void _open(BuildContext context, Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthController>();
    final user = auth.user;

    final cards = <_DashboardCard>[
      _DashboardCard(
        icon: Icons.wb_sunny_outlined,
        label: AppStrings.weatherCard,
        screen: const WeatherScreen(),
      ),
      _DashboardCard(
        icon: Icons.grass,
        label: AppStrings.cropsCard,
        screen: const CropsScreen(),
      ),
      _DashboardCard(
        icon: Icons.layers_outlined,
        label: AppStrings.soilCard,
        screen: const SoilsScreen(),
      ),
      _DashboardCard(
        icon: Icons.image_search_outlined,
        label: AppStrings.diagnosisCard,
        screen: const DiagnosisScreen(),
      ),
      _DashboardCard(
        icon: Icons.auto_awesome_outlined,
        label: AppStrings.recommendationsCard,
        screen: const RecommendationsScreen(),
      ),
      _DashboardCard(
        icon: Icons.healing_outlined,
        label: AppStrings.diseasesCard,
        screen: const DiseasesScreen(),
      ),
      _DashboardCard(
        icon: Icons.groups_outlined,
        label: AppStrings.farmersCard,
        screen: const FarmersScreen(),
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppStrings.homeTitle),
        actions: [
          IconButton(
            tooltip: AppStrings.profileTitle,
            icon: const Icon(Icons.account_circle_outlined),
            onPressed: () => _open(context, const ProfileScreen()),
          ),
        ],
      ),
      body: Column(
        children: [
          if (user != null)
            Container(
              width: double.infinity,
              color: AppTheme.fieldBg,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Text(
                'नमस्ते, ${user.displayName}',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.darkGreen,
                ),
              ),
            ),
          Expanded(
            child: GridView.count(
              padding: const EdgeInsets.all(16),
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.15,
              children: [
                for (final card in cards)
                  _CardTile(card: card, onTap: () => _open(context, card.screen)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DashboardCard {
  const _DashboardCard({
    required this.icon,
    required this.label,
    required this.screen,
  });

  final IconData icon;
  final String label;
  final Widget screen;
}

class _CardTile extends StatelessWidget {
  const _CardTile({required this.card, required this.onTap});

  final _DashboardCard card;
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
              Icon(card.icon, size: 40, color: theme.colorScheme.primary),
              const SizedBox(height: 8),
              Text(
                card.label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 15,
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
