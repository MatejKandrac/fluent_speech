// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'localizations.dart';

// ignore_for_file: type=lint

/// The translations for Slovak (`sk`).
class AppTextsSk extends AppTexts {
  AppTextsSk([String locale = 'sk']) : super(locale);

  @override
  String get startPreparing => 'Začnite sa pripravovať';

  @override
  String get startExercise => 'Začať cvičenie';

  @override
  String get calibrate => 'Kalibrácia';

  @override
  String get record => 'Nahrávanie';

  @override
  String get summary => 'Zhrnutie';

  @override
  String get requiredLandmarks => 'Required landmarks:';

  @override
  String get rightHip => 'Right hip';

  @override
  String get leftHip => 'Left hip';

  @override
  String get rightEye => 'Right eye';

  @override
  String get leftEye => 'Left eye';

  @override
  String get leftCheek => 'Left cheek';

  @override
  String get rightCheek => 'Right cheek';

  @override
  String get getReady => 'Get ready';

  @override
  String get sendForAnalysis => 'Send data for analysis';
}
