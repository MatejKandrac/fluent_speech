import 'package:flutter/material.dart';

import '../../localizations/localizations.dart';
import '../capture/capture_view.dart';
import '../widgets/large_app_bar.dart';
import '../../core/detection_mode.dart';

class ExerciseDetailView extends StatelessWidget {
  const ExerciseDetailView({
    super.key,
    required this.mode,
  });

  final DetectionMode mode;

  void _onContinue(BuildContext context) {
    Navigator.of(context).push(MaterialPageRoute(builder: (context) => CaptureView(mode: mode)));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: LargeAppBar(
      title: Text(
        mode.getText(context),
        style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.bold),
      ),
      leadingIcon: IconButton(
        onPressed: Navigator.of(context).pop,
        icon: Icon(Icons.arrow_back),
      ),
    ),
    body: SafeArea(
      child: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Column(
                  spacing: 24,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: double.infinity,
                      height: MediaQuery.of(context).size.height / 2.5,
                      child: Hero(
                        tag: mode,
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.asset(
                            mode.getCoverImage(),
                            fit: BoxFit.cover,
                          ),
                        ),
                      ),
                    ),
                    Text('DESCRIPTION PLACEHOLDER'),
                  ],
                ),
              ),
            ),
          ),
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(horizontal: 24),
            margin: EdgeInsets.only(bottom: 24),
            child: FilledButton(
              onPressed: () => _onContinue(context),
              child: Text(
                AppTexts.of(context).startExercise,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.onPrimary,
                ),
              ),
            ),
          ),
        ],
      ),
    ),
  );
}
