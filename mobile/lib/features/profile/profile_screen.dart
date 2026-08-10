import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../auth/auth_controller.dart';

/// Shows the logged-in user's details and the logout action.
class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  Future<void> _confirmLogout(BuildContext context) async {
    final auth = context.read<AuthController>();
    final navigator = Navigator.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text(AppStrings.logout),
        content: const Text(AppStrings.logoutConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text(AppStrings.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text(AppStrings.logout),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      navigator.popUntil((route) => route.isFirst);
      await auth.logout();
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthController>().user;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.profileTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          CircleAvatar(
            radius: 36,
            backgroundColor: theme.colorScheme.primary,
            child: Text(
              (user?.displayName.isNotEmpty ?? false)
                  ? user!.displayName[0].toUpperCase()
                  : '?',
              style: const TextStyle(color: Colors.white, fontSize: 28),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            user?.displayName ?? '',
            textAlign: TextAlign.center,
            style: theme.textTheme.titleLarge,
          ),
          Text(
            '@${user?.username ?? ''}',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium
                ?.copyWith(color: theme.colorScheme.outline),
          ),
          const SizedBox(height: 24),
          Card(
            child: Column(
              children: [
                _ProfileRow(label: AppStrings.roleLabel, value: user?.role ?? ''),
                _ProfileRow(label: AppStrings.mobileLabel, value: user?.mobile ?? '—'),
                _ProfileRow(
                  label: AppStrings.statusLabel,
                  value: user?.isActive ?? false
                      ? AppStrings.activeAccount
                      : 'निष्क्रिय',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () => _confirmLogout(context),
            icon: const Icon(Icons.logout),
            label: const Text(AppStrings.logout),
            style: OutlinedButton.styleFrom(
              foregroundColor: theme.colorScheme.error,
              minimumSize: const Size.fromHeight(48),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileRow extends StatelessWidget {
  const _ProfileRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: const Icon(Icons.circle, size: 8),
      title: Text(label),
      trailing: Text(value),
    );
  }
}
