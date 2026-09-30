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

  DropdownButton<String> dropdownAt(WidgetTester tester, int index) =>
      tester.widget<DropdownButton<String>>(
        find.byType(DropdownButton<String>).at(index),
      );

  /// Opens a dropdown and picks [option] from the overlay menu.
  Future<void> pickOption(WidgetTester tester, int index, String option) async {
    await tester.tap(
      find.byType(DropdownButton<String>).at(index),
      warnIfMissed: false,
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text(option).last);
    await tester.pumpAndSettle();
  }

  /// Walks the cascading देश → राज्य → जिला → तहसील dropdowns top to bottom.
  Future<void> selectLocation(
    WidgetTester tester, {
    String state = 'Rajasthan',
    String district = 'Jaipur',
    String tehsil = 'Jaipur Tehsil',
  }) async {
    await pickOption(tester, 0, 'India');
    await pickOption(tester, 1, state);
    await pickOption(tester, 2, district);
    await pickOption(tester, 3, tehsil);
  }

  Future<void> createFarm(WidgetTester tester,
      {String farmSize = '2.5', String village = 'Sanganer'}) async {
    await selectLocation(tester);
    await pickOption(tester, 4, village);
    await tester.enterText(find.byType(TextFormField).at(0), farmSize);
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
    // देश + राज्य + जिला + तहसील dropdowns; गाँव (free-text) + आकार fields.
    expect(find.byType(DropdownButton<String>), findsNWidgets(4));
    expect(find.byType(TextFormField), findsNWidgets(2));
  });

  testWidgets('empty create submit shows validation errors', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await tester.tap(find.text('खेत बनाएं'));
    await tester.pumpAndSettle();

    expect(find.text('देश आवश्यक है'), findsOneWidget);
    expect(find.text('गाँव आवश्यक है'), findsOneWidget);
    expect(find.text('जिला आवश्यक है'), findsOneWidget);
    expect(find.text('राज्य आवश्यक है'), findsOneWidget);
    expect(find.text('तहसील आवश्यक है'), findsOneWidget);
  });

  testWidgets('invalid farm size is rejected', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await selectLocation(tester);
    await pickOption(tester, 4, 'Sanganer');
    await tester.enterText(find.byType(TextFormField).at(0), 'abc');
    await tester.tap(find.text('खेत बनाएं'));
    await tester.pumpAndSettle();

    expect(find.text('सही खेत का आकार दर्ज करें'), findsOneWidget);
  });

  testWidgets(
      'location fields appear in the देश→राज्य→जिला→तहसील→गाँव→आकार order',
      (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    final labels = ['देश', 'राज्य', 'जिला', 'तहसील', 'गाँव', 'खेत का आकार (एकड़)'];
    final tops = <double>[
      for (final label in labels) tester.getTopLeft(find.text(label)).dy,
    ];
    expect(tops, orderedEquals([...tops]..sort()));
  });

  testWidgets('district and tehsil stay disabled until their parent is chosen',
      (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    // Only देश can be opened before anything is selected.
    expect(dropdownAt(tester, 0).onChanged, isNotNull);
    expect(dropdownAt(tester, 1).onChanged, isNull);
    expect(dropdownAt(tester, 2).onChanged, isNull);
    expect(dropdownAt(tester, 3).onChanged, isNull);

    await pickOption(tester, 0, 'India');

    // राज्य enabled, जिला/तहसील still blocked.
    expect(dropdownAt(tester, 1).onChanged, isNotNull);
    expect(dropdownAt(tester, 2).onChanged, isNull);
    expect(dropdownAt(tester, 3).onChanged, isNull);

    await pickOption(tester, 1, 'Rajasthan');

    // जिला enabled, तहसील still blocked on जिला.
    expect(dropdownAt(tester, 2).onChanged, isNotNull);
    expect(dropdownAt(tester, 3).onChanged, isNull);

    await pickOption(tester, 2, 'Jaipur');
    expect(dropdownAt(tester, 3).onChanged, isNotNull);
  });

  testWidgets('selecting a state filters the district options', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await pickOption(tester, 0, 'India');
    await pickOption(tester, 1, 'Madhya Pradesh');
    await tester.tap(find.byType(DropdownButton<String>).at(2),
        warnIfMissed: false);
    await tester.pumpAndSettle();

    expect(find.text('Sehore'), findsOneWidget);
    expect(find.text('Bhopal'), findsOneWidget);
    expect(find.text('Jaipur'), findsNothing);
  });

  testWidgets('selecting a district filters the tehsil options', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await pickOption(tester, 0, 'India');
    await pickOption(tester, 1, 'Rajasthan');
    await pickOption(tester, 2, 'Jaipur');
    await tester.tap(find.byType(DropdownButton<String>).at(3),
        warnIfMissed: false);
    await tester.pumpAndSettle();

    expect(find.text('Jaipur Tehsil'), findsOneWidget);
    expect(find.text('Jodhpur Tehsil'), findsNothing);
  });

  testWidgets(
      'changing the state resets district, tehsil and village selections',
      (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await selectLocation(tester);
    await pickOption(tester, 4, 'Sanganer');
    expect(find.text('Jaipur Tehsil'), findsOneWidget);
    expect(find.text('Sanganer'), findsOneWidget);

    await pickOption(tester, 1, 'Madhya Pradesh');

    // Descendants were cleared: hints are back and old selections gone.
    expect(find.text('जिला चुनें'), findsOneWidget);
    expect(find.text('तहसील चुनें'), findsOneWidget);
    expect(find.text('Jaipur'), findsNothing);
    expect(find.text('Jaipur Tehsil'), findsNothing);
    expect(find.text('Sanganer'), findsNothing);

    // The new district list belongs to the new state only.
    await tester.tap(find.byType(DropdownButton<String>).at(2),
        warnIfMissed: false);
    await tester.pumpAndSettle();
    expect(find.text('Sehore'), findsOneWidget);
    expect(find.text('Jaipur'), findsNothing);
  });

  testWidgets('changing the country resets all descendants', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await selectLocation(tester);
    await pickOption(tester, 4, 'Sanganer');
    expect(find.byType(DropdownButton<String>), findsNWidgets(5));
    expect(find.text('Sanganer'), findsOneWidget);

    // Re-picking the country clears everything below it.
    await pickOption(tester, 0, 'India');

    expect(find.byType(DropdownButton<String>), findsNWidgets(4));
    expect(find.text('राज्य चुनें'), findsOneWidget);
    expect(find.text('Jaipur'), findsNothing);
    expect(find.text('Jaipur Tehsil'), findsNothing);
    expect(find.text('Sanganer'), findsNothing);
  });

  testWidgets('village is disabled until a tehsil is chosen', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await pickOption(tester, 0, 'India');
    await pickOption(tester, 1, 'Rajasthan');
    await pickOption(tester, 2, 'Jaipur');

    // Tehsil not chosen yet → the free-text गाँव field is disabled.
    final villageField =
        tester.widget<TextFormField>(find.byType(TextFormField).first);
    expect(villageField.enabled, isFalse);

    await pickOption(tester, 3, 'Jaipur Tehsil');

    // The tehsil has curated villages → a village dropdown appears.
    expect(find.byType(DropdownButton<String>), findsNWidgets(5));
    expect(dropdownAt(tester, 4).onChanged, isNotNull);
  });

  testWidgets('village dropdown lists only the selected tehsil villages',
      (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await selectLocation(tester); // Rajasthan → Jaipur → Jaipur Tehsil
    await tester.tap(find.byType(DropdownButton<String>).at(4),
        warnIfMissed: false);
    await tester.pumpAndSettle();

    expect(find.text('Amer'), findsOneWidget);
    expect(find.text('Sanganer'), findsOneWidget);
    expect(find.text('Malihabad'), findsNothing); // a Lucknow village

    await tester.tap(find.text('Amer').last);
    await tester.pumpAndSettle();
    expect(find.text('Amer'), findsOneWidget);
  });

  testWidgets('tehsil without curated villages falls back to free-text गाँव',
      (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    await selectLocation(tester,
        state: 'Rajasthan', district: 'Jodhpur', tehsil: 'Jodhpur Tehsil');

    // No curated villages → free-text गाँव field, now enabled.
    expect(find.byType(DropdownButton<String>), findsNWidgets(4));
    final villageField =
        tester.widget<TextFormField>(find.byType(TextFormField).first);
    expect(villageField.enabled, isTrue);

    await tester.enterText(find.byType(TextFormField).at(0), 'नरसिंहपुर');
    await tester.enterText(find.byType(TextFormField).at(1), '2.5');
    await tester.tap(find.text('खेत बनाएं'));
    await tester.pumpAndSettle();

    expect(backend.myFarm?['village'], 'नरसिंहपुर');
    expect(backend.myFarm?['country'], 'India');
  });

  testWidgets(
      'farm payload includes country, state, district, tehsil, village, size',
      (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    await selectLocation(tester);
    await pickOption(tester, 4, 'Sanganer');
    await tester.enterText(find.byType(TextFormField).at(0), '2.5');
    await tester.tap(find.text('खेत बनाएं'));
    await tester.pumpAndSettle();

    final farm = backend.myFarm!;
    expect(farm['country'], 'India');
    expect(farm['state'], 'Rajasthan');
    expect(farm['district'], 'Jaipur');
    expect(farm['block'], 'Jaipur Tehsil');
    expect(farm['village'], 'Sanganer');
    expect(farm['farm_size'], 2.5);
  });

  testWidgets('creating a farm shows the profile details', (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);

    expect(find.text('Ravi Kumar'), findsOneWidget);
    expect(find.text('Sanganer'), findsOneWidget);
    expect(find.text('Jaipur Tehsil'), findsOneWidget);
    expect(find.text('Jaipur'), findsOneWidget);
    expect(find.text('Rajasthan'), findsOneWidget);
    expect(find.text('India'), findsWidgets);
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

  testWidgets('editing a farm keeps the hierarchy and updates the profile',
      (tester) async {
    useTallSurface(tester);
    await tester.pumpWidget(wrap(buildDeps(FakeBackend())));
    await tester.pumpAndSettle();

    await createFarm(tester);

    await tester.tap(find.byTooltip('खेत संपादित करें'));
    await tester.pumpAndSettle();
    await pickOption(tester, 4, 'Bagru');
    await tester.tap(find.text('खेत अपडेट करें'));
    await tester.pumpAndSettle();

    expect(find.text('Bagru'), findsOneWidget);
    expect(find.text('Sanganer'), findsNothing);
    expect(find.text('Jaipur Tehsil'), findsOneWidget);
    expect(find.text('Jaipur'), findsOneWidget);
    expect(find.text('Rajasthan'), findsOneWidget);
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
    expect(find.text('Sanganer'), findsOneWidget);
    expect(find.text('Jaipur Tehsil'), findsOneWidget);
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