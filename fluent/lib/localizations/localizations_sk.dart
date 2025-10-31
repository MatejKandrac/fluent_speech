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
  String get requiredLandmarks => 'Požadované body';

  @override
  String get rightHip => 'Pravý bok';

  @override
  String get leftHip => 'Ľavý bok';

  @override
  String get rightEye => 'Pravé oko';

  @override
  String get leftEye => 'Ľavé oko';

  @override
  String get leftCheek => 'Ľavé líce';

  @override
  String get rightCheek => 'Pravé líce';

  @override
  String get getReady => 'Priprav sa!';

  @override
  String get sendForAnalysis => 'Odoslať na analýzu';
}
