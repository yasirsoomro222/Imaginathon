import 'dart:async';
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../widgets/dashboard_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int alertCount = 0;
  int warningCount = 0;
  int chalanCount = 0;
  int studentCount = 0;
  bool isLoading = true;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    loadStats();
    _refreshTimer = Timer.periodic(const Duration(seconds: 5), (_) => loadStats());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> loadStats() async {
    final results = await Future.wait([
      ApiService.fetchAlerts(),
      ApiService.fetchWarnings(),
      ApiService.fetchChalans(),
      ApiService.fetchStudents(),
    ]);

    if (!mounted) return;
    setState(() {
      alertCount = (results[0] as List).length;
      warningCount = (results[1] as List).length;
      chalanCount = (results[2] as List).length;
      studentCount = (results[3] as List).length;
      isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("CampusGuard AI"),
        centerTitle: true,
      ),
      drawer: Drawer(
        backgroundColor: AppColors.surface,
        child: Column(
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.only(top: 60, bottom: 25),
              decoration: const BoxDecoration(gradient: AppColors.primaryGradient),
              child: const Column(
                children: [
                  CircleAvatar(
                    radius: 38,
                    backgroundColor: Colors.white,
                    child: Icon(Icons.security, size: 42, color: AppColors.primary),
                  ),
                  SizedBox(height: 15),
                  Text(
                    "CampusGuard AI",
                    style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 6),
                  Text("Muhammad Yasir Soomro", style: TextStyle(color: Colors.white70)),
                  SizedBox(height: 4),
                  Text("Campus Security Administrator", style: TextStyle(color: Colors.white54, fontSize: 13)),
                ],
              ),
            ),
            const SizedBox(height: 20),
            ListTile(
              leading: const Icon(Icons.settings, color: Colors.white),
              title: const Text("Settings", style: TextStyle(color: Colors.white)),
              onTap: () {},
            ),
            ListTile(
              leading: const Icon(Icons.info_outline, color: Colors.white),
              title: const Text("About", style: TextStyle(color: Colors.white)),
              onTap: () {},
            ),
            const Spacer(),
            const Divider(color: AppColors.border),
            ListTile(
              leading: const Icon(Icons.logout, color: AppColors.danger),
              title: const Text("Logout", style: TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold)),
              onTap: () {},
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Good Evening, Yasir",
                    style: TextStyle(color: AppColors.textPrimary, fontSize: 28, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "AI Smart Campus Monitoring System",
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
                  ),
                  const SizedBox(height: 25),
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            gradient: AppColors.successGradient,
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: const Icon(Icons.check, color: Colors.white),
                        ),
                        const SizedBox(width: 18),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "System Status",
                                style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 18),
                              ),
                              SizedBox(height: 5),
                              Text(
                                "All AI Agents Running",
                                style: TextStyle(color: AppColors.success),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 30),
                  const Text(
                    "Live Overview",
                    style: TextStyle(color: AppColors.textPrimary, fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 15),
                  Row(
                    children: [
                      Expanded(
                        child: DashboardCard(
                          icon: Icons.notifications_active,
                          title: "Alerts",
                          value: alertCount.toString(),
                          color: AppColors.danger,
                        ),
                      ),
                      const SizedBox(width: 15),
                      Expanded(
                        child: DashboardCard(
                          icon: Icons.warning_amber_rounded,
                          title: "Warnings",
                          value: warningCount.toString(),
                          color: AppColors.warning,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 15),
                  Row(
                    children: [
                      Expanded(
                        child: DashboardCard(
                          icon: Icons.receipt_long,
                          title: "Chalans",
                          value: chalanCount.toString(),
                          color: AppColors.info,
                        ),
                      ),
                      const SizedBox(width: 15),
                      Expanded(
                        child: DashboardCard(
                          icon: Icons.school,
                          title: "Students",
                          value: studentCount.toString(),
                          color: AppColors.success,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 30),
                  const Text(
                    "Recent Activity",
                    style: TextStyle(color: AppColors.textPrimary, fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 15),
                  activityTile(Icons.smoking_rooms, "Smoking Detected", "Classroom 01"),
                  activityTile(Icons.badge, "ID Card Missing", "Classroom 01"),
                  activityTile(Icons.warning_amber_rounded, "Warning Sent", "Student 234023"),
                ],
              ),
            ),
    );
  }

  Widget activityTile(IconData icon, String title, String location) {
    return Card(
      color: AppColors.card,
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Icon(icon, color: AppColors.secondary),
        title: Text(title, style: const TextStyle(color: AppColors.textPrimary)),
        subtitle: Text(location, style: const TextStyle(color: AppColors.textSecondary)),
      ),
    );
  }
}
