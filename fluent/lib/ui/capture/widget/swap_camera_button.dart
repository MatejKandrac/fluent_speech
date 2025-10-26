import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/calibrate_providers.dart';

class SwapCameraButton extends ConsumerWidget {
  const SwapCameraButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentCamera = ref.watch(currentCameraProvider.notifier);
    final currentCameraAsync = ref.watch(currentCameraProvider);
    return SizedBox(
      width: 56,
      height: 56,
      child: FilledButton(
        onPressed: currentCameraAsync.when(
          data: (data) => currentCamera.cameraCount > 1 ? currentCamera.next : null,
          loading: () => null,
          error: (_, _) => null,
        ),
        child: Icon(
          Icons.cameraswitch_rounded,
          size: 24,
        ),
      ),
    );
  }
}
