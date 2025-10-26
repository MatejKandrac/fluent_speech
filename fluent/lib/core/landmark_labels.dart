import 'package:flutter/material.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

import '../localizations/localizations.dart';

extension PoseLandmarkLabels on PoseLandmarkType {
  String getLabel(BuildContext context) {
    final texts = AppTexts.of(context);
    return switch (this) {
      PoseLandmarkType.leftHip => texts.leftHip,
      PoseLandmarkType.rightHip => texts.rightHip,
      _ => 'UNKNOWN',
      // PoseLandmarkType.nose => throw UnimplementedError(),
      // PoseLandmarkType.leftEyeInner => throw UnimplementedError(),
      // PoseLandmarkType.leftEye => throw UnimplementedError(),
      // PoseLandmarkType.leftEyeOuter => throw UnimplementedError(),
      // PoseLandmarkType.rightEyeInner => throw UnimplementedError(),
      // PoseLandmarkType.rightEye => throw UnimplementedError(),
      // PoseLandmarkType.rightEyeOuter => throw UnimplementedError(),
      // PoseLandmarkType.leftEar => throw UnimplementedError(),
      // PoseLandmarkType.rightEar => throw UnimplementedError(),
      // PoseLandmarkType.leftMouth => throw UnimplementedError(),
      // PoseLandmarkType.rightMouth => throw UnimplementedError(),
      // PoseLandmarkType.leftShoulder => throw UnimplementedError(),
      // PoseLandmarkType.rightShoulder => throw UnimplementedError(),
      // PoseLandmarkType.leftElbow => throw UnimplementedError(),
      // PoseLandmarkType.rightElbow => throw UnimplementedError(),
      // PoseLandmarkType.leftWrist => throw UnimplementedError(),
      // PoseLandmarkType.rightWrist => throw UnimplementedError(),
      // PoseLandmarkType.leftPinky => throw UnimplementedError(),
      // PoseLandmarkType.rightPinky => throw UnimplementedError(),
      // PoseLandmarkType.leftIndex => throw UnimplementedError(),
      // PoseLandmarkType.rightIndex => throw UnimplementedError(),
      // PoseLandmarkType.leftThumb => throw UnimplementedError(),
      // PoseLandmarkType.rightThumb => throw UnimplementedError(),
      // PoseLandmarkType.leftHip => throw UnimplementedError(),
      // PoseLandmarkType.rightHip => throw UnimplementedError(),
      // PoseLandmarkType.leftKnee => throw UnimplementedError(),
      // PoseLandmarkType.rightKnee => throw UnimplementedError(),
      // PoseLandmarkType.leftAnkle => throw UnimplementedError(),
      // PoseLandmarkType.rightAnkle => throw UnimplementedError(),
      // PoseLandmarkType.leftHeel => throw UnimplementedError(),
      // PoseLandmarkType.rightHeel => throw UnimplementedError(),
      // PoseLandmarkType.leftFootIndex => throw UnimplementedError(),
      // PoseLandmarkType.rightFootIndex => throw UnimplementedError(),
    };
  }
}

extension FaceLandmarkLabels on FaceLandmarkType {
  String getLabel(BuildContext context) {
    final texts = AppTexts.of(context);
    return switch (this) {
      FaceLandmarkType.rightEye => texts.rightEye,
      FaceLandmarkType.leftEye => texts.leftEye,
      FaceLandmarkType.rightCheek => texts.rightCheek,
      FaceLandmarkType.leftCheek => texts.leftCheek,
      _ => 'UNKNOWN',
      // FaceLandmarkType.bottomMouth => throw UnimplementedError(),
      // FaceLandmarkType.rightMouth => throw UnimplementedError(),
      // FaceLandmarkType.leftMouth => throw UnimplementedError(),
      // FaceLandmarkType.rightEar => throw UnimplementedError(),
      // FaceLandmarkType.leftEar => throw UnimplementedError(),
      // FaceLandmarkType.noseBase => throw UnimplementedError(),
    };
  }
}
