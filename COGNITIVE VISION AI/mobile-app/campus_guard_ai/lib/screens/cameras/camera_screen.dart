import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../services/notification_service.dart';
import '../../widgets/mjpeg_view.dart';
import '../alerts/alerts_screen.dart';
import 'package:http/http.dart' as http;

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final ImagePicker _picker = ImagePicker();
  bool _isLoading = false;

  Timer? _detectionTimer;
  bool _isChecking = false;
  DateTime? _lastAlertTime;

  @override
  void initState() {
    super.initState();
    _startDetectionLoop();
  }

  @override
  void dispose() {
    _detectionTimer?.cancel();
    super.dispose();
  }

  void _startDetectionLoop() {
    _detectionTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
      _pollServerDetectionStatus();
    });
  }

  Future<void> _pollServerDetectionStatus() async {
    if (_isChecking) return;
    _isChecking = true;

    try {
      for (final camera in ['classroom', 'cafeteria']) {
        final response = await ApiService.checkLiveStatus(camera: camera);

        if (response['smoking_detected'] == true) {
          Uint8List? liveSnapBytes;
          try {
            final snapResponse = await http
                .get(Uri.parse('${ApiService.baseUrl}/snapshot?camera=$camera'))
                .timeout(const Duration(seconds: 5));
            if (snapResponse.statusCode == 200) {
              liveSnapBytes = snapResponse.bodyBytes;
            }
          } catch (e) {
            debugPrint("Snapshot fetch error: $e");
          }

          final alertId = response['latest_alert_id'] ?? '';

          _triggerAlert(
            camera == 'classroom' ? "Classroom Camera" : "Cafeteria Camera",
            liveSnapBytes,
            {
              "name": response['student_name'] ?? "Unknown Student",
              "rollNo": response['student_id'] ?? "N/A",
              "department": response['department'] ?? "Air Uni",
              "warnings": response['warnings'] ?? 0,
            },
            alertId: alertId,
          );
        }
      }
    } catch (e) {
      debugPrint("Live polling error: $e");
    } finally {
      _isChecking = false;
    }
  }

  void _triggerAlert(String cameraName, Uint8List? imageBytes, Map<String, dynamic> studentDetails, {String alertId = ''}) {
    final now = DateTime.now();
    if (_lastAlertTime == null || now.difference(_lastAlertTime!).inSeconds > 8) {
      _lastAlertTime = now;

      _playBeepSound();

      NotificationService.showAlertNotification(
        title: "Smoking Detected!",
        body: "Smoking detected at $cameraName. Tap to take action.",
        alertId: alertId,
      );

      String formattedTime = TimeOfDay.now().format(context);
      String formattedDate = "${now.day}/${now.month}/${now.year}";

      AlertManager.alertsList.insert(0, {
        "title": "Smoking Detected!",
        "location": cameraName,
        "time": formattedTime,
        "date": formattedDate,
        "priority": "HIGH",
        "color": Colors.red,
        "icon": Icons.smoking_rooms,
        "image": imageBytes,
        "student": studentDetails,
        "alert_id": alertId,
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("ALARM: Smoking detected in $cameraName! Check Alerts tab."),
            backgroundColor: Colors.redAccent,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
  }

  void _playBeepSound() {
    SystemSound.play(SystemSoundType.alert);
    HapticFeedback.vibrate();
    Future.delayed(const Duration(milliseconds: 300), () => HapticFeedback.vibrate());
    Future.delayed(const Duration(milliseconds: 600), () => HapticFeedback.vibrate());
  }

  Future<void> _testDetection(String cameraName) async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image == null) return;

    setState(() => _isLoading = true);
    var bytes = await image.readAsBytes();

    var result = await ApiService.detectSmoking(bytes);
    setState(() => _isLoading = false);

    if (!mounted) return;

    bool isDetected = result['smoking_detected'] == true;
    double confidence = (result['confidence'] ?? 0.0).toDouble();

    Map<String, dynamic> sampleStudent = {
      "name": "Muhammad Yasir Soomro",
      "rollNo": "234023",
      "department": "Software Engineering",
      "warnings": 1,
    };

    if (isDetected) {
      _triggerAlert(cameraName, bytes, sampleStudent);
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        backgroundColor: AppColors.card,
        child: Container(
          width: 450,
          padding: const EdgeInsets.all(20),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(
                          isDetected ? Icons.warning_amber_rounded : Icons.info_outline,
                          color: isDetected ? Colors.redAccent : Colors.greenAccent,
                          size: 28,
                        ),
                        const SizedBox(width: 10),
                        Text(
                          isDetected ? "SECURITY ALERT: Smoking!" : "$cameraName Result",
                          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white54),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
                const Divider(color: Colors.white24, height: 20),
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.memory(
                    bytes,
                    height: 180,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(height: 15),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: isDetected ? Colors.red.withValues(alpha: 0.1) : Colors.green.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: isDetected ? Colors.red.withValues(alpha: 0.3) : Colors.green.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      Text(
                        "Status: ${isDetected ? 'Detected' : 'Clean'}",
                        style: TextStyle(
                          color: isDetected ? Colors.redAccent : Colors.greenAccent,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (isDetected)
                        Text(
                          "Conf: ${(confidence * 100).toStringAsFixed(1)}%",
                          style: const TextStyle(color: Colors.orangeAccent, fontWeight: FontWeight.bold),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Close", style: TextStyle(color: Colors.white60)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text(
          "Live Cameras",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: Stack(
              children: [
                SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      cameraCard("Classroom Camera", true, 'classroom'),
                      const SizedBox(height: 20),
                      cameraCard("Cafeteria Camera", true, 'cafeteria'),
                    ],
                  ),
                ),
                if (_isLoading)
                  Container(
                    color: Colors.black54,
                    child: const Center(
                      child: CircularProgressIndicator(color: AppColors.primary),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget cameraCard(String title, bool online, String camera) {
    final streamUrl = '${ApiService.baseUrl}/video_feed?camera=$camera';
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.videocam, color: AppColors.primary),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: online ? Colors.green : Colors.red,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  online ? "ONLINE" : "OFFLINE",
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Container(
            height: 220,
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.black54,
              borderRadius: BorderRadius.circular(15),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(15),
              child: buildMjpegView(streamUrl),
            ),
          ),
          const SizedBox(height: 20),
          const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("FPS : ~30", style: TextStyle(color: Colors.white70)),
              Text("AI : Live YOLOv8 Active", style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 15),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => _testDetection(title),
              icon: const Icon(Icons.bug_report),
              label: const Text("Test AI Detection (Gallery)"),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
