import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../dependencies.dart';
import '../../models/admin_models.dart';
import 'admin_controller.dart';

/// Notifications / reports / alerts the admin can create, view and deliver.
class AdminNotificationsScreen extends StatefulWidget {
  const AdminNotificationsScreen({super.key});

  @override
  State<AdminNotificationsScreen> createState() =>
      _AdminNotificationsScreenState();
}

class _AdminNotificationsScreenState extends State<AdminNotificationsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppDependencies>().adminController.loadNotifications();
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<AppDependencies>().adminController;
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.adminNotifications)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _createNotification(context, controller),
        icon: const Icon(Icons.add_alert_outlined),
        label: const Text(AppStrings.adminCreateNotification),
      ),
      body: switch (controller.notificationsState) {
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
        AdminViewState.ready => controller.notifications.isEmpty
            ? const Center(child: Text(AppStrings.adminNoNotifications))
            : RefreshIndicator(
                onRefresh: controller.loadNotifications,
                child: ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: controller.notifications.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) => _card(
                    context,
                    controller,
                    controller.notifications[index],
                  ),
                ),
              ),
      },
    );
  }

  Widget _card(
    BuildContext context,
    AdminController controller,
    NotificationItem item,
  ) {
    final delivered = item.status == 'delivered';
    return Card(
      child: ListTile(
        leading: Icon(
          delivered ? Icons.notifications_active_outlined : Icons.notifications_none,
          color: delivered ? Colors.green : Colors.teal,
        ),
        title: Text(item.title),
        subtitle: Text(
          '${item.category} • ${delivered ? AppStrings.adminDelivered : AppStrings.adminPending}\n${item.message}',
        ),
        isThreeLine: true,
        trailing: delivered
            ? null
            : TextButton(
                onPressed: () => controller.deliverNotification(
                  item.notificationId,
                ),
                child: const Text(AppStrings.adminDelivered),
              ),
      ),
    );
  }

  Future<void> _createNotification(
    BuildContext context,
    AdminController controller,
  ) async {
    final category = TextEditingController(text: 'ALERT');
    final title = TextEditingController();
    final message = TextEditingController();
    final created = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text(AppStrings.adminCreateNotification),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: category,
                  decoration: const InputDecoration(
                    labelText: AppStrings.adminNotificationCategory,
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: title,
                  decoration: const InputDecoration(
                    labelText: AppStrings.adminNotificationTitle,
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: message,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: AppStrings.adminNotificationMessage,
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text(AppStrings.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text(AppStrings.adminCreateNotification),
            ),
          ],
        );
      },
    );
    if (created != true || !context.mounted) return;

    final ok = await controller.createNotification(
      category: category.text.trim().toUpperCase(),
      title: title.text.trim(),
      message: message.text.trim(),
    );
    if (!context.mounted) return;
    if (!ok) {
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
}