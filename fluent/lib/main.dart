import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'localizations/localizations.dart';
import 'ui/dashboard/dashboard_view.dart';
import 'config/theme.dart';
import 'db/database_helper.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await _assignTestRecording();
  runApp(ProviderScope(child: const MyApp()));
}

/// Debug utility: assigns remoteId=11 to the local record named "Test video 1".
/// Safe to leave in — does nothing if the record doesn't exist or is already uploaded.
Future<void> _assignTestRecording() async {
  try {
    final db = DatabaseHelper();
    final records = await db.getAllVideoRecords();
    final match = records.where((r) => r.name == 'Hands calibration' && r.remoteId == 90).firstOrNull;
    if (match != null) {
      await db.updateVideoRecord(match.copyWith(remoteId: 90));
      print('[DEBUG] Assigned remoteId=90 to "Hands calibration"');
    }
  } catch (e) {
    print('[DEBUG] _assignTestRecording failed: $e');
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final brightness = View.of(context).platformDispatcher.platformBrightness;

    MaterialTheme theme = MaterialTheme();

    return MaterialApp(
      title: 'Fluent',
      localizationsDelegates: [
        AppTexts.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
      ],
      supportedLocales: AppTexts.supportedLocales,
      debugShowCheckedModeBanner: false,
      theme: brightness == Brightness.light ? theme.light() : theme.dark(),
      home: DashboardView(),
    );
  }
}
