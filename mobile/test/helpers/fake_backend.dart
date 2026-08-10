import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

http.Response jsonResponse(Object? body, {int status = 200}) {
  return http.Response(
    jsonEncode(body ?? const {}),
    status,
    headers: {'content-type': 'application/json'},
  );
}

const defaultUser = {
  'id': 1,
  'username': 'ravi',
  'full_name': 'Ravi Kumar',
  'mobile': '9876543210',
  'role': 'farmer',
  'is_active': true,
  'created_at': '2026-01-01T00:00:00',
};

const defaultWeather = {
  'location': 'Delhi',
  'temperature': 28.5,
  'humidity': 60,
  'condition': 'Clear',
  'wind_speed': 12.0,
  'updated_at': '2026-08-10T09:00:00',
};

/// A configurable fake backend covering every endpoint the app calls.
///
/// Mirrors the real FastAPI contract: form-encoded token login, JSON lists,
/// multipart detection, JSON recommendation engine.
class FakeBackend {
  FakeBackend({
    this.validPassword = 'secret',
    this.detectStatus = 'MODEL_NOT_CONFIGURED',
    this.recommendationStatus = 'RECOMMENDATION_AVAILABLE',
    this.failWeather = false,
    this.failLogin = false,
  });

  final String validPassword;
  String detectStatus;
  String recommendationStatus;
  bool failWeather;
  bool failLogin;

  MockClient client() => MockClient((request) async {
        if (failLogin) {
          throw http.ClientException('connection refused');
        }
        final path = request.url.path;
        switch (path) {
          case '/api/auth/token':
            if (request.body.contains('password=$validPassword')) {
              return jsonResponse({
                'access_token': 'test-token',
                'token_type': 'bearer',
              });
            }
            return jsonResponse(
              {'detail': {'success': false, 'message': 'Invalid credentials'}},
              status: 401,
            );
          case '/api/auth/me':
            return jsonResponse(defaultUser);
          case '/api/weather':
            if (failWeather) {
              throw http.ClientException('connection refused');
            }
            return jsonResponse(defaultWeather);
          case '/api/crops':
            return jsonResponse(const []);
          case '/api/soils':
            return jsonResponse(const []);
          case '/api/farmers':
            return jsonResponse(const []);
          case '/api/diseases':
            return jsonResponse(const []);
          case '/api/disease-detection':
            return jsonResponse({
              'success': true,
              'status': detectStatus,
              'crop': null,
              'disease_name': null,
              'confidence': null,
              'model': null,
              'message': 'no model bundled',
            });
          case '/api/recommendations':
            if (recommendationStatus == 'INSUFFICIENT_DATA') {
              return jsonResponse({
                'success': true,
                'status': 'INSUFFICIENT_DATA',
                'recommendation_type': 'general',
                'recommendations': [],
                'warnings': [],
                'required_context': ['crop_name', 'soil.ph'],
                'missing': ['crop_name'],
                'message': 'Missing context',
              });
            }
            return jsonResponse({
              'success': true,
              'status': recommendationStatus,
              'recommendation_type': 'general',
              'recommendations': [
                {
                  'category': 'जल',
                  'text': 'सुबह हल्की सिंचाई करें',
                  'reason': 'मिट्टी की नमी कम है',
                  'source': 'recommendation_engine',
                },
              ],
              'warnings': ['मौसम पूर्वानुमान उपलब्ध नहीं'],
              'required_context': [],
              'missing': [],
              'message': '',
            });
          default:
            return jsonResponse({'message': 'not found'}, status: 404);
        }
      });
}
