import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kisanai/core/network/api_client.dart';
import 'package:kisanai/services/location_api.dart';

http.Response listResponse(List<String> list) => http.Response(
      jsonEncode(list),
      200,
      headers: {'content-type': 'application/json'},
    );

void main() {
  group('LocationApi', () {
    test('fetchCountries returns the string list', () async {
      final client = MockClient((request) async {
        expect(request.url.path, '/api/locations/countries');
        return listResponse(['India']);
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      expect(await api.fetchCountries(), ['India']);
    });

    test('fetchStates returns the string list', () async {
      final client = MockClient((request) async {
        expect(request.url.path, '/api/locations/states');
        return listResponse(['Madhya Pradesh', 'Rajasthan']);
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      expect(await api.fetchStates(), ['Madhya Pradesh', 'Rajasthan']);
    });

    test('fetchDistricts sends the selected state as a query parameter',
        () async {
      final client = MockClient((request) async {
        expect(request.url.path, '/api/locations/districts');
        expect(request.url.queryParameters['state'], 'Madhya Pradesh');
        return listResponse(['Sehore', 'Bhopal']);
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      expect(await api.fetchDistricts('Madhya Pradesh'), ['Sehore', 'Bhopal']);
    });

    test('fetchBlocks sends the selected district as a query parameter',
        () async {
      final client = MockClient((request) async {
        expect(request.url.path, '/api/locations/blocks');
        expect(request.url.queryParameters['district'], 'Jaipur');
        return listResponse(['Jaipur Tehsil']);
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      expect(await api.fetchBlocks('Jaipur'), ['Jaipur Tehsil']);
    });

    test('duplicate and blank entries are dropped for safe dropdown values',
        () async {
      final client = MockClient((request) async {
        return listResponse(['Sehore', 'Sehore', '', '  ', 'Bhopal']);
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      expect(await api.fetchDistricts('Madhya Pradesh'), ['Sehore', 'Bhopal']);
    });

    test('queries are URL-encoded', () async {
      final client = MockClient((request) async {
        expect(request.url.path, '/api/locations/districts');
        expect(request.url.queryParameters['state'], 'Madhya Pradesh');
        return listResponse(const []);
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      await api.fetchDistricts('Madhya Pradesh');
    });

    test('fetchVillages sends the selected tehsil as a query parameter',
        () async {
      final client = MockClient((request) async {
        expect(request.url.path, '/api/locations/villages');
        expect(request.url.queryParameters['tehsil'], 'Jaipur Tehsil');
        return listResponse(['Amer', 'Sanganer']);
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      expect(await api.fetchVillages('Jaipur Tehsil'), ['Amer', 'Sanganer']);
    });

    test('fetchVillages degrades to empty on a missing endpoint (404)',
        () async {
      final client = MockClient((request) async {
        return http.Response(
          jsonEncode({'message': 'not found'}),
          404,
          headers: {'content-type': 'application/json'},
        );
      });
      final api =
          LocationApi(ApiClient(baseUrl: 'http://test.local', httpClient: client));
      expect(await api.fetchVillages('Jaipur Tehsil'), isEmpty);
    });
  });
}