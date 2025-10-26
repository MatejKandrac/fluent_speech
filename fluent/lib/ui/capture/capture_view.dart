import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/calibration/calibrator_base.dart';
import '../../core/calibration/calibrators.dart';
import '../../core/detection/detector_base.dart';
import '../../core/detection/detectors.dart';
import '../../util/camera_utils.dart';
import '../../util/extensions.dart';
import '../../core/detection_mode.dart';
import 'providers/calibrate_providers.dart';
import '../summarise/summarise_view.dart';
import 'widget/missing_landmarks.dart';
import 'widget/record_button.dart';
import 'widget/start_counter.dart';
import 'widget/swap_camera_button.dart';

class CaptureView extends ConsumerStatefulWidget {
  const CaptureView({super.key, required this.mode});

  final DetectionMode mode;

  @override
  ConsumerState createState() => _CaptureViewState();
}

class _CaptureViewState extends ConsumerState<CaptureView> with WidgetsBindingObserver {
  late final DetectorBase processor;
  late final CalibratorBase calibrator;

  bool isCalibrating = true;

  List<dynamic> _missingLandmarks = [];
  bool allVisible = false;
  CameraController? _controller;
  CustomPainter? _painter;

  Timer? _timer;
  int currentTime = -3;

  @override
  void initState() {
    super.initState();
    processor = widget.mode.getDetector();
    calibrator = widget.mode.getCalibrator();
    _missingLandmarks = calibrator.requiredLandmarks();
    WidgetsBinding.instance.addObserver(this);
  }

  Future<void> _initializeCamera() async {
    final camera = await ref.watch(currentCameraProvider.future);
    final controller = await initCamera(_controller, camera);
    if (!mounted) return;
    setState(() {
      _controller = controller;
    });
    if (isCalibrating) {
      await startImageStream(
        controller: controller,
        onImage: _onCameraImage,
        onDemoImage: _onDemoImage,
      );
    }
  }

  Future<void> _onCameraImage(CameraImage image) async {
    final camera = await ref.watch(currentCameraProvider.future);
    if (_controller == null) return;
    final result = await processor.processImage(image, camera, _controller!.value.deviceOrientation);
    if (result == null) return;
    final painter = processor.buildPainter(result.$1, result.$2, camera.lensDirection);
    if (painter == null || !mounted) return;
    if (result.$1.isNotEmpty) {
      _missingLandmarks = calibrator.getMissingLandmarks(result.$1[0]);
    }
    setState(() {
      _painter = painter;
      if (!allVisible && _missingLandmarks.isEmpty) allVisible = true;
    });
  }

  void _onDemoImage() async {
    setState(() {
      calibrator as DemoCalibrator;
      _missingLandmarks = calibrator.getMissingLandmarks(0);
      if (!allVisible && _missingLandmarks.isEmpty) allVisible = true;
    });
  }

  Future<void> _onRecord() async {
    setState(() {
      isCalibrating = false;
    });
    await stopImageStream(_controller);
    _timer = Timer.periodic(Duration(seconds: 1), _timerIncrease);
  }

  void _timerIncrease(Timer t) {
    if (currentTime == 0) {
      if (_controller == null) return;
      _controller?.startVideoRecording();
    }
    setState(() => currentTime++);
  }

  Future<void> _endRecording() async {
    final controller = _controller;
    if (controller == null) return;
    final file = await controller.stopVideoRecording();
    if (!mounted) return;
    await Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (context) => SummariseView(mode: widget.mode, filePath: file.path),
      ),
    );
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    disposeCamera(_controller, isCalibrating);
    _timer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.inactive) {
      if (_controller == null || !_controller!.value.isInitialized) return;
      disposeCamera(_controller, isCalibrating);
      setState(() {
        _controller = null;
      });
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(currentCameraProvider);

    ref.listen(currentCameraProvider, (previous, next) {
      next.whenData((value) {
        if (_controller == null || _controller!.description.name != value.name) {
          setState(() {
            _controller = null;
          });
          _initializeCamera();
        }
      });
    });

    return Scaffold(
      body: SafeArea(
        child: Stack(
          fit: StackFit.expand,
          children: [
            Center(
              child: switch (_controller != null) {
                true => CameraPreview(
                  _controller!,
                  child: (_painter != null && isCalibrating) ? CustomPaint(painter: _painter) : null,
                ),
                false => CircularProgressIndicator(),
              },
            ),
            if (!isCalibrating && currentTime < 0) Center(child: StartCounter(secondsRemaining: currentTime * -1)),
            Positioned(
              bottom: 24,
              left: 0,
              right: 0,
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 24),
                child: Row(
                  spacing: 24,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: allVisible ? SizedBox() : MissingLandmarksView(_missingLandmarks),
                    ),
                    if (isCalibrating) SwapCameraButton(),
                  ],
                ),
              ),
            ),
            if (allVisible)
              Positioned(
                bottom: 24,
                left: 24,
                right: 24,
                child: Column(
                  children: [
                    if (!isCalibrating && currentTime >= 0) Text(currentTime.getFormattedTime()),
                    RecordButton(
                      onPressed: isCalibrating ? _onRecord : (currentTime >= 0 ? _endRecording : null),
                      isStop: !isCalibrating,
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
