// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppTextsEn extends AppTexts {
  AppTextsEn([String locale = 'en']) : super(locale);

  @override
  String get startPreparing => 'Start preparing';

  @override
  String get startExercise => 'Start exercise';

  @override
  String get calibrate => 'Calibrate';

  @override
  String get record => 'Record';

  @override
  String get summary => 'Summary';

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
