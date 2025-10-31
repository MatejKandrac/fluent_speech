import 'package:flutter/material.dart';

import '../../core/detection_mode.dart';
import '../../localizations/localizations.dart';
import '../widgets/large_app_bar.dart';

class SummariseView extends StatelessWidget {
  const SummariseView({
    super.key,
    required this.mode,
    required this.filePath,
  });

  final String filePath;
  final DetectionMode mode;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: LargeAppBar(
      title: Text(
        AppTexts.of(context).summary,
        style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.bold),
      ),
    ),
    body: SafeArea(
      child: Column(
        children: [
          Expanded(
            child: Center(
              child: SelectableText(filePath),
            ),
          ),
          FilledButton(
            onPressed: () {
              // TODO: Send video file to backend for analysis
            },
            child: Text(
              AppTexts.of(context).sendForAnalysis,
            ),
          ),
        ],
      ),
    ),
  );
}
