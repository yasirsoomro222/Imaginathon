import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'screens/splash/splash_screen.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.init();
  await NotificationService.requestPermissions();
  runApp(const CampusGuardAI());
}

class CampusGuardAI extends StatelessWidget {
  const CampusGuardAI({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'CampusGuard AI',
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}