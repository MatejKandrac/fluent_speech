import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';

import 'print_utils.dart';

Future<CameraController> initCamera(CameraController? currentController, CameraDescription selectedCamera) async {
  await currentController?.dispose();
  final controller = CameraController(
    selectedCamera,
    ResolutionPreset.medium,
    imageFormatGroup: (kIsWeb || kIsWasm || Platform.isAndroid) ? ImageFormatGroup.nv21 : ImageFormatGroup.bgra8888,
  );
  await controller.initialize();

  return controller;
}

Future<void> disposeCamera(CameraController? controller, [bool shouldStopImageStream = false]) async {
  if (controller == null) return;
  if (shouldStopImageStream && controller.supportsImageStreaming()) {
    await controller.stopImageStream();
  }
  await controller.dispose();
}

Future<void> startImageStream({
  required CameraController? controller,
  required void Function(CameraImage image) onImage,
  required void Function() onDemoImage,
}) async {
  if (controller == null) return;
  if (controller.supportsImageStreaming()) {
    await controller.startImageStream(onImage);
  } else {
    onDemoImage();
  }
}

Future<void> stopImageStream(CameraController? controller) async {
  if (controller == null) return;
  try {
    if (controller.supportsImageStreaming()) await controller.stopImageStream();
  } on Exception catch (e) {
    Log.e('CAMERA', 'Attempted to stop image stream failed');
  }
}