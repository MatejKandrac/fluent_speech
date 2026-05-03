import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';
import 'package:flutter_native_video_trimmer/flutter_native_video_trimmer.dart';
import 'package:path_provider/path_provider.dart';
import '../../core/detection_mode.dart';
import '../summarise/summarise_view.dart';
import '../widgets/large_app_bar.dart';

class CropView extends ConsumerStatefulWidget {
  const CropView({
    super.key,
    required this.mode,
    required this.filePath,
  });

  final String filePath;
  final DetectionMode mode;

  @override
  ConsumerState<CropView> createState() => _CropViewState();
}

class _CropViewState extends ConsumerState<CropView> {
  late VideoPlayerController _videoController;
  bool _isInitialized = false;
  bool _isProcessing = false;

  // Trim values in seconds
  final double _startTime = 0.0;
  double _endTime = 0.0;
  double _maxDuration = 0.0;

  @override
  void initState() {
    super.initState();
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    _videoController = VideoPlayerController.file(File(widget.filePath));

    try {
      await _videoController.initialize();
      _maxDuration = _videoController.value.duration.inMilliseconds / 1000.0;
      _endTime = _maxDuration;

      setState(() {
        _isInitialized = true;
      });

      // Auto-play the video in loop
      _videoController.setLooping(true);
      _videoController.play();
    } catch (e) {
      print('Error initializing video: $e');
    }
  }

  Future<void> _cropVideo() async {
    setState(() {
      _isProcessing = true;
    });

    try {
      // Pause the video player
      await _videoController.pause();

      // Generate output file path
      final directory = await getTemporaryDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final outputPath = '${directory.path}/cropped_$timestamp.mp4';

      print('Trimming video from ${_startTime}s to ${_endTime}s');
      print('Input: ${widget.filePath}');
      print('Output: $outputPath');

      // Use flutter_native_video_trimmer to trim the video
      final trimmer = VideoTrimmer();
      await trimmer.loadVideo(widget.filePath);
      final result = await trimmer.trimVideo(
        startTimeMs: 0,
        endTimeMs: (_endTime * 1000).toInt(),
        includeAudio: true
      );

      if (result != null) {
        print('Video cropped successfully: $outputPath');
        final file = File(widget.filePath);
        await file.delete();

        if (!mounted) return;

        // Navigate to summarise view with cropped video
        await Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (context) => SummariseView(
              mode: widget.mode,
              filePath: result,
            ),
          ),
        );
      } else {
        print('Video trimming failed');

        if (!mounted) return;

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Nepodarilo sa orezať video.'),
            backgroundColor: Colors.red,
          ),
        );

        setState(() {
          _isProcessing = false;
        });
      }
    } catch (e) {
      print('Error cropping video: $e');

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Chyba: $e'),
          backgroundColor: Colors.red,
        ),
      );

      setState(() {
        _isProcessing = false;
      });
    }
  }

  String _formatDuration(double seconds) {
    final duration = Duration(milliseconds: (seconds * 1000).round());
    final minutes = duration.inMinutes;
    final secs = duration.inSeconds % 60;
    final millis = duration.inMilliseconds % 1000 ~/ 10;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}.${millis.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _videoController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: LargeAppBar(
        title: Text(
          'Orezať video',
          style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: _isInitialized
            ? Column(
                children: [
                  // Video Player
                  Expanded(
                    child: Center(
                      child: AspectRatio(
                        aspectRatio: _videoController.value.aspectRatio,
                        child: VideoPlayer(_videoController),
                      ),
                    ),
                  ),

                  // Controls
                  Container(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Instructions
                        Text(
                          'Pohybujte sliderom pre orezanie videa',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Odstránte časť, kde sa vrátite ku kamere',
                          style: Theme.of(context).textTheme.bodyMedium,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),

                        // Duration display
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Štart',
                                  style: Theme.of(context).textTheme.labelSmall,
                                ),
                                Text(
                                  _formatDuration(_startTime),
                                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                        fontWeight: FontWeight.bold,
                                      ),
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  'Koniec',
                                  style: Theme.of(context).textTheme.labelSmall,
                                ),
                                Text(
                                  _formatDuration(_endTime),
                                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                        fontWeight: FontWeight.bold,
                                      ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),

                        // Trim slider
                        Slider(
                          value: _endTime,
                          min: 0.0,
                          max: _maxDuration,
                          divisions: (_maxDuration * 10).round(),
                          label: _formatDuration(_endTime),
                          onChanged: (value) {
                            setState(() {
                              _endTime = value;
                              if (_endTime < _startTime) {
                                _endTime = _startTime;
                              }
                            });
                          },
                          onChangeEnd: (value) {
                            // Seek to the end position to preview
                            _videoController.seekTo(Duration(milliseconds: (value * 1000).round()));
                          },
                        ),

                        Text(
                          'Celková dĺžka: ${_formatDuration(_endTime - _startTime)}',
                          style: Theme.of(context).textTheme.bodyMedium,
                          textAlign: TextAlign.center,
                        ),

                        const SizedBox(height: 24),

                        // Action buttons
                        if (_isProcessing)
                          const Center(
                            child: Column(
                              children: [
                                CircularProgressIndicator(),
                                SizedBox(height: 16),
                                Text('Spracovanie videa...'),
                              ],
                            ),
                          )
                        else
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: () {
                                    // Skip cropping and go directly to summarise
                                    Navigator.of(context).pushReplacement(
                                      MaterialPageRoute(
                                        builder: (context) => SummariseView(
                                          mode: widget.mode,
                                          filePath: widget.filePath,
                                        ),
                                      ),
                                    );
                                  },
                                  child: const Text('Preskočiť'),
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                flex: 2,
                                child: FilledButton(
                                  onPressed: _cropVideo,
                                  child: const Text('Orezať a pokračovať'),
                                ),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ),
                ],
              )
            : const Center(
                child: CircularProgressIndicator(),
              ),
      ),
    );
}
