import 'package:flutter/material.dart';

import 'mjpeg_stub.dart'
    if (dart.library.html) 'mjpeg_web.dart'
    if (dart.library.io) 'mjpeg_io.dart' as impl;

/// Cross-platform MJPEG stream viewer.
/// On the web it renders a native <img> element (browser handles MJPEG).
/// On Android/iOS/desktop it parses the multipart stream in pure Dart.
Widget buildMjpegView(String url, {Key? key}) => impl.buildMjpegView(url, key: key);
