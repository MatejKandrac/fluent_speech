import 'package:flutter/cupertino.dart';
import '../config/constants.dart';

enum DetectionMode { eyeContact, handGestures, hips, pitch, stage, volume }

extension Translation on DetectionMode {
  String getText(BuildContext context) => switch (this) {
    DetectionMode.eyeContact => 'Eye contact',
    DetectionMode.handGestures => 'Hand gestures',
    DetectionMode.hips => 'Hip movement',
    DetectionMode.pitch => 'Voice pitch',
    DetectionMode.stage => 'Stage usage',
    DetectionMode.volume => 'Volume',
  };
}

extension CoverImage on DetectionMode {
  String getCoverImage() => switch (this) {
    DetectionMode.eyeContact => Assets.eyeContact,
    DetectionMode.handGestures => Assets.handGestures,
    DetectionMode.hips => Assets.hips,
    DetectionMode.pitch => Assets.pitch,
    DetectionMode.stage => Assets.stage,
    DetectionMode.volume => Assets.volume,
  };
}
