import 'package:flutter/material.dart';

import 'app.dart';
import 'dependencies.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final dependencies = AppDependencies();
  runApp(KisanApp(dependencies: dependencies));
}
