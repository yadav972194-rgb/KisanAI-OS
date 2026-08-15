import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/core/storage/token_storage.dart';
import 'package:kisanai/features/auth/auth_controller.dart';
import 'package:kisanai/features/auth/login_screen.dart';
import 'package:kisanai/services/auth_api.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';

void main() {
  (AuthController, InMemoryTokenStorage) build(FakeBackend backend) {
    final storage = InMemoryTokenStorage();
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
      tokenProvider: storage.read,
    );
    return (AuthController(AuthApi(client), storage), storage);
  }

  Widget wrap(AuthController controller) {
    return ChangeNotifierProvider<AuthController>.value(
      value: controller,
      child: const MaterialApp(home: LoginScreen()),
    );
  }

  // A tall viewport so every form field and button is laid out and hittable.
  void useTallSurface(WidgetTester tester) {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
  }

  Future<void> openRegister(WidgetTester tester) async {
    await tester.ensureVisible(find.text('नया अकाउंट बनाएं'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('नया अकाउंट बनाएं'));
    await tester.pumpAndSettle();
  }

  Future<void> submit(WidgetTester tester) async {
    await tester.ensureVisible(find.byType(ElevatedButton));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));
  }

  Future<void> fillForm(
    WidgetTester tester, {
    String fullName = 'Naya Kisan',
    String mobile = '9876500000',
    String username = 'newfarmer',
    String password = 'secret123',
  }) async {
    await tester.enterText(find.byType(TextFormField).at(0), fullName);
    await tester.enterText(find.byType(TextFormField).at(1), mobile);
    await tester.enterText(find.byType(TextFormField).at(2), username);
    await tester.enterText(find.byType(TextFormField).at(3), password);
    await tester.enterText(find.byType(TextFormField).at(4), password);
  }

  testWidgets('sign-up link opens the registration screen', (tester) async {
    useTallSurface(tester);
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));
    await openRegister(tester);

    expect(find.text('अकाउंट बनाएं'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(5));
  });

  testWidgets('empty submit shows local validation errors', (tester) async {
    useTallSurface(tester);
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));
    await openRegister(tester);

    await submit(tester);

    expect(find.text('पूरा नाम आवश्यक है'), findsOneWidget);
    expect(find.text('सही 10 अंकों का मोबाइल नंबर दर्ज करें'), findsWidgets);
    expect(find.text('उपयोगकर्ता नाम आवश्यक है'), findsOneWidget);
    expect(find.text('पासवर्ड आवश्यक है'), findsOneWidget);
    expect(find.text('पासवर्ड दोबारा दर्ज करें'), findsOneWidget);
  });

  testWidgets('mismatched confirm password is rejected', (tester) async {
    useTallSurface(tester);
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));
    await openRegister(tester);

    await tester.enterText(find.byType(TextFormField).at(0), 'Naya Kisan');
    await tester.enterText(find.byType(TextFormField).at(1), '9876500000');
    await tester.enterText(find.byType(TextFormField).at(2), 'newfarmer');
    await tester.enterText(find.byType(TextFormField).at(3), 'secret123');
    await tester.enterText(find.byType(TextFormField).at(4), 'different');
    await submit(tester);

    expect(find.text('पासवर्ड मेल नहीं खाते'), findsOneWidget);
  });

  testWidgets('duplicate username shows a friendly 409 message',
      (tester) async {
    useTallSurface(tester);
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));
    await openRegister(tester);

    await fillForm(tester, username: 'ravi');
    await submit(tester);

    expect(find.text('यह username या mobile number पहले से मौजूद है।'),
        findsOneWidget);
    expect(find.text('अकाउंट बनाएं'), findsOneWidget);
  });

  testWidgets('successful registration returns to login with a success message',
      (tester) async {
    useTallSurface(tester);
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));
    await openRegister(tester);

    await fillForm(tester);
    await submit(tester);
    await tester.pumpAndSettle();

    expect(find.text('लॉगिन करें'), findsOneWidget);
    expect(find.text('अकाउंट बन गया! अब लॉगिन करें।'), findsOneWidget);
    expect(find.text('newfarmer'), findsOneWidget);
  });
}
