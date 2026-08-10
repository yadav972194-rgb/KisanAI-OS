/// Models for the auth domain (`/api/auth/*`).
library;

/// Parsed `POST /api/auth/token` response.
class AuthToken {
  const AuthToken({required this.accessToken, required this.tokenType});

  final String accessToken;
  final String tokenType;

  factory AuthToken.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return AuthToken(
      accessToken: map['access_token'] as String,
      tokenType: map['token_type'] as String? ?? 'bearer',
    );
  }
}

/// Parsed user record (`UserOut`).
class AuthUser {
  const AuthUser({
    required this.id,
    required this.username,
    required this.fullName,
    required this.mobile,
    required this.role,
    required this.isActive,
    required this.createdAt,
  });

  final int id;
  final String username;
  final String? fullName;
  final String? mobile;
  final String role;
  final bool isActive;
  final String createdAt;

  factory AuthUser.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return AuthUser(
      id: (map['id'] as num).toInt(),
      username: map['username'] as String? ?? '',
      fullName: map['full_name'] as String?,
      mobile: map['mobile'] as String?,
      role: map['role'] as String? ?? 'farmer',
      isActive: map['is_active'] as bool? ?? true,
      createdAt: map['created_at'] as String? ?? '',
    );
  }

  /// Display name: full name if present, else username.
  String get displayName => (fullName?.isNotEmpty ?? false) ? fullName! : username;
}
