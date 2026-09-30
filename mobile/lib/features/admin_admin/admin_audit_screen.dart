import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../dependencies.dart';
import '../../models/admin_models.dart';
import 'admin_controller.dart';

/// Read-only audit trail of every sensitive admin mutation.
class AdminAuditScreen extends StatefulWidget {
  const AdminAuditScreen({super.key});

  @override
  State<AdminAuditScreen> createState() => _AdminAuditScreenState();
}

class _AdminAuditScreenState extends State<AdminAuditScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppDependencies>().adminController.loadAudit();
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<AppDependencies>().adminController;
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.adminAuditTrail)),
      body: switch (controller.auditState) {
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
        AdminViewState.ready => controller.audit.isEmpty
            ? const Center(child: Text(AppStrings.adminAuditEmpty))
            : RefreshIndicator(
                onRefresh: controller.loadAudit,
                child: ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: controller.audit.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) =>
                      _entry(context, controller.audit[index]),
                ),
              ),
      },
    );
  }

  Widget _entry(BuildContext context, AuditEntry entry) {
    return Card(
      child: ListTile(
        leading: Icon(
          Icons.schedule_outlined,
          color: Theme.of(context).colorScheme.primary,
        ),
        title: Text(entry.action),
        subtitle: Text(
          '${entry.entityType} #${entry.entityId ?? '-'} • '
          '${entry.createdAt}\n'
          '${AppStrings.adminEditedBy}: ${entry.actorUserId ?? '-'}',
        ),
        isThreeLine: true,
      ),
    );
  }
}