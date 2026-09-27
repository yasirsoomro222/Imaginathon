// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html' as html;
// ignore: undefined_hidden_name
import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';

int _viewCounter = 0;
final Set<String> _registered = <String>{};

Widget buildMjpegView(String url, {Key? key}) {
  _viewCounter++;
  final viewType = 'mjpeg-stream-$_viewCounter';

  if (_registered.add(viewType)) {
    ui_web.platformViewRegistry.registerViewFactory(
      viewType,
      (int viewId) => html.ImageElement()
        ..src = url
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.objectFit = 'cover',
    );
  }

  return HtmlElementView(key: key, viewType: viewType);
}
