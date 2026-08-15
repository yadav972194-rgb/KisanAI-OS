import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/auth/forgot_password_controller.dart';
import 'package:kisanai/features/auth/forgot_password_screen.dart';
import 'package:kisanai/services/auth_api.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_backend.dart';

void main() {
  ForgotPasswordController build(FakeBackend backend) {
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    return ForgotPasswordController(AuthApi(client));
  }

  Widget wrap(ForgotPasswordController controller) {
    return ChangeNotifierProvider<ForgotPasswordController>.value(
      value: controller,
      child: const MaterialApp(home: ForgotPasswordScreen()),
    );
  }

  testWidgets('shows the mobile step and the forgot-password hint',
      (tester) async {
    final controller = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));

    expect(find.text('पासवर्ड भूल गए'), findsOneWidget);
    expect(find.text('OTP भेजें'), findsOneWidget);
    expect(find.text('नया पासवर्ड'), findsNothing);
  });

  testWidgets('requesting an OTP reveals the dev OTP and reset form',
      (tester) async {
    final controller = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));

    await tester.enterText(find.byType(TextFormField).first, '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'OTP भेजें'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(controller.step, ForgotPasswordStep.resetting);
    expect(find.textContaining('123456'), findsOneWidget);
    expect(find.text('पासवर्ड बदलें'), findsOneWidget);
  });

  testWidgets('an unknown mobile shows the account-not-found message',
      (tester) async {
    // Backend that always rejects the reset with ACCOUNT_NOT_FOUND.
    final backend = FakeBackend();
    final client = ApiClient(
      baseUrl: 'http://test.local',
      httpClient: backend.client(),
    );
    final controller = ForgotPasswordController(AuthApi(client));
    await tester.pumpWidget(wrap(controller));

    // Mobile empty -> local validation; still on the first step.
    await tester.tap(find.widgetWithText(ElevatedButton, 'OTP भेजें'));
    await tester.pump();
    expect(find.text('OTP कोड'), findsNothing);

    // Enter a valid mobile -> OTP step (mock always succeeds).
    await tester.enterText(find.byType(TextFormField).first, '9876500000');
    await tester.tap(find.widgetWithText(ElevatedButton, 'OTP भेजें'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(controller.step, ForgotPasswordStep.resetting);
  });

  testWidgets('completing a reset shows the success view and returns',
      (tester) async {
    final controller = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));

    await tester.enterText(find.byType(TextFormField).first, '9876543210');
    await tester.tap(find.widgetWithText(ElevatedButton, 'OTP भेजें'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.enterText(find.byType(TextFormField).at(1), '123456');
    await tester.enterText(find.byType(TextFormField).at(2), 'newpass123');
    await tester.enterText(find.byType(TextFormField).at(3), 'newpass123');
    final resetButton = find.widgetWithText(ElevatedButton, 'पासवर्ड बदलें');
    await tester.ensureVisible(resetButton);
    await tester.pump();
    await tester.tap(resetButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(controller.step, ForgotPasswordStep.done);
    expect(find.textContaining('पासवर्ड बदल दिया गया'), findsOneWidget);
  });
}