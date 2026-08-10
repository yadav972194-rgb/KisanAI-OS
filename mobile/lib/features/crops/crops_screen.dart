import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/list_screen.dart';
import '../../dependencies.dart';
import '../../models/crop.dart';

/// Read-only foundation for the crops module (list from the real API).
class CropsScreen extends StatelessWidget {
  const CropsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = context.read<AppDependencies>().cropsController;
    return ListScreen<Crop>(
      title: AppStrings.cropsTitle,
      controller: controller,
      itemBuilder: (context, crop) {
        return Card(
          child: ListTile(
            leading: const Icon(Icons.grass, color: Colors.green),
            title: Text(crop.cropName),
            subtitle: Text(
              '${crop.season} • ${crop.durationDays} दिन • ${crop.waterRequirement}',
            ),
          ),
        );
      },
    );
  }
}
