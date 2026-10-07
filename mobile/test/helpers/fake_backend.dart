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
    this.detectionStatuses = const {},
    this.recommendationStatus = 'RECOMMENDATION_AVAILABLE',
    this.failWeather = false,
    this.failLogin = false,
    this.failMyFarm = false,
    this.failLogout = false,
    this.failAdmin = false,
    this.failFeedback = false,
    this.adminSuperAdmin = true,
    this.existingUsernames = const {'ravi'},
  });

  final String validPassword;
  String detectStatus;

  /// Per-path detection statuses for the crop-health detectors
  /// (`/api/pest/detect`, `/api/weed/detect`, ...). Falls back to
  /// [detectStatus] when a path is not present.
  Map<String, String> detectionStatuses;
  String recommendationStatus;
  bool failWeather;
  bool failLogin;
  bool failMyFarm;
  bool failLogout;
  bool failAdmin;
  bool failFeedback;
  bool adminSuperAdmin;
  final Set<String> existingUsernames;
  int logoutCalls = 0;
  int weatherCalls = 0;

  /// In-memory state for `/api/my-farm` (mirrors the real farm table).
  Map<String, dynamic>? myFarm;
  final List<Map<String, dynamic>> myCrops = [];
  int _nextCropId = 1;

  /// In-memory state for `/api/admin/*` (mirrors the real support module).
  Map<String, dynamic> adminFarmer = {
    'farmer_id': 1,
    'user_id': 1,
    'name': 'Ravi Kumar',
    'mobile': '9876543210',
    'village': 'Sanganer',
    'block': 'Jaipur Tehsil',
    'district': 'Jaipur',
    'state': 'Rajasthan',
    'country': 'India',
    'farm_size': 2.5,
    'created_at': '2026-08-11T00:00:00',
    'crops': <Map<String, dynamic>>[
      {
        'crop_id': 1,
        'farmer_id': 1,
        'crop_name': 'गेहूं',
        'season': 'रबी',
        'duration_days': 120,
        'water_requirement': 'मध्यम',
        'created_at': '2026-08-11T00:00:00',
      },
    ],
  };
  final List<Map<String, dynamic>> adminSoils = [
    {
      'soil_id': 1,
      'farmer_id': 1,
      'soil_type': 'काली',
      'ph': 6.5,
      'moisture': 30.0,
      'nitrogen': 120,
      'phosphorus': 40,
      'potassium': 160,
      'created_at': '2026-08-11T00:00:00',
    },
  ];
  List<Map<String, dynamic>> adminContacts = [];
  final List<Map<String, dynamic>> adminFeedback = [
    {
      'feedback_id': 1,
      'user_id': 1,
      'farmer_id': 1,
      'subject': 'सिंचाई समस्या',
      'description': 'पानी की कमी',
      'status': 'new',
      'priority': 'high',
      'created_at': '2026-08-12T00:00:00',
      'updated_at': null,
    },
  ];
  final List<Map<String, dynamic>> adminNotifications = [
    {
      'notification_id': 1,
      'user_id': 1,
      'farmer_id': 1,
      'category': 'ALERT',
      'title': 'मौसम चेतावनी',
      'message': 'कल भारी बारिश',
      'status': 'pending',
      'created_by': 1,
      'created_at': '2026-08-12T00:00:00',
      'delivered_at': null,
    },
  ];
  final List<Map<String, dynamic>> adminAudit = [
    {
      'audit_id': 1,
      'actor_user_id': 1,
      'action': 'farmer.update',
      'entity_type': 'farmer',
      'entity_id': 1,
      'details': {'mobile': '9876543210'},
      'created_at': '2026-08-12T00:00:00',
    },
  ];
  int _nextContactId = 1;
  int _nextFeedbackId = 2;

  /// In-memory state for `/api/feedback` (farmer self-service "Kisan ki Baat").
  ///
  /// Mirrors the real contract: only the authenticated user's own records are
  /// served, and a POST always binds ownership from the token (never from the
  /// client body).
  final List<Map<String, dynamic>> myFeedback = [
    {
      'feedback_id': 1,
      'user_id': 1,
      'farmer_id': 1,
      'subject': 'सिंचाई समस्या',
      'description': 'पानी की कमी',
      'status': 'new',
      'priority': 'high',
      'created_at': '2026-08-12T00:00:00',
      'updated_at': null,
    },
  ];

  /// The raw JSON body of the last `POST /api/feedback`, so tests can assert
  /// the client never sends a `farmer_id`/`user_id`.
  Map<String, dynamic>? lastFeedbackPayload;
  int _nextMyFeedbackId = 2;

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
          case '/api/pest/detect':
            return _detectionResponse(
              _statusFor('/api/pest/detect'),
              nameKey: 'pest_name',
            );
          case '/api/weed/detect':
            return _detectionResponse(
              _statusFor('/api/weed/detect'),
              nameKey: 'weed_name',
            );
          case '/api/nutrient-deficiency/detect':
            return _detectionResponse(
              _statusFor('/api/nutrient-deficiency/detect'),
              nameKey: 'deficiency_name',
            );
          case '/api/growth-stage/detect':
            return _detectionResponse(
              _statusFor('/api/growth-stage/detect'),
              nameKey: 'growth_stage',
            );
          case '/api/water-stress/detect':
            return _detectionResponse(
              _statusFor('/api/water-stress/detect'),
              nameKey: 'stress_level',
            );
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
          case '/api/feedback':
            return _myFeedback(request);
          default:
            if (path.startsWith('/api/my-farm/crops/')) {
              return _myFarmCropById(request);
            }
            if (path.startsWith('/api/admin')) {
              return _admin(request);
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

  http.Response _myFeedback(http.Request request) {
    if (failFeedback) {
      throw http.ClientException('connection refused');
    }
    switch (request.method) {
      case 'GET':
        final page =
            int.tryParse(request.url.queryParameters['page'] ?? '') ?? 1;
        final size =
            int.tryParse(request.url.queryParameters['size'] ?? '') ??
                myFeedback.length;
        final newestFirst = myFeedback.reversed.toList();
        final items = newestFirst
            .skip((page - 1) * size)
            .take(size)
            .toList();
        return jsonResponse({
          'items': items,
          'total': myFeedback.length,
          'page': page,
          'size': size,
        });
      case 'POST':
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        lastFeedbackPayload = data;
        final item = <String, dynamic>{
          'feedback_id': _nextMyFeedbackId++,
          'user_id': 1,
          'farmer_id': 1,
          'subject': data['subject'],
          'description': data['description'],
          'status': 'new',
          'priority': data['priority'] ?? 'medium',
          'created_at': '2026-08-13T00:00:00',
          'updated_at': null,
        };
        myFeedback.add(item);
        return jsonResponse(item);
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

  http.Response _admin(http.Request request) {
    if (failAdmin) {
      throw http.ClientException('connection refused');
    }
    final path = request.url.path;
    final segments = request.url.pathSegments;
    if (path == '/api/admin/me') {
      return jsonResponse({
        'id': 1,
        'username': 'admin',
        'role': 'admin',
        'super_admin': adminSuperAdmin,
      });
    }
    if (path == '/api/admin/farmers') {
      final q = (request.url.queryParameters['q'] ?? '').toLowerCase();
      final farmer = adminFarmer;
      final name = (farmer['name'] as String).toLowerCase();
      final village = (farmer['village'] as String).toLowerCase();
      final hits =
          q.isEmpty || name.contains(q) || village.contains(q);
      final list = hits ? [adminFarmer] : const <Map<String, dynamic>>[];
      return jsonResponse({
        'items': list,
        'total': list.length,
        'page': 1,
        'size': list.length,
      });
    }
    if (path.startsWith('/api/admin/farmers/')) {
      return _adminFarmer(request, segments);
    }
    if (path == '/api/admin/problems') {
      return _adminProblems(request);
    }
    if (path.startsWith('/api/admin/problems/')) {
      return _adminProblemById(request, segments);
    }
    if (path == '/api/admin/notifications') {
      return _adminNotifications(request);
    }
    if (path.startsWith('/api/admin/notifications/')) {
      return _adminNotificationById(request, segments[3]);
    }
    if (path == '/api/admin/audit') {
      return jsonResponse({
        'items': adminAudit,
        'total': adminAudit.length,
        'page': 1,
        'size': adminAudit.length,
      });
    }
    if (path.startsWith('/api/admin/users/')) {
      return _adminUser(request, segments);
    }
    return jsonResponse({'message': 'not found'}, status: 404);
  }

  http.Response _adminFarmer(http.Request request, List<String> segments) {
    final id = int.tryParse(segments[3]) ?? -1;
    final action = segments.length > 4 ? segments[4] : null;
    switch (request.method) {
      case 'GET':
        if (action == null) {
          return jsonResponse({
            'farmer': adminFarmer,
            'soils': adminSoils,
            'contacts': adminContacts,
            'feedback': adminFeedback
                .where((f) => f['farmer_id'] == id)
                .toList(),
          });
        }
        if (action == 'contacts') {
          final list = adminContacts
              .where((c) => c['farmer_id'] == id)
              .toList();
          return jsonResponse({
            'items': list,
            'total': list.length,
            'page': 1,
            'size': list.length,
          });
        }
        if (action == 'problems') {
          final list = adminFeedback
              .where((f) => f['farmer_id'] == id)
              .toList();
          return jsonResponse({
            'items': list,
            'total': list.length,
            'page': 1,
            'size': list.length,
          });
        }
        return jsonResponse({'message': 'not found'}, status: 404);
      case 'PUT':
        if (action == null) {
          final data = jsonDecode(request.body) as Map<String, dynamic>;
          for (final key in ['name', 'mobile', 'village', 'district', 'state']) {
            if (data.containsKey(key)) adminFarmer[key] = data[key];
          }
          if (data.containsKey('block')) adminFarmer['block'] = data['block'];
          if (data.containsKey('farm_size')) {
            adminFarmer['farm_size'] = data['farm_size'];
          }
          return jsonResponse({'success': true, 'message': 'Farmer updated'});
        }
        final subId = int.tryParse(segments[5]) ?? -1;
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        if (action == 'crops') {
          final crops = adminFarmer['crops'] as List<Map<String, dynamic>>;
          final index = crops.indexWhere((c) => c['crop_id'] == subId);
          if (index < 0) return jsonResponse({'message': 'not found'}, status: 404);
          crops[index] = {...crops[index], ...data};
          return jsonResponse({'success': true, 'message': 'Crop updated'});
        }
        if (action == 'soils') {
          final index = adminSoils.indexWhere((s) => s['soil_id'] == subId);
          if (index < 0) return jsonResponse({'message': 'not found'}, status: 404);
          adminSoils[index] = {...adminSoils[index], ...data};
          return jsonResponse({'success': true, 'message': 'Soil updated'});
        }
        return jsonResponse({'message': 'not found'}, status: 404);
      case 'POST':
        if (action == 'contacts') {
          final data = jsonDecode(request.body) as Map<String, dynamic>;
          final contact = {
            'contact_id': _nextContactId++,
            'farmer_id': id,
            'channel': data['channel'],
            'reason': data['reason'],
            'note': data['note'],
            'created_by': 1,
            'created_at': '2026-08-13T00:00:00',
          };
          adminContacts.add(contact);
          return jsonResponse(contact);
        }
        if (action == 'deactivate') {
          return jsonResponse({'success': true, 'message': 'Farmer deactivated'});
        }
        if (action == 'restore') {
          return jsonResponse({'success': true, 'message': 'Farmer restored'});
        }
        if (action == 'delete') {
          return jsonResponse({
            'farmer_id': id,
            'name': adminFarmer['name'],
            'crops': (adminFarmer['crops'] as List).length,
            'soils': adminSoils.length,
            'feedback': adminFeedback.length,
            'contacts': adminContacts.length,
            'notifications': adminNotifications.length,
          });
        }
        return jsonResponse({'message': 'not found'}, status: 404);
      case 'DELETE':
        return jsonResponse({'success': true, 'message': 'Farmer deleted'});
      default:
        return jsonResponse({'message': 'not found'}, status: 404);
    }
  }

  http.Response _adminProblems(http.Request request) {
    switch (request.method) {
      case 'GET':
        return jsonResponse({
          'items': adminFeedback,
          'total': adminFeedback.length,
          'page': 1,
          'size': adminFeedback.length,
        });
      case 'POST':
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        final item = {
          'feedback_id': _nextFeedbackId++,
          'user_id': 1,
          'farmer_id': data['farmer_id'],
          'subject': data['subject'],
          'description': data['description'],
          'status': 'new',
          'priority': data['priority'] ?? 'medium',
          'created_at': '2026-08-13T00:00:00',
          'updated_at': null,
        };
        adminFeedback.add(item);
        return jsonResponse(item);
      default:
        return jsonResponse({'message': 'not found'}, status: 404);
    }
  }

  http.Response _adminProblemById(http.Request request, List<String> segments) {
    final id = int.tryParse(segments[3]) ?? -1;
    final index = adminFeedback.indexWhere((f) => f['feedback_id'] == id);
    if (index < 0) return jsonResponse({'message': 'not found'}, status: 404);
    if (request.method == 'PUT') {
      final data = jsonDecode(request.body) as Map<String, dynamic>;
      for (final key in ['subject', 'description', 'priority']) {
        if (data.containsKey(key)) adminFeedback[index][key] = data[key];
      }
      adminFeedback[index]['updated_at'] = '2026-08-13T00:00:00';
      return jsonResponse(adminFeedback[index]);
    }
    if (request.method == 'PATCH' && segments[4] == 'status') {
      final data = jsonDecode(request.body) as Map<String, dynamic>;
      adminFeedback[index]['status'] = data['status'];
      adminFeedback[index]['updated_at'] = '2026-08-13T00:00:00';
      return jsonResponse(adminFeedback[index]);
    }
    return jsonResponse({'message': 'not found'}, status: 404);
  }

  http.Response _adminNotifications(http.Request request) {
    switch (request.method) {
      case 'GET':
        return jsonResponse({
          'items': adminNotifications,
          'total': adminNotifications.length,
          'page': 1,
          'size': adminNotifications.length,
        });
      case 'POST':
        final data = jsonDecode(request.body) as Map<String, dynamic>;
        final item = {
          'notification_id': adminNotifications.length + 1,
          'user_id': 1,
          'farmer_id': null,
          'category': data['category'],
          'title': data['title'],
          'message': data['message'],
          'status': 'pending',
          'created_by': 1,
          'created_at': '2026-08-13T00:00:00',
          'delivered_at': null,
        };
        adminNotifications.add(item);
        return jsonResponse(item);
      default:
        return jsonResponse({'message': 'not found'}, status: 404);
    }
  }

  http.Response _adminNotificationById(http.Request request, String idString) {
    final id = int.tryParse(idString) ?? -1;
    final index = adminNotifications.indexWhere((n) => n['notification_id'] == id);
    if (index < 0) return jsonResponse({'message': 'not found'}, status: 404);
    adminNotifications[index]['status'] = 'delivered';
    adminNotifications[index]['delivered_at'] = '2026-08-13T00:00:00';
    return jsonResponse({
      'success': true,
      'message': 'Notification marked as delivered',
    });
  }

  http.Response _adminUser(http.Request request, List<String> segments) {
    switch (request.method) {
      case 'POST':
        return jsonResponse({'success': true, 'message': 'User updated'});
      case 'DELETE':
        return jsonResponse({'success': true, 'message': 'User deleted'});
      default:
        return jsonResponse({'message': 'not found'}, status: 404);
    }
  }

  String _statusFor(String path) => detectionStatuses[path] ?? detectStatus;

  http.Response _detectionResponse(String status, {required String nameKey}) {
    final configured = status != 'MODEL_NOT_CONFIGURED';
    return jsonResponse({
      'success': true,
      'status': status,
      'crop': null,
      nameKey: configured ? 'sample-name' : null,
      'confidence': configured ? 0.87 : null,
      'model': null,
      'message': 'no model bundled',
    });
  }
}
