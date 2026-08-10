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

  testWidgets('empty submit shows local validation errors', (tester) async {
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));

    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();

    expect(find.text('उपयोगकर्ता नाम आवश्यक है'), findsOneWidget);
    expect(find.text('पासवर्ड आवश्यक है'), findsOneWidget);
  });

  testWidgets('wrong credentials show an error banner', (tester) async {
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));

    await tester.enterText(find.byType(TextFormField).first, 'ravi');
    await tester.enterText(find.byType(TextFormField).at(1), 'wrong-password');
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('उपयोगकर्ता नाम या पासवर्ड गलत है'), findsOneWidget);
    expect(controller.status, AuthStatus.unauthenticated);
  });

  testWidgets('valid credentials authenticate without an error banner',
      (tester) async {
    final (controller, _) = build(FakeBackend());
    await tester.pumpWidget(wrap(controller));

    await tester.enterText(find.byType(TextFormField).first, 'ravi');
    await tester.enterText(find.byType(TextFormField).at(1), 'secret');
    await tester.tap(find.byType(ElevatedButton));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('उपयोगकर्ता नाम या पासवर्ड गलत है'), findsNothing);
    expect(controller.status, AuthStatus.authenticated);
  });
}
