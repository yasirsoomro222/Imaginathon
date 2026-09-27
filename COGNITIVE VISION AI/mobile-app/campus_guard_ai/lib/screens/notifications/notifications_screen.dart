import 'dart:async';
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../services/api_service.dart';

class NotificationsScreen extends StatefulWidget {
  final int studentId;
  const NotificationsScreen({super.key, this.studentId = 1});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<Map<String, dynamic>> notifications = [];
  int unreadCount = 0;
  bool isLoading = true;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    loadNotifications();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) => loadNotifications());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> loadNotifications() async {
    final data = await ApiService.fetchNotifications(widget.studentId);
    if (!mounted) return;
    setState(() {
      notifications = List<Map<String, dynamic>>.from(data['notifications'] ?? []);
      unreadCount = data['unread_count'] ?? 0;
      isLoading = false;
    });
  }

  Future<void> markAsRead(int notificationId) async {
    final ok = await ApiService.markNotificationRead(notificationId);
    if (ok) loadNotifications();
  }

  IconData _iconForType(String? type) {
    switch (type) {
      case 'warning':
        return Icons.warning_amber_rounded;
      case 'chalan':
        return Icons.receipt_long;
      default:
        return Icons.notifications;
    }
  }

  Color _colorForType(String? type) {
    switch (type) {
      case 'warning':
        return Colors.orangeAccent;
      case 'chalan':
        return Colors.redAccent;
      default:
        return AppColors.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text(
          "Notifications",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        actions: [
          if (unreadCount > 0)
            Center(
              child: Container(
                margin: const EdgeInsets.only(right: 16),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.redAccent,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  "$unreadCount new",
                  style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                ),
              ),
            ),
        ],
      ),
      body: RefreshIndicator(
        color: AppColors.primary,
        backgroundColor: AppColors.card,
        onRefresh: loadNotifications,
        child: isLoading
            ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
            : notifications.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.notifications_off, size: 70, color: Colors.white.withValues(alpha: 0.3)),
                        const SizedBox(height: 16),
                        const Text(
                          "No notifications yet",
                          style: TextStyle(color: Colors.white70, fontSize: 16),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: notifications.length,
                    itemBuilder: (context, index) {
                      final n = notifications[index];
                      final isRead = n['is_read'] == 1;
                      return Card(
                        color: isRead ? AppColors.card : AppColors.card.withValues(alpha: 0.95),
                        elevation: isRead ? 2 : 6,
                        margin: const EdgeInsets.only(bottom: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: ListTile(
                          contentPadding: const EdgeInsets.all(16),
                          leading: CircleAvatar(
                            radius: 26,
                            backgroundColor: _colorForType(n['type']).withValues(alpha: 0.15),
                            child: Icon(_iconForType(n['type']), color: _colorForType(n['type'])),
                          ),
                          title: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  n['title'] ?? "Notification",
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontWeight: isRead ? FontWeight.w500 : FontWeight.bold,
                                    fontSize: 15,
                                  ),
                                ),
                              ),
                              if (!isRead)
                                Container(
                                  width: 10,
                                  height: 10,
                                  decoration: const BoxDecoration(
                                    color: Colors.redAccent,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                            ],
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 6),
                              Text(
                                n['message'] ?? "",
                                style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                n['created_at'] ?? "",
                                style: const TextStyle(color: Colors.white38, fontSize: 11),
                              ),
                            ],
                          ),
                          onTap: () => markAsRead(n['id']),
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}
