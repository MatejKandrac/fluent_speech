import 'package:flutter/material.dart';

class RecordButton extends StatelessWidget {
  const RecordButton({
    super.key,
    required this.onPressed,
    this.isStop = false,
  });

  final GestureTapCallback? onPressed;
  final bool isStop;

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onPressed,
    borderRadius: BorderRadius.circular(30),
    child: Container(
      width: 60,
      height: 60,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Theme.of(context).colorScheme.surface,
        border: BoxBorder.all(color: Theme.of(context).colorScheme.onSurface, width: 2),
      ),
      padding: EdgeInsets.all(4),
      child: Container(
        decoration: BoxDecoration(shape: BoxShape.circle, color: Theme.of(context).colorScheme.onSurface),
        child: isStop ? Icon(Icons.stop, color: Theme.of(context).colorScheme.errorContainer) : null,
      ),
    ),
  );
}
