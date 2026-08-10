import 'package:flutter_test/flutter_test.dart';
import 'package:kisanai/models/auth_models.dart';
import 'package:kisanai/models/crop.dart';
import 'package:kisanai/models/disease.dart';
import 'package:kisanai/models/disease_detection.dart';
import 'package:kisanai/models/farmer.dart';
import 'package:kisanai/models/recommendation.dart';
import 'package:kisanai/models/soil.dart';
import 'package:kisanai/models/weather.dart';

void main() {
  group('models parse backend JSON', () {
    test('AuthToken.fromJson', () {
      final token = AuthToken.fromJson({
        'access_token': 'abc',
        'token_type': 'bearer',
      });
      expect(token.accessToken, 'abc');
      expect(token.tokenType, 'bearer');
    });

    test('AuthUser.fromJson', () {
      final user = AuthUser.fromJson({
        'id': 3,
        'username': 'ravi',
        'full_name': 'Ravi Kumar',
        'mobile': '9876543210',
        'role': 'farmer',
        'is_active': true,
        'created_at': '2026-01-01T00:00:00',
      });
      expect(user.id, 3);
      expect(user.username, 'ravi');
      expect(user.role, 'farmer');
      expect(user.isActive, true);
      expect(user.displayName, 'Ravi Kumar');
    });

    test('AuthUser.fromJson tolerates missing optional fields', () {
      final user = AuthUser.fromJson({'id': 1, 'username': 'a'});
      expect(user.fullName, isNull);
      expect(user.role, 'farmer');
      expect(user.isActive, true);
    });

    test('Weather.fromJson', () {
      final weather = Weather.fromJson({
        'location': 'Delhi',
        'temperature': 28.5,
        'humidity': 60,
        'condition': 'Clear',
        'wind_speed': 12.0,
        'updated_at': '2026-08-10T09:00:00',
      });
      expect(weather.location, 'Delhi');
      expect(weather.temperature, 28.5);
      expect(weather.humidity, 60);
      expect(weather.windSpeed, 12.0);
    });

    test('Crop.fromJson', () {
      final crop = Crop.fromJson({
        'crop_id': 7,
        'farmer_id': 1,
        'crop_name': 'गेहूँ',
        'season': 'Rabi',
        'duration_days': 120,
        'water_requirement': 'Medium',
        'created_at': 'x',
      });
      expect(crop.cropId, 7);
      expect(crop.cropName, 'गेहूँ');
      expect(crop.durationDays, 120);
    });

    test('Soil.fromJson', () {
      final soil = Soil.fromJson({
        'soil_id': 2,
        'soil_type': 'Loamy',
        'ph': 6.5,
        'moisture': 45.0,
        'nitrogen': 50,
        'phosphorus': 30,
        'potassium': 40,
        'created_at': 'x',
      });
      expect(soil.soilType, 'Loamy');
      expect(soil.ph, 6.5);
      expect(soil.potassium, 40);
    });

    test('Farmer.fromJson with nested crops', () {
      final farmer = Farmer.fromJson({
        'farmer_id': 4,
        'name': 'Sita',
        'mobile': '9812345678',
        'village': 'Ramnagar',
        'district': 'Palwal',
        'state': 'Haryana',
        'created_at': 'x',
        'crops': [
          {
            'crop_id': 1,
            'crop_name': 'सरसों',
            'season': 'Rabi',
            'duration_days': 90,
            'water_requirement': 'Low',
            'created_at': 'x',
          },
        ],
      });
      expect(farmer.farmerId, 4);
      expect(farmer.crops, hasLength(1));
      expect(farmer.crops.first.cropName, 'सरसों');
      expect(farmer.locationSummary, 'Ramnagar, Palwal');
    });

    test('Disease.fromJson', () {
      final disease = Disease.fromJson({
        'disease_id': 9,
        'crop_id': 1,
        'crop_name': 'गेहूँ',
        'disease_name': 'काला रतुआ',
        'symptoms': 'पत्तियों पर धब्बे',
        'solution': 'फफूंदनाशक छिड़कें',
        'severity': 'High',
        'created_at': 'x',
      });
      expect(disease.diseaseName, 'काला रतुआ');
      expect(disease.severity, 'High');
    });

    test('DiseaseDetectionResult parses MODEL_NOT_CONFIGURED', () {
      final result = DiseaseDetectionResult.fromJson({
        'success': true,
        'status': 'MODEL_NOT_CONFIGURED',
        'message': 'no model',
      });
      expect(result.isModelNotConfigured, isTrue);
      expect(result.isHealthy, isFalse);
      expect(result.diseaseName, isNull);
    });

    test('DiseaseDetectionResult parses HEALTHY and DISEASE_DETECTED', () {
      final healthy = DiseaseDetectionResult.fromJson(
          {'success': true, 'status': 'HEALTHY'});
      expect(healthy.isHealthy, isTrue);

      final detected = DiseaseDetectionResult.fromJson({
        'success': true,
        'status': 'DISEASE_DETECTED',
        'disease_name': 'रतुआ',
        'confidence': 0.93,
      });
      expect(detected.isDiseaseDetected, isTrue);
      expect(detected.diseaseName, 'रतुआ');
      expect(detected.confidence, 0.93);
    });

    test('RecommendationInput.toJson omits null fields', () {
      const input = RecommendationInput(cropName: 'गेहूँ', ph: 6.5);
      final json = input.toJson();
      expect(json['crop_name'], 'गेहूँ');
      expect((json['soil'] as Map)['ph'], 6.5);
      expect(json['soil'].containsKey('moisture'), isFalse);
      expect(json.containsKey('weather'), isFalse);
      expect(json.containsKey('disease'), isFalse);
    });

    test('RecommendationResult parses items, warnings and status', () {
      final result = RecommendationResult.fromJson({
        'success': true,
        'status': 'RECOMMENDATION_AVAILABLE',
        'recommendation_type': 'general',
        'recommendations': [
          {
            'category': 'जल',
            'text': 'पानी दें',
            'reason': 'नमी कम',
            'source': 'engine',
          },
        ],
        'warnings': ['w1'],
        'required_context': <String>[],
        'missing': <String>[],
        'message': '',
      });
      expect(result.isInsufficientData, isFalse);
      expect(result.hasRecommendations, isTrue);
      expect(result.recommendations.first.category, 'जल');
      expect(result.warnings, ['w1']);
    });

    test('RecommendationResult flags INSUFFICIENT_DATA', () {
      final result = RecommendationResult.fromJson({
        'success': true,
        'status': 'INSUFFICIENT_DATA',
        'recommendations': [],
        'required_context': ['crop_name'],
        'missing': ['crop_name'],
      });
      expect(result.isInsufficientData, isTrue);
      expect(result.missing, ['crop_name']);
    });
  });
}
