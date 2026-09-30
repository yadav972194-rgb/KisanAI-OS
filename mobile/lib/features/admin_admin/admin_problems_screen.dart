import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../dependencies.dart';
import '../../models/admin_models.dart';
import 'admin_controller.dart';

/// Global problem/feedback workflow: list, create and status transitions.
class AdminProblemsScreen extends StatefulWidget {
  const AdminProblemsScreen({super.key});

  @override
  State<AdminProblemsScreen> createState() => _AdminProblemsScreenState();
}

class _AdminProblemsScreenState extends State<AdminProblemsScreen> {
  static const _statusFlow = [
    'new',
    'investigating',
    'contacted',
    'in_progress',
    'resolved',
    'closed',
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppDependencies>().adminController.loadProblems();
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<AppDependencies>().adminController;
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.adminProblems)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _createProblem(context, controller),
        icon: const Icon(Icons.add),
        label: const Text(AppStrings.adminNewProblem),
      ),
      body: switch (controller.problemsState) {
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
        AdminViewState.ready => controller.problems.isEmpty
            ? const Center(
                child: Text(AppStrings.adminProblemsEmpty),
              )
            : RefreshIndicator(
                onRefresh: controller.loadProblems,
                child: ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: controller.problems.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final item = controller.problems[index];
                    return _problemCard(context, controller, item);
                  },
                ),
              ),
      },
    );
  }

  Widget _problemCard(
    BuildContext context,
    AdminController controller,
    FeedbackItem item,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    item.subject,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
                const SizedBox(width: 8),
                PopupMenuButton<String>(
                  initialValue: item.status,
                  onSelected: (status) {
                    if (status == item.status) return;
                    controller.transitionStatus(item.feedbackId, status);
                  },
                  itemBuilder: (context) => [
                    for (final status in _statusFlow)
                      PopupMenuItem(
                        value: status,
                        child: Text(status),
                      ),
                  ],
                  child: Chip(
                    label: Text(item.status),
                    backgroundColor:
                        item.status == 'new'
                            ? Colors.orange.shade100
                            : item.status == 'resolved'
                            ? Colors.green.shade100
                            : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(item.description),
            const SizedBox(height: 8),
            Row(
              children: [
                if (item.farmerId != null)
                  Text('किसान #${item.farmerId}'),
                const SizedBox(width: 12),
                Text('${AppStrings.adminPriorityLabel}: ${item.priority}'),
                const Spacer(),
                Text(
                  item.updatedAt ?? item.createdAt,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _createProblem(
    BuildContext context,
    AdminController controller,
  ) async {
    final subject = TextEditingController();
    final description = TextEditingController();
    final created = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text(AppStrings.adminNewProblem),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: subject,
                  decoration: const InputDecoration(
                    labelText: AppStrings.adminSubjectLabel,
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: description,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: AppStrings.adminDescriptionLabel,
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
              child: const Text(AppStrings.adminNewProblem),
            ),
          ],
        );
      },
    );
    if (created != true || !context.mounted) return;

    final ok = await controller.createProblem(
      subject: subject.text.trim(),
      description: description.text.trim(),
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