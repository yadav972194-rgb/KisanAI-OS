import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/core/config/app_config.dart';

void main() {
  group('AppConfig base URL resolution', () {
    test('A: production configuration resolves to the Render backend', () {
      expect(
        AppConfig.resolveApiBaseUrl(isRelease: true, override: ''),
        'https://kisanai-os.onrender.com',
      );
      expect(AppConfig.productionApiBaseUrl, 'https://kisanai-os.onrender.com');
    });

    test('B: release builds never resolve to a loopback/localhost URL', () {
      for (final loopback in [
        'http://127.0.0.1:8712',
        'http://localhost:8712',
        '127.0.0.1:8712',
        'localhost:8712',
        'http://0.0.0.0:8712',
        'http://10.0.2.2:8000',
      ]) {
        final url = AppConfig.resolveApiBaseUrl(isRelease: true, override: loopback);
        expect(url, 'https://kisanai-os.onrender.com',
            reason: 'loopback override "$loopback" must not leak into release');
      }
    });

    test('B2: an empty override on release means production, never localhost',
        () {
      final url = AppConfig.apiBaseUrl;
      expect(url, isNot(contains('127.0.0.1')));
      expect(url, isNot(contains('localhost')));
    });

    test('C: local development resolves to http://127.0.0.1:8712 when selected',
        () {
      expect(AppConfig.localApiBaseUrl, 'http://127.0.0.1:8712');
      expect(
        AppConfig.resolveApiBaseUrl(
          isRelease: false,
          override: 'http://127.0.0.1:8712',
        ),
        'http://127.0.0.1:8712',
      );
    });

    test('C2: debug default is production, never an implicit localhost', () {
      final url = AppConfig.resolveApiBaseUrl(isRelease: false, override: '');
      expect(url, 'https://kisanai-os.onrender.com');
    });

    test('release honors an explicit non-loopback override (staging)', () {
      expect(
        AppConfig.resolveApiBaseUrl(
          isRelease: true,
          override: 'https://staging.example.com',
        ),
        'https://staging.example.com',
      );
    });
  });
}