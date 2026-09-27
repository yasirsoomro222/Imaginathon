import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../services/api_service.dart';

class AlertManager {
  static final List<Map<String, dynamic>> alertsList = [];
  static final List<Map<String, dynamic>> historyList = [];
}

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  List<Map<String, dynamic>> students = [];
  bool isLoadingStudents = true;

  @override
  void initState() {
    super.initState();
    loadStudents();
  }

  Future<void> loadStudents() async {
    final data = await ApiService.fetchStudents();
    if (!mounted) return;
    setState(() {
      students = data;
      isLoadingStudents = false;
    });
  }

  void _openActionSheet(BuildContext context, Map<String, dynamic> alert, int index) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => AlertActionSheet(
        alert: alert,
        students: students,
        isLoadingStudents: isLoadingStudents,
        onActionDone: () {
          setState(() {
            var resolvedItem = AlertManager.alertsList.removeAt(index);
            AlertManager.historyList.insert(0, resolvedItem);
          });
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    int todayAlertsCount = AlertManager.alertsList.length;
    int highPriorityCount = AlertManager.alertsList.where((e) => e['priority'] == 'HIGH').length;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        title: const Text("Live Alerts", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.history, color: Colors.white),
            tooltip: "View History",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const HistoryScreen()),
              ).then((_) => setState(() {}));
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: summaryCard("Today's Alerts", todayAlertsCount.toString(), AppColors.danger, Icons.notifications_active),
                ),
                const SizedBox(width: 15),
                Expanded(
                  child: summaryCard("High Priority", highPriorityCount.toString(), AppColors.warning, Icons.warning_amber_rounded),
                ),
              ],
            ),
            const SizedBox(height: 25),
            AlertManager.alertsList.isEmpty
                ? const Padding(
                    padding: EdgeInsets.only(top: 100),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle_outline, size: 80, color: AppColors.success),
                          SizedBox(height: 20),
                          Text(
                            "All Clear! No active smoking alerts.",
                            style: TextStyle(color: Colors.white70, fontSize: 18, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: AlertManager.alertsList.length,
                    itemBuilder: (context, index) {
                      final alert = AlertManager.alertsList[index];
                      return InkWell(
                        onTap: () => _openActionSheet(context, alert, index),
                        borderRadius: BorderRadius.circular(18),
                        child: alertCard(
                          title: alert['title'] ?? "Alert",
                          location: alert['location'] ?? "Unknown Location",
                          time: alert['time'] ?? "",
                          priority: alert['priority'] ?? "HIGH",
                          color: alert['color'] ?? AppColors.danger,
                          icon: alert['icon'] ?? Icons.warning,
                          imageBytes: alert['image'],
                          studentData: alert['student'],
                        ),
                      );
                    },
                  ),
          ],
        ),
      ),
    );
  }

  Widget summaryCard(String title, String value, Color color, IconData icon) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.card, AppColors.card.withValues(alpha: 0.85)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border.withValues(alpha: 0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Icon(icon, color: color, size: 36),
            const SizedBox(height: 10),
            Text(value, style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
            const SizedBox(height: 5),
            Text(title, style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
          ],
        ),
      ),
    );
  }

  Widget alertCard({
    required String title,
    required String location,
    required String time,
    required String priority,
    required Color color,
    required IconData icon,
    required Uint8List? imageBytes,
    required Map<String, dynamic>? studentData,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border.withValues(alpha: 0.5)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(icon, color: color, size: 28),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text(location, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                  decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(20)),
                  child: Text(priority, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              height: 190,
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.border),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: (imageBytes != null && imageBytes.isNotEmpty)
                    ? Image.memory(imageBytes, fit: BoxFit.cover, width: double.infinity)
                    : buildPlaceholder("Detection Snapshot"),
              ),
            ),
            const SizedBox(height: 14),
            if (studentData != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border.withValues(alpha: 0.5)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "${studentData['name']} (${studentData['rollNo']})",
                            style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "Dept: ${studentData['department']}",
                            style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: AppColors.danger.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.danger.withValues(alpha: 0.3)),
                      ),
                      child: Text(
                        "Warnings: ${studentData['warnings']}",
                        style: const TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
            ],
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.access_time, color: AppColors.textSecondary, size: 16),
                    const SizedBox(width: 6),
                    Text(time, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                  ],
                ),
                const Text(
                  "Tap to take action",
                  style: TextStyle(color: AppColors.primary, fontSize: 12, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget buildPlaceholder(String text) {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.image_outlined, size: 50, color: Colors.grey),
            const SizedBox(height: 8),
            Text(text, style: const TextStyle(color: Colors.white54, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}

class AlertActionSheet extends StatefulWidget {
  final Map<String, dynamic> alert;
  final List<Map<String, dynamic>> students;
  final bool isLoadingStudents;
  final VoidCallback onActionDone;

  const AlertActionSheet({
    super.key,
    required this.alert,
    required this.students,
    required this.isLoadingStudents,
    required this.onActionDone,
  });

  @override
  State<AlertActionSheet> createState() => _AlertActionSheetState();
}

class _AlertActionSheetState extends State<AlertActionSheet> {
  int? selectedStudentId;
  final reasonController = TextEditingController();
  bool sendEmail = false;
  bool sendPortal = true;
  bool isSending = false;

  @override
  void initState() {
    super.initState();
    reasonController.text = "Smoking detected on campus premises";
  }

  @override
  void dispose() {
    reasonController.dispose();
    super.dispose();
  }

  Future<void> _sendAction(String type) async {
    if (selectedStudentId == null) {
      _showToast("Please select a student");
      return;
    }
    if (!sendEmail && !sendPortal) {
      _showToast("Select at least Email or Portal");
      return;
    }

    setState(() => isSending = true);

    Map<String, dynamic> result;
    if (type == 'warning') {
      result = await ApiService.sendWarning(
        selectedStudentId!,
        alertId: widget.alert['alert_id'] ?? '',
        camera: widget.alert['location'] ?? 'classroom',
        reason: reasonController.text,
        sendEmail: sendEmail,
        sendPortal: sendPortal,
      );
    } else {
      result = await ApiService.issueChalan(
        selectedStudentId!,
        alertId: widget.alert['alert_id'] ?? '',
        camera: widget.alert['location'] ?? 'classroom',
        reason: reasonController.text,
        amount: 5000,
        sendEmail: sendEmail,
        sendPortal: sendPortal,
      );
    }

    if (!mounted) return;
    setState(() => isSending = false);

    if (result['success'] == true) {
      final selectedStudentObj = widget.students.firstWhere(
        (s) => s['id'] == selectedStudentId,
        orElse: () => {},
      );
      
      widget.alert['student'] = {
        'name': selectedStudentObj['name'],
        'rollNo': selectedStudentObj['roll_no'],
        'department': selectedStudentObj['department'],
        'warnings': selectedStudentObj['warnings'] ?? '1',
      };
      widget.alert['reason'] = reasonController.text;

      Navigator.pop(context);
      widget.onActionDone();
      _showToast(type == 'warning' ? "Warning sent" : "Chalan issued", success: true);
    } else {
      _showToast("Failed to send. Check backend connection.");
    }
  }

  void _showToast(String msg, {bool success = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: success ? AppColors.success : AppColors.danger,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final student = widget.alert['student'] ?? {};

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(4)),
                ),
              ),
              const SizedBox(height: 18),
              const Text("Take Action", style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Student: ${student['name'] ?? 'Unknown'} (${student['rollNo'] ?? 'N/A'})",
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    Text("Department: ${student['department'] ?? 'N/A'}", style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                    Text("Location: ${widget.alert['location'] ?? 'N/A'}", style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              const Text("Select Student", style: TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              widget.isLoadingStudents
                  ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
                  : Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      decoration: BoxDecoration(
                        color: AppColors.card,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<int>(
                          isExpanded: true,
                          dropdownColor: AppColors.card,
                          value: selectedStudentId,
                          hint: const Text("Choose student", style: TextStyle(color: AppColors.textSecondary)),
                          icon: const Icon(Icons.arrow_drop_down, color: AppColors.textSecondary),
                          style: const TextStyle(color: Colors.white),
                          items: widget.students.map((s) {
                            return DropdownMenuItem<int>(
                              value: s['id'],
                              child: Text("${s['name']} (${s['roll_no']})"),
                            );
                          }).toList(),
                          onChanged: (val) => setState(() => selectedStudentId = val),
                        ),
                      ),
                    ),
              const SizedBox(height: 18),
              const Text("Reason", style: TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              TextField(
                controller: reasonController,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  filled: true,
                  fillColor: AppColors.card,
                  hintText: "Enter reason",
                  hintStyle: const TextStyle(color: AppColors.textMuted),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: AppColors.border)),
                  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: AppColors.border)),
                  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.primary)),
                ),
              ),
              const SizedBox(height: 18),
              Row(
                children: [
                  Expanded(
                    child: _checkboxTile(
                      label: "Portal",
                      value: sendPortal,
                      onChanged: (v) => setState(() => sendPortal = v ?? true),
                    ),
                  ),
                  Expanded(
                    child: _checkboxTile(
                      label: "Email",
                      value: sendEmail,
                      onChanged: (v) => setState(() => sendEmail = v ?? false),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 22),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: isSending ? null : () => _sendAction('warning'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.warning,
                        side: const BorderSide(color: AppColors.warning),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: isSending
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.warning))
                          : const Text("Send Warning", style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: isSending ? null : () => _sendAction('chalan'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.danger,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: isSending
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Text("Issue Chalan", style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _checkboxTile({required String label, required bool value, required ValueChanged<bool?> onChanged}) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: CheckboxListTile(
        title: Text(label, style: const TextStyle(color: Colors.white, fontSize: 14)),
        value: value,
        activeColor: AppColors.primary,
        checkColor: Colors.white,
        onChanged: onChanged,
        controlAffinity: ListTileControlAffinity.leading,
        contentPadding: const EdgeInsets.symmetric(horizontal: 8),
      ),
    );
  }
}

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  void _openHistoryDetail(BuildContext context, Map<String, dynamic> item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        final student = item['student'] ?? {};
        final Uint8List? imageBytes = item['image'];

        return Padding(
          padding: EdgeInsets.only(
            left: 22,
            right: 22,
            top: 22,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 22,
          ),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: AppColors.border,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
                const SizedBox(height: 18),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "Resolved History",
                      style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.success.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.success.withValues(alpha: 0.5)),
                      ),
                      child: const Text("Resolved", style: TextStyle(color: AppColors.success, fontSize: 11, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.check_circle, color: AppColors.success, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              item['reason'] ?? 'Smoking detected on campus premises',
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Container(
                        height: 180,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: Colors.black54,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: (imageBytes != null && imageBytes.isNotEmpty)
                              ? Image.memory(imageBytes, fit: BoxFit.cover, width: double.infinity)
                              : const Center(
                                  child: Text("No Snapshot Available", style: TextStyle(color: Colors.white54, fontSize: 12)),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("Student Information", style: TextStyle(color: AppColors.primary, fontSize: 12, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Text(
                        "Name: ${student['name'] ?? 'Unknown'} (${student['rollNo'] ?? 'N/A'})",
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
                      ),
                      const SizedBox(height: 4),
                      Text("Department: ${student['department'] ?? 'N/A'}", style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                      const SizedBox(height: 4),
                      Text("Total Warnings: ${student['warnings'] ?? '0'}", style: const TextStyle(color: AppColors.danger, fontSize: 13, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("Incident Metadata", style: TextStyle(color: AppColors.primary, fontSize: 12, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Text("Location / Camera: ${item['location'] ?? 'N/A'}", style: const TextStyle(color: Colors.white, fontSize: 13)),
                      const SizedBox(height: 4),
                      Text("Timestamp: ${item['time'] ?? 'N/A'}", style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.card,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text("Close", style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: const Text("Resolved History", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: AlertManager.historyList.isEmpty
          ? const Center(
              child: Text("No history logs found.", style: TextStyle(color: Colors.white54, fontSize: 16)),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: AlertManager.historyList.length,
              itemBuilder: (context, index) {
                final item = AlertManager.historyList[index];
                return Card(
                  color: AppColors.card,
                  margin: const EdgeInsets.only(bottom: 15),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(15),
                    onTap: () => _openHistoryDetail(context, item),
                    child: ListTile(
                      contentPadding: const EdgeInsets.all(12),
                      leading: const CircleAvatar(
                        backgroundColor: AppColors.success,
                        child: Icon(Icons.check, color: Colors.white),
                      ),
                      title: Text(item['title'] ?? "Resolved Alert", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Location: ${item['location']} | Time: ${item['time']}\nStudent: ${item['student']?['name'] ?? 'N/A'} (${item['student']?['rollNo'] ?? 'N/A'})",
                            style: const TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                          if ((int.tryParse(item['student']?['warnings']?.toString() ?? '0') ?? 0) > 0)
                            Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text(
                                "${item['student']['warnings']} warning(s) already recorded",
                                style: const TextStyle(color: Colors.orangeAccent, fontSize: 11, fontWeight: FontWeight.w600),
                              ),
                            ),
                        ],
                      ),
                      isThreeLine: true,
                    ),
                  ),
                );
              },
            ),
    );
  }
}