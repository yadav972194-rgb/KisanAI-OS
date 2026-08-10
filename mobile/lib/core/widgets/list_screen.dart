import 'package:flutter/material.dart';

import '../controllers/list_controller.dart';
import 'common_views.dart';

/// Scaffold + state handling shared by the simple read-only list screens.
class ListScreen<T> extends StatefulWidget {
  const ListScreen({
    super.key,
    required this.title,
    required this.controller,
    required this.itemBuilder,
  });

  final String title;
  final ListController<T> controller;
  final Widget Function(BuildContext context, T item) itemBuilder;

  @override
  State<ListScreen<T>> createState() => _ListScreenState<T>();
}

class _ListScreenState<T> extends State<ListScreen<T>> {
  @override
  void initState() {
    super.initState();
    widget.controller.load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: ListenableBuilder(
        listenable: widget.controller,
        builder: (context, _) {
          final controller = widget.controller;
          switch (controller.state) {
            case ListLoadState.initial:
            case ListLoadState.loading:
              return const LoadingView();
            case ListLoadState.error:
              return ErrorView(
                message: controller.errorMessage,
                onRetry: controller.load,
              );
            case ListLoadState.success:
              if (controller.items.isEmpty) {
                return const EmptyView();
              }
              return RefreshIndicator(
                onRefresh: controller.load,
                child: ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(12),
                  itemCount: controller.items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) =>
                      widget.itemBuilder(context, controller.items[index]),
                ),
              );
          }
        },
      ),
    );
  }
}
