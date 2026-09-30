import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/features/admin_admin/admin_controller.dart';
import 'package:kisanai/services/admin_api.dart';

import 'helpers/fake_backend.dart';

void main() {
  group('AdminController', () {
    (AdminController, FakeBackend) build(FakeBackend backend) {
      final client = ApiClient(
        baseUrl: 'http://test.local',
        httpClient: backend.client(),
      );
      return (AdminController(AdminApi(client)), backend);
    }

    test('loadSummary exposes super-admin privileges', () async {
      final (controller, _) = build(FakeBackend());
      expect(controller.isSuperAdmin, isFalse);
      await controller.loadSummary();
      expect(controller.summary, isNotNull);
      expect(controller.summary!.role, 'admin');
      expect(controller.isSuperAdmin, isTrue);
      expect(controller.summaryState, AdminViewState.ready);
    });

    test('summary reflects a base admin (super_admin=false)', () async {
      final (controller, _) = build(FakeBackend()..adminSuperAdmin = false);
      await controller.loadSummary();
      expect(controller.isSuperAdmin, isFalse);
    });

    test('loadSummary failure surfaces a connection error', () async {
      final (controller, _) = build(FakeBackend()..failAdmin = true);
      await controller.loadSummary();
      expect(controller.summary, isNull);
      expect(controller.summaryState, AdminViewState.error);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });

    test('loadFarmers populates the directory', () async {
      final (controller, _) = build(FakeBackend());
      await controller.loadFarmers();
      expect(controller.farmers, hasLength(1));
      expect(controller.farmers.first.name, 'Ravi Kumar');
      expect(controller.directoryState, AdminViewState.ready);
    });

    test('loadFarmers filters by query', () async {
      final (controller, _) = build(FakeBackend());
      await controller.loadFarmers(query: 'Sanganer');
      expect(controller.farmers, hasLength(1));
      await controller.loadFarmers(query: 'NoSuchVillage');
      expect(controller.farmers, isEmpty);
    });

    test('openFarmer loads profile, contacts and problems', () async {
      final (controller, _) = build(FakeBackend());
      await controller.openFarmer(1);
      expect(controller.profile, isNotNull);
      expect(controller.profile!.farmer.name, 'Ravi Kumar');
      expect(controller.profile!.soils, hasLength(1));
      expect(controller.profile!.feedback, hasLength(1));
      expect(controller.contacts, hasLength(0));
      expect(controller.problems, hasLength(1));
      expect(controller.profileState, AdminViewState.ready);
    });

    test('recordContact appends to the farmer contact list', () async {
      final (controller, _) = build(FakeBackend());
      await controller.openFarmer(1);
      final ok = await controller.recordContact(
        channel: 'phone',
        reason: 'फसल बीमा',
      );
      expect(ok, isTrue);
      expect(controller.contacts, hasLength(1));
      expect(controller.contacts.first.channel, 'phone');
    });

    test('createProblem refreshes the global problem list', () async {
      final (controller, _) = build(FakeBackend());
      await controller.loadProblems();
      expect(controller.problems, hasLength(1));
      final ok = await controller.createProblem(
        subject: 'नई समस्या',
        description: 'विवरण',
      );
      expect(ok, isTrue);
      expect(controller.problems, hasLength(2));
      expect(controller.problems.last.subject, 'नई समस्या');
    });

    test('transitionStatus moves a problem through the flow', () async {
      final (controller, _) = build(FakeBackend());
      await controller.loadProblems();
      expect(controller.problems.first.status, 'new');
      final ok = await controller.transitionStatus(1, 'resolved');
      expect(ok, isTrue);
      expect(controller.problems.first.status, 'resolved');
    });

    test('loadNotifications lists pending deliveries', () async {
      final (controller, _) = build(FakeBackend());
      await controller.loadNotifications();
      expect(controller.notifications, hasLength(1));
      expect(controller.notifications.first.category, 'ALERT');
      expect(controller.notifications.first.status, 'pending');
    });

    test('deliverNotification marks a notification as delivered', () async {
      final (controller, _) = build(FakeBackend());
      await controller.loadNotifications();
      final ok = await controller.deliverNotification(1);
      expect(ok, isTrue);
      expect(controller.notifications.first.status, 'delivered');
    });

    test('loadAudit surfaces the last admin actions', () async {
      final (controller, _) = build(FakeBackend());
      await controller.loadAudit();
      expect(controller.audit, hasLength(1));
      expect(controller.audit.first.action, 'farmer.update');
      expect(controller.auditState, AdminViewState.ready);
    });

    test('fetchDeletePreview returns the delete impact counts', () async {
      final (controller, _) = build(FakeBackend());
      final preview = await controller.fetchDeletePreview(1);
      expect(preview, isNotNull);
      expect(preview!.name, 'Ravi Kumar');
      expect(preview.crops, greaterThan(0));
    });

    test('deleteFarmer requires explicit confirmation', () async {
      final (controller, _) = build(FakeBackend());
      await controller.openFarmer(1);
      final denied = await controller.deleteFarmer(1, confirm: false);
      expect(denied, isTrue);
      expect(controller.profile, isNotNull);

      final confirmed = await controller.deleteFarmer(1, confirm: true);
      expect(confirmed, isTrue);
    });

    test('deactivateFarmer reports success and reloads the profile', () async {
      final (controller, _) = build(FakeBackend());
      await controller.openFarmer(1);
      final ok = await controller.deactivateFarmer(1);
      expect(ok, isTrue);
      expect(controller.profileState, AdminViewState.ready);
    });

    test('mutations surface error messages on failure', () async {
      final backend = FakeBackend();
      final (controller, _) = build(backend);
      await controller.loadProblems();
      backend.failAdmin = true;
      final ok = await controller.transitionStatus(1, 'resolved');
      expect(ok, isFalse);
      expect(controller.errorMessage, contains('नेटवर्क'));
    });
  });
}