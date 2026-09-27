// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html' as html;

void playAlarm() {
  try {
    final audio = html.AudioElement(
      'https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3',
    );
    audio.autoplay = true;
    html.document.body?.append(audio);
    audio.play().then((_) {
      // ignore: avoid_print
      print("Alarm beep played");
    }).catchError((_) {});
    Future.delayed(const Duration(seconds: 3), () => audio.remove());
  } catch (_) {}
}

void unlockAudio() => playAlarm();
