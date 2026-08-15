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
    this.failMyFarm = false,
    this.failLogout = false,
    this.existingUsernames = const {'ravi'},
  });

  final String validPassword;
  String detectStatus;
  String recommendationStatus;
  bool failWeather;
  bool failLogin;
  bool failMyFarm;
  bool failLogout;
  final Set<String> existingUsernames;
  int logoutCalls = 0;
  int weatherCalls = 0;

  /// In-memory state for `/api/my-farm` (mirrors the real farm table).
  Map<String, dynamic>? myFarm;
  final List<Map<String, dynamic>> myCrops = [];
  int _nextCropId = 1;

  MockClient client() => MockClient((request) async {
        if (failLogin) {
          throw http.ClientException('connection refused');
        }
        final path = request.url.path;
        switch (path) {
          case '/api/auth/token':            if (request.body.contains('password=$validPassword')) {
              return jsonResponse({
                'access_token': 'test-token',
                'token_type': 'bearer',
              });
            }
            return jsonResponse(
              {
                'detail': {
                  'success': false,
                  'message': 'Invalid credentials',
                  'code': 'AUTH_INVALID',
                },
              },
              status: 401,
            );
          case '/api/auth/register':
            final data = jsonDecode(request.body) as Map<String, dynamic>;
            final username = (data['username'] as String? ?? '').trim();
            if (existingUsernames.contains(username)) {
              return jsonResponse(
                {
                  'detail': {
                    'success': false,
                    'message': 'Username already exists',
                    'code': 'CONFLICT',
                  },
                },
                status: 409,
              );
            }
            return jsonResponse({
              'id': 2,
              'username': username,
              'full_name': data['full_name'],
              'mobile': data['mobile'],
              'role': data['role'] ?? 'farmer',
              'is_active': true,
              'created_at': '2026-08-11T00:00:00',
            });
          case '/api/auth/me':
            return jsonResponse(defaultUser);
          case '/api/auth/otp/request':
            return jsonResponse({
              'success': true,
              'message': 'OTP sent successfully (development mock)',
              'ttl_seconds': 300,
              'dev_otp': '123456',
            });
          case '/api/auth/reset-password':
            return jsonResponse({
              'success': true,
              'message': 'Password updated successfully',
            });
          case '/api/auth/logout':
            logoutCalls++;
            if (failLogout) {
              throw http.ClientException('connection refused');
            }
            return jsonResponse({
              'success': true,
              'message': 'Logged out successfully',
            });
          case '/api/assistant':
            final data = jsonDecode(request.body) as Map<String, dynamic>;
            final text = (data['text'] as String? ?? '');
            if (text.contains('मौसम')) {
              return jsonResponse({
                'intent': 'WEATHER',
                'status': 'OK',
                'message': 'Delhi में अभी मौसम: Clear, तापमान 28.5°C, नमी 60%।',
                'data': defaultWeather,
              });
            }
            if (myFarm == null || myCrops.isEmpty) {
              return jsonResponse({
                'intent': 'CROP_STATUS',
                'status': 'INSUFFICIENT_DATA',
                'message':
                    'आपकी फसल की पूरी स्थिति बताने के लिए पहले अपनी फसल की जानकारी दर्ज करें।',
                'data': {'missing': ['farm', 'crops']},
              });
            }
            return jsonResponse({
              'intent': 'CROP_STATUS',
              'status': 'OK',
              'message': 'आपके खेत में फसलें: ${myCrops.map((c) => c['crop_name']).join(', ')}।',
              'data': {
                'farm': {
                  'village': myFarm!['village'],
                  'district': myFarm!['district'],
                  'state': myFarm!['state'],
                  'farm_size': myFarm!['farm_size'],
                },
                'crops': [
                  for (final c in myCrops)
                    {'crop_name': c['crop_name'], 'season': c['season']},
                ],
                'weather': defaultWeather,
              },
            });
          case '/api/weather':
            weatherCalls++;
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
          case '/api/my-farm':
            return _myFarm(request);
          case '/api/my-farm/crops':
            return _myFarmCrops(request);
          default:
            if (path.startsWith('/api/my-farm/crops/')) {
              return _myFarmCropById(request);
            }
            return jsonResponse({'message': 'not found'}, status: 404);
        }
      });

  http.Response _myFarm(http.Request request) {
    if (failMyFarm) {
      throw http.ClientException('connection refused');
    }
    switch (request.method) {
      case 'GET':
        if (myFarm == null) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Farm Not Found'}},
            status: 404,
          );
        }
        return jsonResponse(myFarm);
      case 'POST':
        if (myFarm != null) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Farm already exists'}},
            status: 409,
          );
        }
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        myFarm = {
          'farmer_id': 1,
          'user_id': 1,
          'name': defaultUser['full_name'],
          'mobile': defaultUser['mobile'],
          'village': data['village'],
          'district': data['district'],
          'state': data['state'],
          'farm_size': data['farm_size'],
          'created_at': '2026-08-11T00:00:00',
          'crops': <Map<String, dynamic>>[],
        };
        return jsonResponse({'success': true, 'message': 'Farm Created Successfully'});
      case 'PUT':
        if (myFarm == null) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Farm Not Found'}},
            status: 404,
          );
        }
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        if (data.containsKey('village')) myFarm!['village'] = data['village'];
        if (data.containsKey('district')) myFarm!['district'] = data['district'];
        if (data.containsKey('state')) myFarm!['state'] = data['state'];
        if (data.containsKey('farm_size')) {
          myFarm!['farm_size'] = data['farm_size'];
        }
        return jsonResponse({'success': true, 'message': 'Farm Updated Successfully'});
      case 'DELETE':
        if (myFarm == null) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Farm Not Found'}},
            status: 404,
          );
        }
        myFarm = null;
        myCrops.clear();
        return jsonResponse({'success': true, 'message': 'Farm Deleted Successfully'});
      default:
        return jsonResponse({'message': 'not found'}, status: 404);
    }
  }

  http.Response _myFarmCrops(http.Request request) {
    if (failMyFarm) {
      throw http.ClientException('connection refused');
    }
    switch (request.method) {
      case 'GET':
        if (myFarm == null) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Farm Not Found'}},
            status: 404,
          );
        }
        return jsonResponse(myCrops);
      case 'POST':
        if (myFarm == null) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Farm Not Found'}},
            status: 404,
          );
        }
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        final name = (data['crop_name'] as String? ?? '').trim();
        if (myCrops.any((c) => c['crop_name'] == name)) {
          return jsonResponse(
            {
              'detail': {
                'success': false,
                'message': 'Crop already added to this farm',
              },
            },
            status: 409,
          );
        }
        final crop = <String, dynamic>{
          'crop_id': _nextCropId++,
          'farmer_id': 1,
          'crop_name': name,
          'season': data['season'],
          'duration_days': data['duration_days'],
          'water_requirement': data['water_requirement'],
          'created_at': '2026-08-11T00:00:00',
        };
        myCrops.add(crop);
        (myFarm!['crops'] as List).add(crop);
        return jsonResponse({'success': true, 'message': 'Crop Added Successfully'});
      default:
        return jsonResponse({'message': 'not found'}, status: 404);
    }
  }

  http.Response _myFarmCropById(http.Request request) {
    final cropId =
        int.tryParse(request.url.pathSegments.last) ?? -1;
    final index = myCrops.indexWhere((c) => c['crop_id'] == cropId);
    switch (request.method) {
      case 'PUT':
        if (myFarm == null || index < 0) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Crop Not Found'}},
            status: 404,
          );
        }
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        final name = (data['crop_name'] as String? ?? '').trim();
        if (myCrops.any((c) => c['crop_name'] == name && c['crop_id'] != cropId)) {
          return jsonResponse(
            {
              'detail': {
                'success': false,
                'message': 'Crop already added to this farm',
              },
            },
            status: 409,
          );
        }
        myCrops[index]['crop_name'] = name;
        myCrops[index]['season'] = data['season'];
        myCrops[index]['duration_days'] = data['duration_days'];
        myCrops[index]['water_requirement'] = data['water_requirement'];
        return jsonResponse({'success': true, 'message': 'Crop Updated Successfully'});
      case 'DELETE':
        if (myFarm == null || index < 0) {
          return jsonResponse(
            {'detail': {'success': false, 'message': 'Crop Not Found'}},
            status: 404,
          );
        }
        myCrops.removeAt(index);
        return jsonResponse({'success': true, 'message': 'Crop Deleted Successfully'});
      default:
        return jsonResponse({'message': 'not found'}, status: 404);
    }
  }
}
