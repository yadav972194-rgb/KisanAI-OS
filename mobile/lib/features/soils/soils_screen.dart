import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/widgets/list_screen.dart';
import '../../dependencies.dart';
import '../../models/soil.dart';

/// Read-only foundation for the soil module (list from the real API).
class SoilsScreen extends StatelessWidget {
  const SoilsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = context.read<AppDependencies>().soilsController;
    return ListScreen<Soil>(
      title: AppStrings.soilTitle,
      controller: controller,
      itemBuilder: (context, soil) {
        return Card(
          child: ListTile(
            leading: const Icon(Icons.layers_outlined, color: Colors.brown),
            title: Text(soil.soilType),
            subtitle: Text(
              'pH ${soil.ph.toStringAsFixed(1)} • नमी ${soil.moisture.toStringAsFixed(0)}% • '
              'N ${soil.nitrogen} • P ${soil.phosphorus} • K ${soil.potassium}',
            ),
          ),
        );
      },
    );
  }
}
