import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

abstract class DetectorBase<T, P> {

  DetectorBase([this.isDemo = false]);

  bool _isBusy = false;
  final bool isDemo;

  final _orientations = {
    DeviceOrientation.portraitUp: 0,
    DeviceOrientation.landscapeLeft: 90,
    DeviceOrientation.portraitDown: 180,
    DeviceOrientation.landscapeRight: 270,
  };

  Future<List<T>> getFeatures(InputImage image);

  P buildPainter(List<T> features, InputImage image, CameraLensDirection lensDirection);

  Future<P?> getPainter(
    CameraImage image,
    CameraDescription camera,
    DeviceOrientation orientation,
  ) async {
    if (isDemo) return null;
    final result = await _processImage(image, camera, orientation);
    if (result == null) return null;
    return buildPainter(result.$1, result.$2, camera.lensDirection);
  }

  Future<(List<T>, InputImage)?> processImage(
    CameraImage cameraImage,
    CameraDescription camera,
    DeviceOrientation orientation,
  ) async => _processImage(cameraImage, camera, orientation);

  Future<(List<T>, InputImage)?> _processImage(
    CameraImage image,
    CameraDescription camera,
    DeviceOrientation orientation,
  ) async {
    if (isDemo) return null;
    if (_isBusy) {
      return null;
    }
    _isBusy = true;
    final inputImage = inputImageFromCameraImage(image, camera, orientation);
    if (inputImage == null) {
      _isBusy = false;
      return null;
    }
    final features = await getFeatures(inputImage);

    _isBusy = false;
    return (features, inputImage);
  }

  InputImage? inputImageFromCameraImage(
    CameraImage image,
    CameraDescription camera,
    DeviceOrientation orientation,
  ) {
    final sensorOrientation = camera.sensorOrientation;

    InputImageRotation? rotation;
    if (Platform.isIOS) {
      rotation = InputImageRotationValue.fromRawValue(sensorOrientation);
    } else if (Platform.isAndroid) {
      var rotationCompensation = _orientations[orientation];
      if (rotationCompensation == null) return null;
      if (camera.lensDirection == CameraLensDirection.front) {
        rotationCompensation = (sensorOrientation + rotationCompensation) % 360;
      } else {
        rotationCompensation = (sensorOrientation - rotationCompensation + 360) % 360;
      }
      rotation = InputImageRotationValue.fromRawValue(rotationCompensation);
    }
    if (rotation == null) return null;

    final format = InputImageFormatValue.fromRawValue(image.format.raw);
    if (format == null ||
        (Platform.isAndroid && format != InputImageFormat.nv21) ||
        (Platform.isIOS && format != InputImageFormat.bgra8888)) {
      return null;
    }

    if (image.planes.length != 1) return null;
    final plane = image.planes.first;

    return InputImage.fromBytes(
      bytes: plane.bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: plane.bytesPerRow,
      ),
    );
  }
}
