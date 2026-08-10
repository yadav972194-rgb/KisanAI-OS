/// Weather model (`WeatherOut`).
class Weather {
  const Weather({
    required this.location,
    required this.temperature,
    required this.humidity,
    required this.condition,
    required this.windSpeed,
    required this.updatedAt,
  });

  final String location;
  final double temperature;
  final int humidity;
  final String condition;
  final double windSpeed;
  final String updatedAt;

  factory Weather.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return Weather(
      location: map['location'] as String? ?? '',
      temperature: (map['temperature'] as num?)?.toDouble() ?? 0,
      humidity: (map['humidity'] as num?)?.toInt() ?? 0,
      condition: map['condition'] as String? ?? '',
      windSpeed: (map['wind_speed'] as num?)?.toDouble() ?? 0,
      updatedAt: map['updated_at'] as String? ?? '',
    );
  }
}
