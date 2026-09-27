import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  // Web: http://localhost:8000
  // Android emulator: http://10.0.2.2:8000
  // Android real device: http://<PC's LAN IP>:8000
  static const String baseUrl = 'http://localhost:8000';

  static Future<Map<String, dynamic>> detectObject(Uint8List imageBytes) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/detect/object'),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          imageBytes,
          filename: 'upload.jpg',
        ),
      );

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        return {'success': false, 'message': 'Server error: ${response.statusCode}'};
      }
    } catch (e) {
      return {'success': false, 'message': 'Connection error: $e'};
    }
  }

  static Future<Map<String, dynamic>> detectSmoking(Uint8List imageBytes) async {
    // Unified endpoint for smoking + id card detection
    return detectObject(imageBytes);
  }

  static Future<Map<String, dynamic>> checkLiveStatus({String camera = 'classroom'}) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/live_status?camera=$camera'))
          .timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint("API Error: $e");
    }
    return {
      "camera": camera,
      "online": false,
      "smoking_detected": false,
      "id_card_missing": false,
      "confidence": 0.0,
    };
  }

  static Future<Uint8List?> fetchSnapshot(String camera) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/snapshot?camera=$camera'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return response.bodyBytes;
      }
    } catch (e) {
      debugPrint("Snapshot error: $e");
    }
    return null;
  }

  static Future<List<Map<String, dynamic>>> fetchAlerts() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/alerts'))
          .timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['alerts'] ?? []);
      }
    } catch (e) {
      debugPrint("Alerts fetch error: $e");
    }
    return [];
  }

  // ---------------- Student portal notifications ----------------
  static Future<Map<String, dynamic>> fetchNotifications(int studentId) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/portal/notifications/$studentId'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint("Notifications fetch error: $e");
    }
    return {"notifications": [], "unread_count": 0};
  }

  static Future<bool> markNotificationRead(int notificationId) async {
    try {
      final response = await http
          .post(Uri.parse('$baseUrl/portal/notifications/$notificationId/read'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      debugPrint("Mark read error: $e");
      return false;
    }
  }

  static Future<Map<String, dynamic>> fetchStudentByRoll(String rollNo) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/portal/student/$rollNo'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint("Student fetch error: $e");
    }
    return {"student": null};
  }

  // ---------------- Admin endpoints ----------------
  static Future<Map<String, dynamic>> sendWarning(
    int studentId, {
    String alertId = '',
    String camera = 'classroom',
    String reason = 'Smoking detected on campus',
    bool sendEmail = false,
    bool sendPortal = true,
  }) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/admin/send_warning'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'student_id': studentId,
              'alert_id': alertId,
              'camera': camera,
              'reason': reason,
              'send_email': sendEmail,
              'send_portal': sendPortal,
            }),
          )
          .timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint("Send warning error: $e");
    }
    return {'success': false};
  }

  static Future<Map<String, dynamic>> issueChalan(
    int studentId, {
    String alertId = '',
    String camera = 'classroom',
    String reason = 'Repeated smoking violation',
    int amount = 5000,
    bool sendEmail = false,
    bool sendPortal = true,
  }) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/admin/issue_chalan'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'student_id': studentId,
              'alert_id': alertId,
              'camera': camera,
              'reason': reason,
              'amount': amount,
              'send_email': sendEmail,
              'send_portal': sendPortal,
            }),
          )
          .timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint("Issue chalan error: $e");
    }
    return {'success': false};
  }

  static Future<List<Map<String, dynamic>>> fetchWarnings() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/admin/warnings'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['warnings'] ?? []);
      }
    } catch (e) {
      debugPrint("Warnings fetch error: $e");
    }
    return [];
  }

  static Future<List<Map<String, dynamic>>> fetchChalans() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/admin/chalans'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['chalans'] ?? []);
      }
    } catch (e) {
      debugPrint("Chalans fetch error: $e");
    }
    return [];
  }

  static Future<List<Map<String, dynamic>>> fetchStudents() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/admin/students'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(data['students'] ?? []);
      }
    } catch (e) {
      debugPrint("Students fetch error: $e");
    }
    return [];
  }
}
