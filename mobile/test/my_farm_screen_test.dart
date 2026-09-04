import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/app.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/storage/token_storage.dart';
import 'package:kisanai/dependencies.dart';
import 'package:kisanai/features/my_farm/my_farm_screen.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';

void main() {
  // A tall viewport so every field, sheet and dialog is laid out.
  void useTallSurface(WidgetTester tester) {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
  }

  AppDependencies buildDeps(FakeBackend backend) {
    final storage = InMemoryTokenStorage();
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
      tokenProvider: storage.read,
    );
    return AppDependencies(apiClient: client, tokenStorage: storage);
  }

  Widget wrap(AppDependencies deps) {
    return Provider<AppDependencies>.value(
      value: deps,
      child: const MaterialApp(home: MyFarmScreen()),
    );
  }

  Future<void> createFarm(WidgetTester tester,
      {String farmSize = '2.5'}) async {
    await tester.enterText(find.byType(TextFormField).at(0), 'नरसिंहपुर');
    await tester.enterText(find.byType(TextFormField).at(1), 'सीहोर');
    await tester.enterText(find.byType(TextFormField).at(2), 'मध्य प्रदेश');
    await tester.enterText(find.byType(TextFormField).at(3), farmSize);
    await tester.tap(find.text('खेत बनाएं'));
    await tester.pumpAndSettle();
  }

  Future<void> addCrop(WidgetTester tester,
      {String name = 'गेहूँ',
      String season = 'रबी',
      String duration = '120',
      String water = 'मध्यम'}) async {
    await tester.tap(find.text('फसल जोड़ें'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).at(0), name);
    await tester.enterText(find.byType(TextFormField).at(1), season);
    await tester.enterText(find.byType(TextFormField).at(2), duration);
    await tester.enterText(find.byType(TextFormField).at(3), water);
    await tester.tap(find.text('सेव करें'));
    await tester.pumpAndSettle();
  }

  testWidgets('no farm yet shows the create form', (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    expect(find.text('खेत बनाएं'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(4));
  });

  testWidgets('empty create submit shows validation errors', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await tester.tap(find.text('खेत बनाएं'));
    await tester.pumpAndSettle();

    expect(find.text('गाँव आवश्यक है'), findsOneWidget);
    expect(find.text('जिला आवश्यक है'), findsOneWidget);
    expect(find.text('राज्य आवश्यक है'), findsOneWidget);
  });

  testWidgets('invalid farm size is rejected', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextFormField).at(0), 'नरसिंहपुर');
    await tester.enterText(find.byType(TextFormField).at(1), 'सीहोर');
    await tester.enterText(find.byType(TextFormField).at(2), 'मध्य प्रदेश');
    await tester.enterText(find.byType(TextFormField).at(3), 'abc');
    await tester.tap(find.text('खेत बनाएं'));
    await tester.pumpAndSettle();

    expect(find.text('सही खेत का आकार दर्ज करें'), findsOneWidget);
  });

  testWidgets('creating a farm shows the profile details', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);

    expect(find.text('Ravi Kumar'), findsOneWidget);
    expect(find.text('नरसिंहपुर'), findsWidgets);
    expect(find.text('सीहोर'), findsOneWidget);
    expect(find.text('मध्य प्रदेश'), findsOneWidget);
    expect(find.text('2.5 एकड़'), findsOneWidget);
    expect(find.text('मेरी फसलें'), findsOneWidget);
    expect(find.text('अभी कोई फसल नहीं जोड़ी गई'), findsOneWidget);
  });

  testWidgets('adding a crop shows it in the list', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);
    await addCrop(tester);

    expect(find.text('गेहूँ'), findsOneWidget);
    expect(find.textContaining('रबी'), findsOneWidget);
    expect(find.textContaining('120 दिन'), findsOneWidget);
    expect(find.text('अभी कोई फसल नहीं जोड़ी गई'), findsNothing);
  });

  testWidgets('duplicate crop shows a friendly message', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);
    await addCrop(tester);
    await addCrop(tester, name: 'गेहूँ');

    expect(find.text('Crop already added to this farm'), findsOneWidget);
  });

  testWidgets('deleting a crop removes it', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);
    await addCrop(tester);

    await tester.tap(find.byTooltip('हटाएं'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('हटाएं'));
    await tester.pumpAndSettle();

    expect(find.text('गेहूँ'), findsNothing);
    expect(find.text('अभी कोई फसल नहीं जोड़ी गई'), findsOneWidget);
  });

  testWidgets('editing a farm updates the profile', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);

    await tester.tap(find.byTooltip('खेत संपादित करें'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).at(0), 'छिंदवाड़ा');
    await tester.tap(find.text('खेत अपडेट करें'));
    await tester.pumpAndSettle();

    expect(find.text('छिंदवाड़ा'), findsOneWidget);
    expect(find.text('नरसिंहपुर'), findsNothing);
  });

  testWidgets('deleting a farm returns to the create form', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);

    await tester.tap(find.byTooltip('खेत हटाएं'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('हटाएं'));
    await tester.pumpAndSettle();

    expect(find.text('खेत बनाएं'), findsOneWidget);
  });

  testWidgets('network failure shows the retry view', (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend()..failMyFarm = true;
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    expect(find.text('पुनः प्रयास करें'), findsOneWidget);
  });

  testWidgets('farm and crops persist after an app restart', (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();

    // First app session: create the farm and a crop.
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();
    await createFarm(tester);
    await addCrop(tester);
    expect(find.text('Ravi Kumar'), findsOneWidget);
    expect(find.text('गेहूँ'), findsOneWidget);

    // Simulate a full app restart: brand-new widget tree + brand-new
    // controller hitting the same backend, so nothing is held in memory.
    await tester.pumpWidget(const SizedBox());
    await tester.pumpAndSettle();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    expect(find.text('Ravi Kumar'), findsOneWidget);
    expect(find.text('नरसिंहपुर'), findsWidgets);
    expect(find.text('2.5 एकड़'), findsOneWidget);
    expect(find.text('गेहूँ'), findsOneWidget);
    expect(find.text('खेत बनाएं'), findsNothing);
    expect(find.text('अभी कोई फसल नहीं जोड़ी गई'), findsNothing);
  });

  testWidgets('home card opens the my-farm screen', (tester) async {
    useTallSurface(tester);
    final deps = buildDeps(FakeBackend());
    await tester.pumpWidget(KisanApp(dependencies: deps));
    // Pass the enforced ~2s branded splash before the login form is shown.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 2100));

    await tester.enterText(find.byType(TextFormField).first, 'ravi');
    await tester.enterText(find.byType(TextFormField).at(1), 'secret');
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    await tester.tap(find.text('मेरा खेत'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));
    await tester.pumpAndSettle();

    expect(find.text('खेत बनाएं'), findsOneWidget);
  });
}
