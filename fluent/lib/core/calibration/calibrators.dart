import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

import '../../config/constants.dart';
import '../detection_mode.dart';
import 'calibrator_base.dart';

extension CalibratorMapper on DetectionMode {
  CalibratorBase getCalibrator() {
    if (kIsWasm || kIsWeb || (!Platform.isAndroid && !Platform.isIOS)) {
      if (this == DetectionMode.eyeContact) {
        return DemoCalibrator<FaceLandmarkType>(
          mockedRequiredLandmarks: [
            FaceLandmarkType.leftCheek,
            FaceLandmarkType.rightCheek,
            FaceLandmarkType.rightEye,
            FaceLandmarkType.leftEye,
          ],
          mockedLandmarks: [],
        );
      } else {
        return DemoCalibrator<PoseLandmarkType>(
          mockedRequiredLandmarks: [
            PoseLandmarkType.rightHip,
            PoseLandmarkType.leftHip,
          ],
          mockedLandmarks: [],
        );
      }
    }
    if (this == DetectionMode.eyeContact) return EyeContactCalibrator();
    return PoseCalibrator(this);
  }
}

final class EyeContactCalibrator extends CalibratorBase<FaceLandmarkType, Face> {
  @override
  List<FaceLandmarkType> getLandmarks(Face data) => data.landmarks.keys.toList();

  @override
  List<FaceLandmarkType> requiredLandmarks() => [
    FaceLandmarkType.rightEye,
    FaceLandmarkType.leftEye,
    FaceLandmarkType.leftCheek,
    FaceLandmarkType.rightCheek,
    FaceLandmarkType.noseBase,
  ];
}

final class PoseCalibrator extends CalibratorBase<PoseLandmarkType, Pose> {
  final DetectionMode mode;

  PoseCalibrator(this.mode);

  @override
  List<PoseLandmarkType> getLandmarks(Pose data) {
    final landmarks = <PoseLandmarkType>[];
    for (var key in data.landmarks.keys) {
      if ((data.landmarks[key]?.likelihood ?? 0) < Constants.probabilityThreshold) continue;
      landmarks.add(key);
    }
    return landmarks;
  }

  @override
  List<PoseLandmarkType> requiredLandmarks() => [PoseLandmarkType.leftHip];
}

final class DemoCalibrator<T> extends CalibratorBase<T, dynamic> {
  final List<T> mockedRequiredLandmarks;
  final List<T> mockedLandmarks;

  DemoCalibrator({
    required this.mockedRequiredLandmarks,
    required this.mockedLandmarks,
  });

  @override
  List<T> getLandmarks(dynamic data) => mockedLandmarks;

  @override
  List<T> requiredLandmarks() => mockedRequiredLandmarks;
}
