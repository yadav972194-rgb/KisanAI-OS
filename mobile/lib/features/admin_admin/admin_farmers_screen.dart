import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../dependencies.dart';
import '../../models/farmer.dart';
import 'admin_controller.dart';
import 'admin_farmer_profile_screen.dart';

/// Searchable farmer directory used by admins.
class AdminFarmersScreen extends StatefulWidget {
  const AdminFarmersScreen({super.key});

  @override
  State<AdminFarmersScreen> createState() => _AdminFarmersScreenState();
}

class _AdminFarmersScreenState extends State<AdminFarmersScreen> {
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppDependencies>().adminController.loadFarmers();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = context.read<AppDependencies>().adminController;
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.adminFarmersDirectory)),
      body: ListenableBuilder(
        listenable: controller,
        builder: (context, _) {
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(12),
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: AppStrings.adminSearchHint,
                    prefixIcon: const Icon(Icons.search),
                    border: const OutlineInputBorder(),
                    suffixIcon: controller.busy
                        ? const Padding(
                            padding: EdgeInsets.all(12),
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : null,
                  ),
                  onSubmitted: (value) => controller.loadFarmers(query: value),
                ),
              ),
              Expanded(
                child: switch (controller.directoryState) {
                  AdminViewState.initial ||
                  AdminViewState.loading =>
                    const Center(child: CircularProgressIndicator()),
                  AdminViewState.error => _errorView(context, controller),
                  AdminViewState.ready =>
                    controller.farmers.isEmpty
                        ? Center(
                            child: Text(
                              AppStrings.adminNoFarmers,
                              style: Theme.of(context).textTheme.bodyLarge,
                            ),
                          )
                        : ListView.separated(
                            padding: const EdgeInsets.all(12),
                            itemCount: controller.farmers.length,
                            separatorBuilder: (_, _) =>
                                const SizedBox(height: 8),
                            itemBuilder: (context, index) => _farmerCard(
                              context,
                              controller.farmers[index],
                            ),
                          ),
                },
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _errorView(BuildContext context, AdminController controller) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            controller.errorMessage.isEmpty
                ? AppStrings.genericError
                : controller.errorMessage,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: () => controller.loadFarmers(),
            child: const Text(AppStrings.retry),
          ),
        ],
      ),
    );
  }

  Widget _farmerCard(BuildContext context, Farmer farmer) {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.person_outline, color: Colors.teal),
        title: Text(farmer.name),
        subtitle: Text('${farmer.mobile} • ${farmer.locationSummary}'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => AdminFarmerProfileScreen(
                farmerId: farmer.farmerId,
              ),
            ),
          );
        },
      ),
    );
  }
}