import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/app.dart';
import 'package:kisanai/core/constants/app_strings.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/storage/token_storage.dart';
import 'package:kisanai/dependencies.dart';
import 'package:kisanai/features/feedback/feedback_screen.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';

void main() {
  // A tall viewport so the whole feedback screen is laid out.
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
      child: const MaterialApp(home: FeedbackScreen()),
    );
  }

  Future<void> enterSubject(
    WidgetTester tester,
    String subject, {
    String description = 'पानी की कमी',
  }) async {
    await tester.enterText(find.byType(TextFormField).at(0), subject);
    await tester.enterText(find.byType(TextFormField).at(1), description);
  }

  Future<void> submit(WidgetTester tester) async {
    await tester.tap(find.text(AppStrings.feedbackSubmitButton));
    await tester.pumpAndSettle();
  }

  testWidgets('shows the form and the user own feedback history',
      (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    expect(find.text(AppStrings.feedbackSubjectLabel), findsOneWidget);
    expect(find.text(AppStrings.feedbackDescriptionLabel), findsOneWidget);
    expect(find.text(AppStrings.feedbackPriorityLabel), findsOneWidget);
    expect(find.text(AppStrings.feedbackHistoryTitle), findsOneWidget);
    expect(find.text('सिंचाई समस्या'), findsOneWidget);
    expect(find.text('पानी की कमी'), findsOneWidget);
    expect(find.text('new'), findsOneWidget);
  });

  testWidgets('empty submit shows validation errors and sends nothing',
      (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    await submit(tester);

    expect(find.text(AppStrings.feedbackSubjectRequired), findsOneWidget);
    expect(find.text(AppStrings.feedbackDescriptionRequired), findsOneWidget);
    expect(backend.lastFeedbackPayload, isNull);
  });

  testWidgets('successful submit shows a message and updates the history',
      (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    await enterSubject(tester, 'लोन समस्या',
        description: 'किसान क्रेडिट कार्ड चाहिए');
    await submit(tester);

    expect(find.text(AppStrings.feedbackSubmitted), findsOneWidget);
    expect(find.text('लोन समस्या'), findsOneWidget);
    expect(find.text('किसान क्रेडिट कार्ड चाहिए'), findsOneWidget);
    expect(find.text('सिंचाई समस्या'), findsOneWidget);
  });

  testWidgets('chosen priority is included in the submitted payload',
      (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    await enterSubject(tester, 'अत्यावश्यक बीमा');
    await tester.tap(
      find.byType(DropdownButton<String>),
      warnIfMissed: false,
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text(AppStrings.severityHigh).last);
    await tester.pumpAndSettle();
    await submit(tester);

    expect(backend.lastFeedbackPayload?['priority'], 'high');
  });

  testWidgets('empty history shows the empty state', (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend()..myFeedback.clear();
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    expect(find.text(AppStrings.feedbackEmpty), findsOneWidget);
    expect(find.text('सिंचाई समस्या'), findsNothing);
  });

  testWidgets('network failure shows the retry view', (tester) async {
    useTallSurface(tester);
    final backend = FakeBackend()..failFeedback = true;
    await tester.pumpWidget(wrap(buildDeps(backend)));
    await tester.pumpAndSettle();

    expect(find.text(AppStrings.retry), findsOneWidget);
  });

  testWidgets('home card opens the feedback screen', (tester) async {
    useTallSurface(tester);
    final deps = buildDeps(FakeBackend());
    await tester.pumpWidget(KisanApp(dependencies: deps));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 2100));

    await tester.enterText(find.byType(TextFormField).first, 'ravi');
    await tester.enterText(find.byType(TextFormField).at(1), 'secret');
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    await tester.ensureVisible(find.text(AppStrings.feedbackCard));
    await tester.pump();
    await tester.tap(find.text(AppStrings.feedbackCard));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));
    await tester.pumpAndSettle();

    expect(find.text(AppStrings.feedbackSubjectLabel), findsOneWidget);
    expect(find.text(AppStrings.feedbackHistoryTitle), findsOneWidget);
  });
}