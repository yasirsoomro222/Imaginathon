import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

Widget buildMjpegView(String url, {Key? key}) {
  return MjpegView(key: key, url: url);
}

/// Pure-Dart MJPEG (multipart/x-mixed-replace) viewer for non-web platforms.
class MjpegView extends StatefulWidget {
  final String url;
  const MjpegView({super.key, required this.url});

  @override
  State<MjpegView> createState() => _MjpegViewState();
}

class _MjpegViewState extends State<MjpegView> {
  http.Client? _client;
  StreamSubscription<List<int>>? _subscription;
  final List<int> _buffer = <int>[];
  Uint8List? _frame;
  bool _failed = false;
  bool _connecting = true;

  static const int _maxBuffer = 2 * 1024 * 1024;

  @override
  void initState() {
    super.initState();
    _connect();
  }

  Future<void> _connect() async {
    _client = http.Client();
    try {
      final request = http.Request('GET', Uri.parse(widget.url));
      final response = await _client!.send(request);
      if (!mounted) return;
      setState(() {
        _connecting = false;
        _failed = response.statusCode != 200;
      });
      if (response.statusCode != 200) return;

      _subscription = response.stream.listen(
        _onChunk,
        onError: (_) => _markFailed(),
        onDone: () => _markFailed(),
        cancelOnError: true,
      );
    } catch (_) {
      _markFailed();
    }
  }

  void _markFailed() {
    if (!mounted || _failed) return;
    setState(() {
      _failed = true;
      _connecting = false;
    });
  }

  void _onChunk(List<int> chunk) {
    _buffer.addAll(chunk);
    if (_buffer.length > _maxBuffer) {
      _buffer.removeRange(0, _buffer.length - _maxBuffer);
    }
    _extractFrame();
  }

  void _extractFrame() {
    while (true) {
      final start = _findPattern(_buffer, const [0xFF, 0xD8], 0);
      if (start < 0) {
        if (_buffer.length > 2) {
          _buffer.removeRange(0, _buffer.length - 1);
        }
        return;
      }
      final end = _findPattern(_buffer, const [0xFF, 0xD9], start + 2);
      if (end < 0) {
        if (start > 0) _buffer.removeRange(0, start);
        return;
      }
      final frameEnd = end + 2;
      final frame = Uint8List.fromList(_buffer.sublist(start, frameEnd));
      _buffer.removeRange(0, frameEnd);
      if (mounted) {
        setState(() {
          _frame = frame;
        });
      }
    }
  }

  int _findPattern(List<int> data, List<int> pattern, int from) {
    for (int i = from; i <= data.length - pattern.length; i++) {
      bool match = true;
      for (int j = 0; j < pattern.length; j++) {
        if (data[i + j] != pattern[j]) {
          match = false;
          break;
        }
      }
      if (match) return i;
    }
    return -1;
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _client?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black54,
      child: _failed
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.videocam_off, size: 46, color: Colors.white38),
                  SizedBox(height: 10),
                  Text("Camera offline",
                      style: TextStyle(color: Colors.white54, fontSize: 13)),
                ],
              ),
            )
          : _frame == null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(
                        width: 28,
                        height: 28,
                        child: CircularProgressIndicator(strokeWidth: 2.5),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _connecting ? "Connecting..." : "Waiting for stream...",
                        style: const TextStyle(color: Colors.white54, fontSize: 13),
                      ),
                    ],
                  ),
                )
              : Image.memory(
                  _frame!,
                  fit: BoxFit.cover,
                  width: double.infinity,
                  height: double.infinity,
                  gaplessPlayback: true,
                ),
    );
  }
}
