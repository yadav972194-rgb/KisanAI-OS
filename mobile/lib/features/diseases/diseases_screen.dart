import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/list_screen.dart';
import '../../dependencies.dart';
import '../../models/disease.dart';

/// Read-only foundation for the disease reference module.
class DiseasesScreen extends StatelessWidget {
  const DiseasesScreen({super.key});

  Color _severityColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'low':
        return Colors.green;
      case 'medium':
        return Colors.orange;
      case 'high':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.read<AppDependencies>().diseasesController;
    return ListScreen<Disease>(
      title: AppStrings.diseasesTitle,
      controller: controller,
      itemBuilder: (context, disease) {
        return Card(
          child: ExpansionTile(
            leading: const Icon(Icons.healing_outlined, color: Colors.redAccent),
            title: Text(disease.diseaseName),
            subtitle: Text('${disease.cropName} • ${disease.severity}'),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _LabeledText(
                      label: 'लक्षण (symptoms)',
                      text: disease.symptoms,
                    ),
                    const SizedBox(height: 8),
                    _LabeledText(label: 'उपाय (solution)', text: disease.solution),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: _severityColor(disease.severity)
                              .withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'गंभीरता: ${disease.severity}',
                          style: TextStyle(
                            color: _severityColor(disease.severity),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _LabeledText extends StatelessWidget {
  const _LabeledText({required this.label, required this.text});

  final String label;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                fontWeight: FontWeight.w700,
                color: Theme.of(context).colorScheme.primary,
              ),
        ),
        const SizedBox(height: 2),
        Text(text),
      ],
    );
  }
}
