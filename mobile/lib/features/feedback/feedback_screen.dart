import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/common_views.dart';
import '../../dependencies.dart';
import '../../models/admin_models.dart';
import 'feedback_controller.dart';

/// Farmer self-service feedback screen ("Kisan ki Baat").
///
/// A form to raise a problem/suggestion plus the read-back of the current
/// user's own records with their status. The controller is shared per app and
/// bound to the authenticated user only.
class FeedbackScreen extends StatefulWidget {
  const FeedbackScreen({super.key});

  @override
  State<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen> {
  FeedbackController? _controller;
  final _formKey = GlobalKey<FormState>();
  final _subject = TextEditingController();
  final _description = TextEditingController();
  String _priority = 'medium';

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final controller = context.read<AppDependencies>().feedbackController;
    if (!identical(controller, _controller)) {
      _controller = controller;
      controller.load();
    }
  }

  @override
  void dispose() {
    _subject.dispose();
    _description.dispose();
    super.dispose();
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _submit(FeedbackController controller) async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    final ok = await controller.submit(
      subject: _subject.text.trim(),
      description: _description.text.trim(),
      priority: _priority,
    );
    if (!ok || !mounted) return;
    _subject.clear();
    _description.clear();
    _showMessage(AppStrings.feedbackSubmitted);
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.read<AppDependencies>().feedbackController;
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        return Scaffold(
          appBar: AppBar(title: const Text(AppStrings.feedbackTitle)),
          body: Builder(
            builder: (context) {
              switch (controller.state) {
                case FeedbackViewState.initial:
                case FeedbackViewState.loading:
                  return const LoadingView();
                case FeedbackViewState.error:
                  return ErrorView(
                    message: controller.errorMessage,
                    onRetry: controller.load,
                  );
                case FeedbackViewState.ready:
                  return RefreshIndicator(
                    onRefresh: controller.load,
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.all(16),
                      children: [
                        if (controller.errorMessage != null) ...[
                          ErrorBanner(message: controller.errorMessage!),
                          const SizedBox(height: 16),
                        ],
                        _FeedbackForm(
                          formKey: _formKey,
                          subject: _subject,
                          description: _description,
                          priority: _priority,
                          busy: controller.busy,
                          onPriorityChanged: (value) => setState(() {
                            _priority = value ?? 'medium';
                          }),
                          onSubmit: () => _submit(controller),
                        ),
                        const SizedBox(height: 8),
                        SectionHeader(
                          title: AppStrings.feedbackHistoryTitle,
                          subtitle:
                              '${controller.items.length} ${AppStrings.feedbackCountLabel}',
                        ),
                        if (controller.items.isEmpty)
                          const EmptyView(message: AppStrings.feedbackEmpty)
                        else
                          for (final item in controller.items)
                            _FeedbackTile(item: item),
                      ],
                    ),
                  );
              }
            },
          ),
        );
      },
    );
  }
}

/// Card holding the "raise feedback" form: subject, description and priority.
class _FeedbackForm extends StatelessWidget {
  const _FeedbackForm({
    required this.formKey,
    required this.subject,
    required this.description,
    required this.priority,
    required this.busy,
    required this.onPriorityChanged,
    required this.onSubmit,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController subject;
  final TextEditingController description;
  final String priority;
  final bool busy;
  final ValueChanged<String?> onPriorityChanged;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.rate_review_outlined,
                  size: 40, color: AppTheme.primaryGreen),
              const SizedBox(height: 8),
              Text(
                AppStrings.feedbackHint,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: subject,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: AppStrings.feedbackSubjectLabel,
                  prefixIcon: Icon(Icons.subject_outlined),
                ),
                validator: (value) =>
                    (value == null || value.trim().isEmpty)
                        ? AppStrings.feedbackSubjectRequired
                        : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: description,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: AppStrings.feedbackDescriptionLabel,
                  prefixIcon: Icon(Icons.notes_outlined),
                ),
                validator: (value) =>
                    (value == null || value.trim().isEmpty)
                        ? AppStrings.feedbackDescriptionRequired
                        : null,
              ),
              const SizedBox(height: 16),
              InputDecorator(
                decoration: const InputDecoration(
                  labelText: AppStrings.feedbackPriorityLabel,
                  prefixIcon: Icon(Icons.flag_outlined),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: priority,
                    isExpanded: true,
                    items: const [
                      DropdownMenuItem(
                        value: 'low',
                        child: Text(AppStrings.severityLow),
                      ),
                      DropdownMenuItem(
                        value: 'medium',
                        child: Text(AppStrings.severityMedium),
                      ),
                      DropdownMenuItem(
                        value: 'high',
                        child: Text(AppStrings.severityHigh),
                      ),
                    ],
                    onChanged: busy ? null : onPriorityChanged,
                  ),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: busy ? null : onSubmit,
                child: busy
                    ? const SizedBox(
                        height: 22,
                        width: 22,
                        child: CircularProgressIndicator(strokeWidth: 2.5),
                      )
                    : const Text(AppStrings.feedbackSubmitButton),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// One of the user's own feedback records with its status badge.
class _FeedbackTile extends StatelessWidget {
  const _FeedbackTile({required this.item});

  final FeedbackItem item;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
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
                Chip(
                  label: Text(item.status),
                  backgroundColor:
                      item.status == 'new'
                          ? Colors.orange.shade100
                          : item.status == 'resolved'
                          ? Colors.green.shade100
                          : null,
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(item.description),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(
                  '${AppStrings.feedbackPriorityLabel}: ${item.priority}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
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
}