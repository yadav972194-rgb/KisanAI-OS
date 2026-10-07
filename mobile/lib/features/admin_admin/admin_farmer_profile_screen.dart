import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../dependencies.dart';
import '../../models/farmer.dart';
import 'admin_controller.dart';

/// Full admin view of a single farmer: profile fields, crops, soils,
/// contact records, problems and account actions.
class AdminFarmerProfileScreen extends StatefulWidget {
  const AdminFarmerProfileScreen({super.key, required this.farmerId});

  final int farmerId;

  @override
  State<AdminFarmerProfileScreen> createState() =>
      _AdminFarmerProfileScreenState();
}

class _AdminFarmerProfileScreenState extends State<AdminFarmerProfileScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppDependencies>().adminController.openFarmer(widget.farmerId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<AppDependencies>().adminController;
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.adminFarmerProfile)),
      body: switch (controller.profileState) {
        AdminViewState.initial ||
        AdminViewState.loading =>
          const Center(child: CircularProgressIndicator()),
        AdminViewState.error => Center(
            child: Text(
              controller.errorMessage.isEmpty
                  ? AppStrings.genericError
                  : controller.errorMessage,
            ),
          ),
        AdminViewState.ready => _buildContent(context, controller),
      },
    );
  }

  Widget _buildContent(BuildContext context, AdminController controller) {
    final profile = controller.profile!;
    final farmer = profile.farmer;
    return RefreshIndicator(
      onRefresh: () => controller.openFarmer(widget.farmerId),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _section(
            context,
            Icons.person_outline,
            AppStrings.adminFarmerProfile,
            [
              _field(context, 'नाम', farmer.name),
              _field(context, AppStrings.mobileLabel, farmer.mobile),
              _field(context, AppStrings.villageLabel, farmer.village),
              _field(context, AppStrings.districtLabel, farmer.district),
              _field(context, AppStrings.stateLabel, farmer.state),
              if (farmer.country != null)
                _field(context, AppStrings.countryLabel, farmer.country!),
            ],
          ),
          const SizedBox(height: 16),
          _section(
            context,
            Icons.grass,
            AppStrings.adminCrops,
            profile.farmer.crops.isEmpty
                ? [_empty(context, 'कोई फसल नहीं')]
                : [
                    for (final crop in profile.farmer.crops)
                      _field(
                        context,
                        crop.cropName,
                        '${crop.season} • ${crop.durationDays} दिन • ${crop.waterRequirement}',
                      ),
                  ],
          ),
          const SizedBox(height: 16),
          _section(
            context,
            Icons.layers_outlined,
            AppStrings.adminSoils,
            profile.soils.isEmpty
                ? [_empty(context, 'कोई मिट्टी रिकॉर्ड नहीं')]
                : [
                    for (final soil in profile.soils)
                      _field(
                        context,
                        soil.soilType,
                        'pH ${soil.ph} • नमी ${soil.moisture}% • N ${soil.nitrogen} P ${soil.phosphorus} K ${soil.potassium}',
                      ),
                  ],
          ),
          const SizedBox(height: 16),
          _section(
            context,
            Icons.assignment_outlined,
            AppStrings.adminFeedback,
            profile.feedback.isEmpty
                ? [_empty(context, AppStrings.adminProblemsEmpty)]
                : [
                    for (final item in profile.feedback)
                      _field(
                        context,
                        item.subject,
                        '${item.status} • ${item.priority} — ${item.description}',
                      ),
                  ],
          ),
          const SizedBox(height: 16),
          _section(
            context,
            Icons.forum_outlined,
            AppStrings.adminContacts,
            profile.contacts.isEmpty
                ? [_empty(context, 'कोई संपर्क नहीं')]
                : [
                    for (final contact in profile.contacts)
                      _field(
                        context,
                        contact.channel,
                        '${contact.reason ?? ''} ${contact.note ?? ''}'.trim(),
                      ),
                  ],
          ),
          const SizedBox(height: 16),
          _accountActions(context, controller, farmer),
        ],
      ),
    );
  }

  Widget _accountActions(BuildContext context, AdminController controller, Farmer farmer) {
    if (!controller.isSuperAdmin) {
      return const SizedBox.shrink();
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              AppStrings.adminActions,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.lock_outline),
                    label: const Text(AppStrings.adminDeactivate),
                    onPressed: () => _run(
                      context,
                      controller.deactivateFarmer(farmer.farmerId),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.lock_open_outlined),
                    label: const Text(AppStrings.adminRestore),
                    onPressed: () => _run(
                      context,
                      controller.restoreFarmer(farmer.farmerId),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              icon: const Icon(Icons.delete_outline),
              label: const Text(AppStrings.adminDeleteFarmer),
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
              onPressed: () => _confirmDelete(context, controller, farmer),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _confirmDelete(
    BuildContext context,
    AdminController controller,
    Farmer farmer,
  ) async {
    final preview = await controller.fetchDeletePreview(farmer.farmerId);
    if (!context.mounted || preview == null) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text('${AppStrings.adminDeleteFarmer}: ${preview.name}'),
          content: Text(
            'फसलें: ${preview.crops}, मिट्टी: ${preview.soils}, '
            'सूचनाएं: ${preview.feedback}, संपर्क: ${preview.contacts}\n\n'
            '${AppStrings.adminDeleteConfirm}',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text(AppStrings.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text(AppStrings.adminDeleteFarmer),
            ),
          ],
        );
      },
    );
    if (!context.mounted || confirmed != true) return;

    final ok = await controller.deleteFarmer(farmer.farmerId, confirm: true);
    if (!context.mounted) return;
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text(AppStrings.adminDeleteFarmer)),
      );
      Navigator.of(context).pop();
    }
  }

  Future<void> _run(BuildContext context, Future<bool> action) async {
    final ok = await action;
    if (!context.mounted) return;
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text(AppStrings.adminSaved)),
      );
    } else {
      final controller = context.read<AppDependencies>().adminController;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            controller.errorMessage.isEmpty
                ? AppStrings.genericError
                : controller.errorMessage,
          ),
        ),
      );
    }
  }

  Widget _section(
    BuildContext context,
    IconData icon,
    String title,
    List<Widget> children,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: Colors.teal, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _field(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Widget _empty(BuildContext context, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(context).colorScheme.outline,
            ),
      ),
    );
  }
}