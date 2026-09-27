import 'package:flutter/material.dart';

// Fallback implementation; replaced at compile time by platform-specific variants.
Widget buildMjpegView(String url, {Key? key}) {
  return Container(
    key: key,
    color: Colors.black54,
    child: const Center(
      child: Text(
        "Camera preview not supported on this platform",
        style: TextStyle(color: Colors.white54),
      ),
    ),
  );
}
