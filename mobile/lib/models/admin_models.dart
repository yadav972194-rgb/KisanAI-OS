/// Models for the Admin Control & Farmer Support module (`/api/admin/*`).
library;

import 'farmer.dart';
import 'soil.dart';

/// Parsed `GET /api/admin/me` (`AdminMeOut`).
class AdminSummary {
  const AdminSummary({
    required this.id,
    required this.username,
    required this.role,
    required this.isSuperAdmin,
  });

  final int id;
  final String username;
  final String role;

  /// `users.super_admin` escalation flag (delete + privilege controls).
  final bool isSuperAdmin;

  factory AdminSummary.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return AdminSummary(
      id: (map['id'] as num).toInt(),
      username: map['username'] as String? ?? '',
      role: map['role'] as String? ?? 'admin',
      isSuperAdmin: map['super_admin'] as bool? ?? false,
    );
  }
}

/// Parsed `GET /api/admin/farmers/{id}` (`FarmerProfileOut`).
class FarmerProfile {
  const FarmerProfile({
    required this.farmer,
    required this.soils,
    required this.contacts,
    required this.feedback,
  });

  final Farmer farmer;
  final List<Soil> soils;
  final List<ContactRecord> contacts;
  final List<FeedbackItem> feedback;

  factory FarmerProfile.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return FarmerProfile(
      farmer: Farmer.fromJson(map['farmer']),
      soils: _parse(map['soils'], Soil.fromJson),
      contacts: _parse(map['contacts'], ContactRecord.fromJson),
      feedback: _parse(map['feedback'], FeedbackItem.fromJson),
    );
  }
}

/// Parsed `POST /api/admin/farmers/{id}/contacts` (`ContactOut`).
class ContactRecord {
  const ContactRecord({
    required this.contactId,
    required this.farmerId,
    required this.channel,
    this.reason,
    this.note,
    this.createdBy,
    required this.createdAt,
  });

  final int contactId;
  final int farmerId;
  final String channel;
  final String? reason;
  final String? note;
  final int? createdBy;
  final String createdAt;

  factory ContactRecord.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return ContactRecord(
      contactId: (map['contact_id'] as num).toInt(),
      farmerId: (map['farmer_id'] as num).toInt(),
      channel: map['channel'] as String? ?? '',
      reason: map['reason'] as String?,
      note: map['note'] as String?,
      createdBy: (map['created_by'] as num?)?.toInt(),
      createdAt: map['created_at'] as String? ?? '',
    );
  }
}

/// Parsed feedback/problem record (`FeedbackOut`).
class FeedbackItem {
  const FeedbackItem({
    required this.feedbackId,
    this.userId,
    this.farmerId,
    required this.subject,
    required this.description,
    required this.status,
    required this.priority,
    required this.createdAt,
    this.updatedAt,
  });

  final int feedbackId;
  final int? userId;
  final int? farmerId;
  final String subject;
  final String description;
  final String status;
  final String priority;
  final String createdAt;
  final String? updatedAt;

  factory FeedbackItem.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return FeedbackItem(
      feedbackId: (map['feedback_id'] as num).toInt(),
      userId: (map['user_id'] as num?)?.toInt(),
      farmerId: (map['farmer_id'] as num?)?.toInt(),
      subject: map['subject'] as String? ?? '',
      description: map['description'] as String? ?? '',
      status: map['status'] as String? ?? 'new',
      priority: map['priority'] as String? ?? 'medium',
      createdAt: map['created_at'] as String? ?? '',
      updatedAt: map['updated_at'] as String?,
    );
  }
}

/// Parsed notification / report / alert (`NotificationOut`).
class NotificationItem {
  const NotificationItem({
    required this.notificationId,
    this.userId,
    this.farmerId,
    required this.category,
    required this.title,
    required this.message,
    required this.status,
    this.createdBy,
    required this.createdAt,
    this.deliveredAt,
  });

  final int notificationId;
  final int? userId;
  final int? farmerId;
  final String category;
  final String title;
  final String message;
  final String status;
  final int? createdBy;
  final String createdAt;
  final String? deliveredAt;

  factory NotificationItem.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return NotificationItem(
      notificationId: (map['notification_id'] as num).toInt(),
      userId: (map['user_id'] as num?)?.toInt(),
      farmerId: (map['farmer_id'] as num?)?.toInt(),
      category: map['category'] as String? ?? '',
      title: map['title'] as String? ?? '',
      message: map['message'] as String? ?? '',
      status: map['status'] as String? ?? 'new',
      createdBy: (map['created_by'] as num?)?.toInt(),
      createdAt: map['created_at'] as String? ?? '',
      deliveredAt: map['delivered_at'] as String?,
    );
  }
}

/// Parsed `GET /api/admin/audit` entry (`AuditOut`).
class AuditEntry {
  const AuditEntry({
    required this.auditId,
    this.actorUserId,
    required this.action,
    required this.entityType,
    this.entityId,
    required this.details,
    required this.createdAt,
  });

  final int auditId;
  final int? actorUserId;
  final String action;
  final String entityType;
  final int? entityId;
  final Map<String, dynamic> details;
  final String createdAt;

  factory AuditEntry.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return AuditEntry(
      auditId: (map['audit_id'] as num).toInt(),
      actorUserId: (map['actor_user_id'] as num?)?.toInt(),
      action: map['action'] as String? ?? '',
      entityType: map['entity_type'] as String? ?? '',
      entityId: (map['entity_id'] as num?)?.toInt(),
      details: (map['details'] as Map?)?.cast<String, dynamic>() ?? const {},
      createdAt: map['created_at'] as String? ?? '',
    );
  }
}

/// Parsed `POST /api/admin/farmers/{id}/delete/preview` (`DeletePreviewOut`).
class DeletePreview {
  const DeletePreview({
    required this.farmerId,
    required this.name,
    required this.crops,
    required this.soils,
    required this.feedback,
    required this.contacts,
    required this.notifications,
  });

  final int farmerId;
  final String name;
  final int crops;
  final int soils;
  final int feedback;
  final int contacts;
  final int notifications;

  factory DeletePreview.fromJson(Object? json) {
    final map = json as Map<String, dynamic>;
    return DeletePreview(
      farmerId: (map['farmer_id'] as num).toInt(),
      name: map['name'] as String? ?? '',
      crops: (map['crops'] as num?)?.toInt() ?? 0,
      soils: (map['soils'] as num?)?.toInt() ?? 0,
      feedback: (map['feedback'] as num?)?.toInt() ?? 0,
      contacts: (map['contacts'] as num?)?.toInt() ?? 0,
      notifications: (map['notifications'] as num?)?.toInt() ?? 0,
    );
  }
}

List<T> _parse<T>(Object? value, T Function(Object?) fromJson) {
  if (value is! List) return const [];
  return value
      .whereType<Map<String, dynamic>>()
      .map(fromJson)
      .toList();
}