import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';

import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

import '../detection_mode.dart';
import 'detector_base.dart';
import 'painter/face_painter.dart';
import 'painter/pose_painter.dart';

extension DetectorMapper on DetectionMode {
  DetectorBase getDetector() {
    if (kIsWasm || kIsWeb || (!Platform.isAndroid && !Platform.isIOS)) return DemoProcessor();
    if (this == DetectionMode.eyeContact) return FaceProcessor();
    return PoseProcessor();
  }
}

final class PoseProcessor extends DetectorBase<Pose, PosePainter> {
  final _poseDetector = PoseDetector(options: PoseDetectorOptions(mode: PoseDetectionMode.stream));

  @override
  PosePainter buildPainter(
    List<Pose> features,
    InputImage image,
    CameraLensDirection lensDirection,
  ) => PosePainter(
    features,
    image.metadata!.size,
    image.metadata!.rotation,
    lensDirection,
  );

  @override
  Future<List<Pose>> getFeatures(InputImage image) => _poseDetector.processImage(image);
}

final class FaceProcessor extends DetectorBase<Face, FaceDetectorPainter> {
  final _faceDetector = FaceDetector(options: FaceDetectorOptions());

  @override
  FaceDetectorPainter buildPainter(
    List<Face> features,
    InputImage image,
    CameraLensDirection lensDirection,
  ) => FaceDetectorPainter(
    features,
    image.metadata!.size,
    image.metadata!.rotation,
    lensDirection,
  );

  @override
  Future<List<Face>> getFeatures(InputImage image) => _faceDetector.processImage(image);
}

final class DemoProcessor extends DetectorBase<dynamic, FaceDetectorPainter> {
  DemoProcessor() : super(true);

  @override
  FaceDetectorPainter buildPainter(features, InputImage image, CameraLensDirection lensDirection) =>
      throw Exception('Cannot build painter for demo processor');

  @override
  Future<List<dynamic>> getFeatures(InputImage image) async =>
      throw Exception('Cannot get features from demo processor');
}
