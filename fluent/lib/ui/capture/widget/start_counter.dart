import 'package:flutter/material.dart';

import '../../../localizations/localizations.dart';

class StartCounter extends StatelessWidget {
  const StartCounter({super.key, required this.secondsRemaining});

  final int secondsRemaining;

  @override
  Widget build(BuildContext context) => Container(
    decoration: BoxDecoration(color: Color(0x80000000), borderRadius: BorderRadius.circular(15)),
    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(
          AppTexts.of(context).getReady,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        Text(
          secondsRemaining.toString(),
          style: Theme.of(context).textTheme.displayLarge,
        ),
      ],
    ),
  );
}
