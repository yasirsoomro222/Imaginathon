import 'alarm_sound_stub.dart'
    if (dart.library.html) 'alarm_sound_web.dart'
    if (dart.library.io) 'alarm_sound_io.dart' as impl;

/// Plays the alarm on alert. Uses an audio beep on the web and
/// haptic vibration on Android/iOS/desktop.
void playAlarm() => impl.playAlarm();

/// Web-only: unlocks audio playback after a user gesture. No-op elsewhere.
void unlockAudio() => impl.unlockAudio();
