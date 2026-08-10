import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/constants/app_strings.dart';
import 'core/theme/app_theme.dart';
import 'dependencies.dart';
import 'features/auth/auth_controller.dart';
import 'features/auth/login_screen.dart';
import 'features/diagnosis/diagnosis_controller.dart';
import 'features/home/home_screen.dart';
import 'features/recommendations/recommendations_controller.dart';
import 'features/splash/splash_screen.dart';
import 'features/weather/weather_controller.dart';

/// Root widget of the KisanAI app.
class KisanApp extends StatelessWidget {
  const KisanApp({super.key, required this.dependencies});

  final AppDependencies dependencies;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<AppDependencies>.value(value: dependencies),
        ChangeNotifierProvider<AuthController>.value(
          value: dependencies.authController,
        ),
        ChangeNotifierProvider<WeatherController>.value(
          value: dependencies.weatherController,
        ),
        ChangeNotifierProvider<DiagnosisController>.value(
          value: dependencies.diagnosisController,
        ),
        ChangeNotifierProvider<RecommendationsController>.value(
          value: dependencies.recommendationsController,
        ),
      ],
      child: MaterialApp(
        title: AppStrings.appName,
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        home: const SplashGate(),
      ),
    );
  }
}

/// Picks the root screen based on the current auth status.
class SplashGate extends StatefulWidget {
  const SplashGate({super.key});

  @override
  State<SplashGate> createState() => _SplashGateState();
}

class _SplashGateState extends State<SplashGate> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthController>().restoreSession();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthController>(
      builder: (context, auth, _) {
        switch (auth.status) {
          case AuthStatus.unknown:
            return const SplashScreen();
          case AuthStatus.authenticated:
            return HomeScreen();
          case AuthStatus.unauthenticated:
            return LoginScreen();
        }
      },
    );
  }
}
