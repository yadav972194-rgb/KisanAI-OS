import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/list_screen.dart';
import '../../dependencies.dart';
import '../../models/farmer.dart';

/// Read-only foundation for the farmer module (list from the real API).
class FarmersScreen extends StatelessWidget {
  const FarmersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = context.read<AppDependencies>().farmersController;
    return ListScreen<Farmer>(
      title: AppStrings.farmersTitle,
      controller: controller,
      itemBuilder: (context, farmer) {
        return Card(
          child: ListTile(
            leading: const Icon(Icons.person_outline, color: Colors.teal),
            title: Text(farmer.name),
            subtitle: Text(
              '${farmer.mobile} • ${farmer.locationSummary}\n'
              'फसलें: ${farmer.crops.isEmpty ? '—' : farmer.crops.map((c) => c.cropName).join(', ')}',
            ),
            isThreeLine: true,
          ),
        );
      },
    );
  }
}
