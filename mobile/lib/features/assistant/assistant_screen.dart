import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/theme/app_theme.dart';
import '../assistant/assistant_controller.dart';

/// Ask the assistant natural-language questions about the farm / crop.
///
/// Answers come from `POST /api/assistant` which is honest by contract:
/// CROP_STATUS is built only from verified data (farm, crops, weather,
/// supplied soil) and missing data yields a clear Hindi message. This
/// screen renders the answer message plus any structured sections.
class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final _textController = TextEditingController();

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  void _ask(AssistantController controller) {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    FocusScope.of(context).unfocus();
    controller.ask(text);
  }

  void _askSuggestion(AssistantController controller, String suggestion) {
    _textController.text = suggestion;
    controller.ask(suggestion);
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<AssistantController>();

    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.assistantTitle)),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    AppStrings.assistantIntro,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: ActionChip(
                      avatar: const Icon(Icons.help_outline, size: 18),
                      label: const Text(AppStrings.assistantSuggestion),
                      onPressed: controller.state == AssistantState.loading
                          ? null
                          : () => _askSuggestion(
                              controller, AppStrings.assistantSuggestion),
                    ),
                  ),
                  const SizedBox(height: 16),
                  _AnswerArea(controller: controller),
                ],
              ),
            ),
          ),
          _InputBar(
            controller: _textController,
            onSend: () => _ask(controller),
            enabled: controller.state != AssistantState.loading,
          ),
        ],
      ),
    );
  }
}

class _AnswerArea extends StatelessWidget {
  const _AnswerArea({required this.controller});

  final AssistantController controller;

  @override
  Widget build(BuildContext context) {
    switch (controller.state) {
      case AssistantState.idle:
        return const SizedBox.shrink();
      case AssistantState.loading:
        return const Center(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: CircularProgressIndicator(),
          ),
        );
      case AssistantState.error:
        final errorColor = Theme.of(context).colorScheme.error;
        return Card(
          color: errorColor.withValues(alpha: 0.08),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.error_outline, color: errorColor),
                    const SizedBox(width: 8),
                    const Text(
                      AppStrings.genericError,
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(controller.errorMessage ?? ''),
              ],
            ),
          ),
        );
      case AssistantState.success:
        final response = controller.response;
        if (response == null) return const SizedBox.shrink();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              color: AppTheme.fieldBg,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  response.message,
                  style: const TextStyle(fontSize: 16, height: 1.4),
                ),
              ),
            ),
            if (response.data != null && response.isOk)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: _DataSections(data: response.data!),
              ),
          ],
        );
    }
  }
}

class _DataSections extends StatelessWidget {
  const _DataSections({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (data['farm'] is Map<String, dynamic>)
          _Section(
            title: AppStrings.farmSectionLabel,
            rows: _stringRows(data['farm'] as Map<String, dynamic>),
          ),
        if (data['crops'] is List && (data['crops'] as List).isNotEmpty)
          _Section(
            title: AppStrings.cropsSectionLabel,
            rows: [
              for (final crop in data['crops'] as List)
                if (crop is Map<String, dynamic>)
                  '${crop['crop_name']} (${crop['season'] ?? ''})',
            ],
          ),
        if (data['weather'] is Map<String, dynamic>)
          _Section(
            title: AppStrings.weatherSectionLabel,
            rows: _stringRows(data['weather'] as Map<String, dynamic>),
          ),
        if (data['advice'] is Map<String, dynamic>)
          _Section(
            title: AppStrings.adviceSectionLabel,
            rows: _adviceRows(data['advice'] as Map<String, dynamic>),
          ),
      ],
    );
  }

  List<String> _stringRows(Map<String, dynamic> map) {
    return [
      for (final entry in map.entries)
        if (entry.value != null && '${entry.value}'.isNotEmpty)
          '${entry.key}: ${entry.value}',
    ];
  }

  List<String> _adviceRows(Map<String, dynamic> advice) {
    final status = advice['status'];
    final recommendations = advice['recommendations'];
    if (recommendations is List && recommendations.isNotEmpty) {
      return [
        for (final item in recommendations)
          if (item is Map<String, dynamic>)
            '${item['category'] ?? ''}: ${item['text'] ?? ''}',
      ];
    }
    if (status != null) return ['status: $status'];
    return const [AppStrings.notAvailable];
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.rows});

  final String title;
  final List<String> rows;

  @override
  Widget build(BuildContext context) {
    if (rows.isEmpty) return const SizedBox.shrink();
    return Card(
      margin: const EdgeInsets.only(top: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                color: AppTheme.darkGreen,
              ),
            ),
            const SizedBox(height: 6),
            for (final row in rows)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text(row, style: const TextStyle(height: 1.3)),
              ),
          ],
        ),
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  const _InputBar({
    required this.controller,
    required this.onSend,
    required this.enabled,
  });

  final TextEditingController controller;
  final VoidCallback onSend;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                enabled: enabled,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSend(),
                decoration: InputDecoration(
                  hintText: AppStrings.assistantHint,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 10,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              tooltip: AppStrings.askButton,
              onPressed: enabled ? onSend : null,
              icon: const Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }
}
