import 'package:flutter/material.dart';
import '../../localizations/localizations.dart';
import '../detail/exercise_detail_view.dart';
import '../widgets/large_app_bar.dart';
import '../../core/detection_mode.dart';

class DashboardView extends StatelessWidget {
  const DashboardView({super.key});

  void onModeSelect(BuildContext context, DetectionMode mode) {
    Navigator.of(context).push(MaterialPageRoute(builder: (context) => ExerciseDetailView(mode: mode)));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: LargeAppBar(
      title: Text(
        'Fluent',
        style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.bold),
      ),
      subtitle: Text(
        AppTexts.of(context).startExercise,
        style: Theme.of(context).textTheme.bodyLarge,
      ),
    ),
    body: Padding(
      padding: EdgeInsets.symmetric(horizontal: 20),
      child: GridView.builder(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: MediaQuery.of(context).orientation == Orientation.portrait ? 2 : 3,
          childAspectRatio: 0.7,
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
        ),
        itemCount: DetectionMode.values.length,
        itemBuilder: (context, index) {
          final mode = DetectionMode.values[index];
          return _GridItem(mode: mode, onPressed: () => onModeSelect(context, mode));
        },
      ),
    ),
  );
}

class _GridItem extends StatelessWidget {
  const _GridItem({required this.mode, required this.onPressed});

  final DetectionMode mode;
  final GestureTapCallback onPressed;

  @override
  Widget build(BuildContext context) => SizedBox(
    child: Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onPressed,
        child: Padding(
          padding: EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 12,
            children: [
              Hero(
                tag: mode,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: ConstrainedBox(
                    constraints: BoxConstraints(minHeight: 150, maxHeight: 150, minWidth: double.infinity),
                    child: Image.asset(
                      mode.getCoverImage(),
                      fit: BoxFit.cover,
                    ),
                  ),
                ),
              ),
              Text(
                mode.getText(context),
                style:
                    Theme.of(
                      context,
                    ).textTheme.bodyLarge?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
