import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../dependencies.dart';
import 'admin_audit_screen.dart';
import 'admin_farmers_screen.dart';
import 'admin_notifications_screen.dart';
import 'admin_problems_screen.dart';

/// Hub screen for the Admin Control & Farmer Support module.
class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppDependencies>().adminController.loadSummary();
    });
  }

  void _open(BuildContext context, Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<AppDependencies>().adminController;

    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.adminTitle)),
      body: ListenableBuilder(
        listenable: controller,
        builder: (context, _) {
          final tiles = <_AdminTile>[
            _AdminTile(
              icon: Icons.groups_outlined,
              label: AppStrings.adminFarmersDirectory,
              screen: const AdminFarmersScreen(),
            ),
            _AdminTile(
              icon: Icons.assignment_outlined,
              label: AppStrings.adminProblems,
              screen: const AdminProblemsScreen(),
            ),
            _AdminTile(
              icon: Icons.notifications_outlined,
              label: AppStrings.adminNotifications,
              screen: const AdminNotificationsScreen(),
            ),
          ];
          if (controller.isSuperAdmin) {
            tiles.insert(
              3,
              _AdminTile(
                icon: Icons.receipt_long_outlined,
                label: AppStrings.adminAudit,
                screen: const AdminAuditScreen(),
              ),
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (controller.isSuperAdmin)
                Card(
                  color: Colors.indigo.shade50,
                  child: const ListTile(
                    leading: Icon(Icons.verified_user, color: Colors.indigo),
                    title: Text(AppStrings.adminSuperAdminBadge),
                    subtitle: Text(AppStrings.adminSuperAdminOnly),
                  ),
                ),
              const SizedBox(height: 12),
              for (final tile in tiles)
                Card(
                  child: ListTile(
                    leading: Icon(tile.icon, color: Colors.teal),
                    title: Text(tile.label),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _open(context, tile.screen),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _AdminTile {
  const _AdminTile({
    required this.icon,
    required this.label,
    required this.screen,
  });

  final IconData icon;
  final String label;
  final Widget screen;
}