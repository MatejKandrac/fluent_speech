import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final currentCameraProvider = AsyncNotifierProvider.autoDispose<CurrentCameraNotifier, CameraDescription>(
  CurrentCameraNotifier.new,
);

final class CurrentCameraNotifier extends AsyncNotifier<CameraDescription> {
  int _currentIndex = 0;
  int cameraCount = 0;

  @override
  FutureOr<CameraDescription> build() async => _getCamera();

  Future<void> next() async {
    state = AsyncLoading();
    _currentIndex++;
    final camera = await _getCamera();
    state = AsyncData(camera);
  }

  Future<CameraDescription> _getCamera() async {
    final cameras = await availableCameras();
    cameraCount = cameras.length;
    _currentIndex = _currentIndex % cameras.length;
    return cameras[_currentIndex];
  }
}
