
import 'package:flutter/material.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

import '../../../core/landmark_labels.dart';
import '../../../localizations/localizations.dart';

class MissingLandmarksView extends StatelessWidget {
  const MissingLandmarksView(this.missingLandmarks, {super.key});

  final List<dynamic> missingLandmarks;

  String getLabel(dynamic landmark, BuildContext context) {
    if (landmark is FaceLandmarkType) {
      return landmark.getLabel(context);
    } else if (landmark is PoseLandmarkType) {
      return landmark.getLabel(context);
    }
    return 'UNKNOWN TYPE';
  }

  @override
  Widget build(BuildContext context) => Container(
    decoration: BoxDecoration(color: Color(0x80000000), borderRadius: BorderRadius.circular(15)),
    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(AppTexts.of(context).requiredLandmarks, style: Theme.of(context).textTheme.titleSmall),
        for (var value in missingLandmarks) Text(getLabel(value, context)),
      ],
    ),
  );
}
