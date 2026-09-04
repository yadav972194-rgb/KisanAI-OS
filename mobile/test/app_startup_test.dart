import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/app.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/storage/token_storage.dart';
import 'package:kisanai/dependencies.dart';
import 'package:kisanai/features/splash/splash_screen.dart';

import 'helpers/fake_backend.dart';

void main() {
  // A taller viewport so every dashboard card is actually laid out (GridView
  // lazily builds only visible children).
  void useTallSurface(WidgetTester tester) {
    tester.view.physicalSize = const Size(1080, 2200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
  }

  AppDependencies buildDeps({FakeBackend? backend}) {
    final storage = InMemoryTokenStorage();
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: (backend ?? FakeBackend()).client(),
      tokenProvider: storage.read,
    );
    return AppDependencies(apiClient: client, tokenStorage: storage);
  }

  // The branded splash is enforced for a minimum ~2s in SplashGate, so any
  // test that must reach the post-splash screen advances the fake clock past
  // that minimum duration (tester.pump(Duration) is virtual time, not real).
  Future<void> passSplash(WidgetTester tester) async {
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 2100));
  }

  Future<void> login(WidgetTester tester) async {
    await tester.enterText(find.byType(TextFormField).first, 'ravi');
    await tester.enterText(find.byType(TextFormField).at(1), 'secret');
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));
  }

  testWidgets('no saved session starts at the login screen', (tester) async {
    final deps = buildDeps();
    await tester.pumpWidget(KisanApp(dependencies: deps));
    await passSplash(tester);

    expect(find.text('लॉगिन करें'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(2));
  });

  testWidgets('a saved session skips login and lands on the dashboard',
      (tester) async {
    final storage = InMemoryTokenStorage();
    await storage.write('saved-token');
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: FakeBackend().client(),
      tokenProvider: storage.read,
    );
    final deps = AppDependencies(apiClient: client, tokenStorage: storage);

    await tester.pumpWidget(KisanApp(dependencies: deps));
    await passSplash(tester);

    expect(find.text('किसान होम'), findsOneWidget);
    expect(find.text('लॉगिन करें'), findsNothing);
  });

  testWidgets('login reaches the dashboard with Hindi quick-access cards',
      (tester) async {
    useTallSurface(tester);
    final deps = buildDeps();
    await tester.pumpWidget(KisanApp(dependencies: deps));
    await passSplash(tester);
    await login(tester);

    expect(find.text('किसान होम'), findsOneWidget);
    for (final label in [
      'मेरा खेत',
      'मौसम',
      'फसल',
      'मिट्टी',
      'रोग पहचान',
      'AI सलाह',
      'रोग ज्ञान',
      'किसान',
    ]) {
      expect(find.text(label), findsOneWidget);
    }
  });

  testWidgets('weather card opens the live weather screen', (tester) async {
    final deps = buildDeps();
    await tester.pumpWidget(KisanApp(dependencies: deps));
    await passSplash(tester);
    await login(tester);

    await tester.tap(find.text('मौसम'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    expect(find.text('Delhi'), findsOneWidget);
    expect(find.text('28.5°C'), findsWidgets);
    expect(find.text('Clear'), findsWidgets);
  });

  testWidgets('logout from profile returns to login', (tester) async {
    final deps = buildDeps();
    await tester.pumpWidget(KisanApp(dependencies: deps));
    await passSplash(tester);
    await login(tester);

    await tester.tap(find.byTooltip('प्रोफ़ाइल'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));
    expect(find.text('Ravi Kumar'), findsOneWidget);

    await tester.tap(find.text('लॉग आउट'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    await tester.tap(find.widgetWithText(FilledButton, 'लॉग आउट'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    expect(find.text('लॉगिन करें'), findsOneWidget);
  });

  testWidgets('branded splash is shown for the enforced minimum duration',
      (tester) async {
    final deps = buildDeps();
    await tester.pumpWidget(KisanApp(dependencies: deps));

    // Splash is shown on the initial frame.
    await tester.pump();
    expect(find.byType(SplashScreen), findsOneWidget);

    // Just before the enforced ~2s minimum it is still showing.
    await tester.pump(const Duration(milliseconds: 1500));
    expect(find.byType(SplashScreen), findsOneWidget);
    expect(find.text('लॉगिन करें'), findsNothing);

    // Past the minimum it transitions to login.
    await tester.pump(const Duration(milliseconds: 700));
    expect(find.byType(SplashScreen), findsNothing);
    expect(find.text('लॉगिन करें'), findsOneWidget);
  });
}
