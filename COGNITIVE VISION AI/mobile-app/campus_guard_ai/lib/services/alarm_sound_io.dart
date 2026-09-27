import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

void playAlarm() {
  SystemSound.play(SystemSoundType.alert);
  HapticFeedback.vibrate();
  Future.delayed(const Duration(milliseconds: 300), () => HapticFeedback.vibrate());
  Future.delayed(const Duration(milliseconds: 600), () => HapticFeedback.vibrate());
  debugPrint("Alarm beep + vibration triggered");
}

void unlockAudio() {}
