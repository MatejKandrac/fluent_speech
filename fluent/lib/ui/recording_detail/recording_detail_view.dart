import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';

import '../../api/providers/api_providers.dart';
import '../../api/services/video_upload_service.dart';
import '../../db/database_helper.dart';
import '../../db/models/video_record.dart';

class RecordingDetailView extends ConsumerStatefulWidget {
  const RecordingDetailView({super.key, required this.record});

  final VideoRecord record;

  @override
  ConsumerState<RecordingDetailView> createState() => _RecordingDetailViewState();
}

class _RecordingDetailViewState extends ConsumerState<RecordingDetailView> {
  late VideoRecord _record;
  VideoPlayerController? _videoController;

  // Processing status
  bool _videoReady = false;
  bool _audioReady = false;
  bool _transcriptReady = false;
  bool _statusLoading = false;

  // Upload retry state
  bool _uploading = false;
  String? _uploadError;

  // Analysis state
  bool _analyzing = false;
  Map<String, dynamic>? _analysisResult;
  String? _analysisError;

  bool get _notUploaded => _record.remoteId == -1;

  @override
  void initState() {
    super.initState();
    _record = widget.record;
    _initVideo();
    if (!_notUploaded) _fetchStatus();
  }

  @override
  void dispose() {
    _videoController?.dispose();
    super.dispose();
  }

  void _initVideo() {
    final path = widget.record.localPath;
    if (path == null || path.isEmpty) return;

    _videoController = VideoPlayerController.file(File(path))
      ..initialize().then((_) {
        if (mounted) setState(() {});
      });
  }

  Future<void> _fetchStatus() async {
    setState(() => _statusLoading = true);
    try {
      final client = ref.read(videoApiClientProvider);
      final status = await client.getProcessingStatus(recordingId: widget.record.remoteId);
      if (mounted) {
        setState(() {
          _videoReady = status.videoProcessingFinished;
          _audioReady = status.audioProcessingFinished;
          _transcriptReady = status.transcriptProcessingFinished;
        });
      }
    } catch (e) {
      // Status fetch failed — keep defaults (false)
    } finally {
      if (mounted) setState(() => _statusLoading = false);
    }
  }

  Future<void> _retryUpload() async {
    final path = _record.localPath;
    if (path == null || path.isEmpty) return;

    setState(() {
      _uploading = true;
      _uploadError = null;
    });

    try {
      final service = ref.read(videoUploadServiceProvider);
      final response = await service.uploadVideo(path);

      if (response.success && response.id != null && response.filename != null) {
        final updated = _record.copyWith(
          remoteId: response.id!,
          filename: response.filename!,
        );
        await DatabaseHelper().updateVideoRecord(updated);
        if (mounted) {
          setState(() => _record = updated);
          _fetchStatus();
        }
      } else {
        if (mounted) setState(() => _uploadError = 'Server returned failure');
      }
    } catch (e) {
      if (mounted) setState(() => _uploadError = e.toString());
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  bool get _allReady => _videoReady && _audioReady && _transcriptReady;

  Future<void> _runAnalysis() async {
    setState(() {
      _analyzing = true;
      _analysisError = null;
      _analysisResult = null;
    });

    try {
      final client = ref.read(analysisApiClientProvider);
      final result = await client.runAnalysis(_record.remoteId);
      if (mounted) {
        setState(() => _analysisResult = result);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _analysisError = e.toString());
      }
    } finally {
      if (mounted) setState(() => _analyzing = false);
    }
  }

  void _seekTo(double seconds) {
    _videoController?.seekTo(Duration(milliseconds: (seconds * 1000).round()));
    _videoController?.play();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Text(_record.name),
      actions: [
        if (!_notUploaded)
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh status',
            onPressed: _fetchStatus,
          ),
      ],
    ),
    body: SafeArea(
      child: Column(
        children: [
          // Video player
          _VideoSection(controller: _videoController),

          if (_notUploaded) ...[
            // Upload retry section
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    children: const [
                      Icon(Icons.cloud_off, color: Colors.orange),
                      SizedBox(width: 8),
                      Text('Not uploaded to server yet', style: TextStyle(color: Colors.orange)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (_uploadError != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        'Error: $_uploadError',
                        style: const TextStyle(color: Colors.red, fontSize: 12),
                      ),
                    ),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _uploading ? null : _retryUpload,
                      icon: _uploading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.cloud_upload),
                      label: Text(_uploading ? 'Uploading...' : 'Upload to server'),
                    ),
                  ),
                ],
              ),
            ),
          ] else ...[
            // Processing status row
            _StatusRow(
              videoReady: _videoReady,
              audioReady: _audioReady,
              transcriptReady: _transcriptReady,
              loading: _statusLoading,
            ),

            const Divider(height: 1),

            // Analyze button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: (_allReady && !_analyzing && _analysisResult == null) ? _runAnalysis : null,
                  icon: _analyzing
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.analytics),
                  label: Text(
                    _analyzing
                        ? 'Analyzing...'
                        : _analysisResult != null
                        ? 'Analysis complete'
                        : _allReady
                        ? 'Analyze presentation'
                        : 'Waiting for processing...',
                  ),
                ),
              ),
            ),

            if (_analysisError != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(
                  'Error: $_analysisError',
                  style: const TextStyle(color: Colors.red),
                ),
              ),

            // Results
            if (_analysisResult != null)
              Expanded(
                child: _ResultsSection(
                  result: _analysisResult!,
                  onSeek: _seekTo,
                ),
              )
            else
              const SizedBox.shrink(),
          ], // end else (uploaded)
        ],
      ),
    ),
  );
}

// ─── Video section ────────────────────────────────────────────────────────────

class _VideoSection extends StatefulWidget {
  const _VideoSection({required this.controller});

  final VideoPlayerController? controller;

  @override
  State<_VideoSection> createState() => _VideoSectionState();
}

class _VideoSectionState extends State<_VideoSection> {
  @override
  void initState() {
    super.initState();
    widget.controller?.addListener(_onControllerUpdate);
  }

  @override
  void didUpdateWidget(_VideoSection old) {
    super.didUpdateWidget(old);
    old.controller?.removeListener(_onControllerUpdate);
    widget.controller?.addListener(_onControllerUpdate);
  }

  @override
  void dispose() {
    widget.controller?.removeListener(_onControllerUpdate);
    super.dispose();
  }

  void _onControllerUpdate() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final ctrl = widget.controller;
    if (ctrl == null || !ctrl.value.isInitialized) {
      return Container(
        height: 220,
        color: Colors.black,
        child: const Center(
          child: Text('No video available', style: TextStyle(color: Colors.white54)),
        ),
      );
    }

    // Cap the player to 220dp. AspectRatio inside Center correctly handles both
    // portrait (black pillars on sides) and landscape (black bars top/bottom).
    return Container(
      height: 220,
      color: Colors.black,
      child: Stack(
        fit: StackFit.expand,
        children: [
          Center(
            child: AspectRatio(
              aspectRatio: ctrl.value.aspectRatio,
              child: VideoPlayer(ctrl),
            ),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: _VideoControls(controller: ctrl),
          ),
        ],
      ),
    );
  }
}

class _VideoControls extends StatelessWidget {
  const _VideoControls({required this.controller});

  final VideoPlayerController controller;

  @override
  Widget build(BuildContext context) {
    final position = controller.value.position;
    final duration = controller.value.duration;
    final isPlaying = controller.value.isPlaying;

    return Container(
      color: Colors.black45,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          VideoProgressIndicator(
            controller,
            allowScrubbing: true,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          ),
          Row(
            children: [
              IconButton(
                icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow, color: Colors.white),
                onPressed: () => isPlaying ? controller.pause() : controller.play(),
              ),
              Text(
                '${_fmt(position)} / ${_fmt(duration)}',
                style: const TextStyle(color: Colors.white, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _fmt(Duration d) {
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$s';
  }
}

// ─── Status row ───────────────────────────────────────────────────────────────

class _StatusRow extends StatelessWidget {
  const _StatusRow({
    required this.videoReady,
    required this.audioReady,
    required this.transcriptReady,
    required this.loading,
  });

  final bool videoReady;
  final bool audioReady;
  final bool transcriptReady;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Padding(
        padding: EdgeInsets.all(8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
            SizedBox(width: 8),
            Text('Checking processing status...'),
          ],
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _StatusChip(label: 'Video', ready: videoReady),
          _StatusChip(label: 'Audio', ready: audioReady),
          _StatusChip(label: 'Transcript', ready: transcriptReady),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label, required this.ready});

  final String label;
  final bool ready;

  @override
  Widget build(BuildContext context) => Chip(
    avatar: Icon(
      ready ? Icons.check_circle : Icons.hourglass_empty,
      size: 16,
      color: ready ? Colors.green : Colors.orange,
    ),
    label: Text(label, style: const TextStyle(fontSize: 12)),
    padding: EdgeInsets.zero,
    visualDensity: VisualDensity.compact,
  );
}

// ─── Results section ──────────────────────────────────────────────────────────

class _ResultsSection extends StatelessWidget {
  const _ResultsSection({required this.result, required this.onSeek});

  final Map<String, dynamic> result;
  final void Function(double seconds) onSeek;

  @override
  Widget build(BuildContext context) {
    final performance = result['performance'] as Map<String, dynamic>?;
    final analysisResults = result['results'] as Map<String, dynamic>? ?? {};

    final tabs = _buildTabs(analysisResults);

    return DefaultTabController(
      length: tabs.length + 1,
      child: Column(
        children: [
          TabBar(
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            tabs: [
              const Tab(text: 'Score'),
              ...tabs.map((t) => Tab(text: t.label)),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _ScoreTab(performance: performance),
                ...tabs.map((t) => _EventsTab(tab: t, onSeek: onSeek)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<_TabData> _buildTabs(Map<String, dynamic> results) {
    final tabs = <_TabData>[];

    // Pitch — monotonous segments
    final pitch = results['pitch'] as Map<String, dynamic>?;
    final monotone = _extractSegments(pitch?['monotonous_segments']);
    if (monotone.isNotEmpty) {
      tabs.add(
        _TabData(
          label: 'Monotone',
          icon: Icons.graphic_eq,
          events: monotone,
          description: 'Monotonous speech segments',
        ),
      );
    }

    // Volume
    final volume = results['volume'] as Map<String, dynamic>?;
    final tooSoft = _extractSegments(volume?['too_soft_segments']);
    final tooLoud = _extractSegments(volume?['too_loud_segments']);
    if (tooSoft.isNotEmpty || tooLoud.isNotEmpty) {
      tabs.add(
        _TabData(
          label: 'Volume',
          icon: Icons.volume_up,
          events: [
            ..._labelEvents(tooSoft, 'Too soft'),
            ..._labelEvents(tooLoud, 'Too loud'),
          ],
          description: 'Volume issues',
        ),
      );
    }

    // Filler words
    final filler = results['filler_words'] as Map<String, dynamic>?;
    final fillerEvents = _extractFillerOccurrences(filler?['filler_occurrences']);
    if (fillerEvents.isNotEmpty) {
      tabs.add(
        _TabData(
          label: 'Filler words',
          icon: Icons.record_voice_over,
          events: fillerEvents,
          description: 'Filler word occurrences',
        ),
      );
    }

    // Arm movement
    final arm = results['arm_movement'] as Map<String, dynamic>?;
    final anomalies = arm?['anomalies'] as Map<String, dynamic>?;
    final noMovement = _extractArmPeriods(anomalies?['no_movement_periods']);
    final excessive = _extractArmPeriods(anomalies?['excessive_movement_periods']);
    if (noMovement.isNotEmpty || excessive.isNotEmpty) {
      tabs.add(
        _TabData(
          label: 'Arms',
          icon: Icons.accessibility_new,
          events: [
            ..._labelEvents(noMovement, 'No movement'),
            ..._labelEvents(excessive, 'Excessive'),
          ],
          description: 'Arm movement issues',
        ),
      );
    }

    // Hip swaying
    final hip = results['hip'] as Map<String, dynamic>?;
    final hipSegments = _extractSegments(hip?['swaying_segments']);
    if (hipSegments.isNotEmpty) {
      tabs.add(
        _TabData(
          label: 'Hip sway',
          icon: Icons.directions_walk,
          events: hipSegments,
          description: 'Hip swaying detected',
        ),
      );
    }

    // Eye contact
    final eye = results['eye_contact'] as Map<String, dynamic>?;
    if (eye != null) {
      final lookingAway = _extractEyeEvents(eye['looking_away_events']);
      final staring = _extractEyeEvents(eye['staring_events']);
      final heatmapData = eye['heatmap'] as Map<String, dynamic>?;
      final audienceZone = eye['audience_zone_thresholds'] as Map<String, dynamic>?;
      if (lookingAway.isNotEmpty || staring.isNotEmpty || heatmapData != null) {
        tabs.add(
          _TabData(
            label: 'Eye contact',
            icon: Icons.visibility,
            events: [
              ..._labelEvents(lookingAway, 'Looking away'),
              ..._labelEvents(staring, 'Staring'),
            ],
            description: 'Eye contact issues',
            heatmapData: heatmapData,
            audienceZone: audienceZone,
          ),
        );
      }
    }

    return tabs;
  }

  /// Safely converts a dynamic value to double — handles num, String, or null.
  double? _toDouble(dynamic v) {
    if (v == null) return null;
    if (v is num) return v.toDouble();
    if (v is String) return double.tryParse(v);
    return null;
  }

  List<_Event> _extractSegments(dynamic raw) {
    if (raw == null) return [];
    final list = raw as List<dynamic>;
    return list.map((e) {
      final m = e as Map<String, dynamic>;
      return _Event(
        start: _toDouble(m['start_timestamp']) ?? 0,
        end: _toDouble(m['end_timestamp']) ?? 0,
        label: null,
      );
    }).toList();
  }

  List<_Event> _extractEyeEvents(dynamic raw) {
    if (raw == null) return [];
    final list = raw as List<dynamic>;
    return list.map((e) {
      final m = e as Map<String, dynamic>;
      final dur = _toDouble(m['duration_seconds']) ?? 0;
      final start = _toDouble(m['start_timestamp']) ?? 0;
      return _Event(start: start, end: start + dur, label: null);
    }).toList();
  }

  List<_Event> _extractArmPeriods(dynamic raw) {
    if (raw == null) return [];
    final list = raw as List<dynamic>;
    return list.map((e) {
      final m = e as Map<String, dynamic>;
      final start = _toDouble(m['start_time']) ?? _toDouble(m['start_timestamp']) ?? 0;
      final end = _toDouble(m['end_time']) ?? _toDouble(m['end_timestamp']) ?? 0;
      return _Event(start: start, end: end, label: null);
    }).toList();
  }

  List<_Event> _extractFillerOccurrences(dynamic raw) {
    if (raw == null) return [];
    final list = raw as List<dynamic>;
    return list.map((e) {
      final m = e as Map<String, dynamic>;
      return _Event(
        start: _toDouble(m['start_time']) ?? 0,
        end: _toDouble(m['end_time']) ?? 0,
        label: m['word'] as String?,
      );
    }).toList();
  }

  List<_Event> _labelEvents(List<_Event> events, String prefix) =>
      events.map((e) => _Event(start: e.start, end: e.end, label: prefix)).toList();
}

// ─── Score tab ────────────────────────────────────────────────────────────────

class _ScoreTab extends StatelessWidget {
  const _ScoreTab({required this.performance});

  final Map<String, dynamic>? performance;

  @override
  Widget build(BuildContext context) {
    if (performance == null || performance!['success'] != true) {
      return const Center(child: Text('Performance score not available.'));
    }

    final total = (performance!['total_score'] as num).toDouble();
    final label = performance!['total_label'] as String? ?? '';
    final dimensions = performance!['dimensions'] as Map<String, dynamic>? ?? {};
    final recommendations = (performance!['recommendations'] as List<dynamic>?) ?? [];

    final color = _scoreColor(total);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Total score card
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                SizedBox(
                  width: 72,
                  height: 72,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      CircularProgressIndicator(
                        value: total / 100,
                        strokeWidth: 8,
                        color: color,
                        backgroundColor: color.withOpacity(0.2),
                      ),
                      Text(
                        total.toStringAsFixed(0),
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Overall score', style: Theme.of(context).textTheme.bodySmall),
                    Text(
                      label,
                      style: Theme.of(
                        context,
                      ).textTheme.titleMedium?.copyWith(color: color, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        // Dimension scores
        ...dimensions.entries.map((entry) {
          final dim = entry.value as Map<String, dynamic>;
          final score = (dim['score'] as num).toDouble();
          final weight = (dim['weight'] as num).toDouble();
          final dimColor = _scoreColor(score);
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                SizedBox(
                  width: 80,
                  child: Text(
                    _dimName(entry.key),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: score / 100,
                      minHeight: 12,
                      color: dimColor,
                      backgroundColor: dimColor.withOpacity(0.15),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                SizedBox(
                  width: 36,
                  child: Text(
                    score.toStringAsFixed(0),
                    style: TextStyle(fontWeight: FontWeight.bold, color: dimColor, fontSize: 13),
                  ),
                ),
                Text(
                  '×${weight.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          );
        }),

        if (recommendations.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('Recommendations', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...recommendations.map(
            (r) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.info_outline, size: 16, color: Colors.blue),
                  const SizedBox(width: 8),
                  Expanded(child: Text(r.toString(), style: Theme.of(context).textTheme.bodySmall)),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }

  Color _scoreColor(double score) {
    if (score >= 90) return Colors.green;
    if (score >= 75) return Colors.lightGreen;
    if (score >= 60) return Colors.orange;
    if (score >= 40) return Colors.deepOrange;
    return Colors.red;
  }

  String _dimName(String key) {
    const names = {
      'voice': 'Voice',
      'fluency': 'Fluency',
      'body': 'Body',
      'eye_contact': 'Eye',
    };
    return names[key] ?? key;
  }
}

// ─── Events tab ───────────────────────────────────────────────────────────────

class _TabData {
  final String label;
  final IconData icon;
  final List<_Event> events;
  final String description;
  final Map<String, dynamic>? heatmapData;
  final Map<String, dynamic>? audienceZone;

  _TabData({
    required this.label,
    required this.icon,
    required this.events,
    required this.description,
    this.heatmapData,
    this.audienceZone,
  });
}

class _Event {
  final double start;
  final double end;
  final String? label;

  _Event({required this.start, required this.end, this.label});

  double get duration => end - start;
}

class _EventsTab extends StatelessWidget {
  const _EventsTab({required this.tab, required this.onSeek});

  final _TabData tab;
  final void Function(double) onSeek;

  Widget _buildEventTile(BuildContext context, _Event event) => ListTile(
    leading: CircleAvatar(
      radius: 18,
      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      child: Icon(tab.icon, size: 16, color: Theme.of(context).colorScheme.onPrimaryContainer),
    ),
    title: Text(event.label ?? tab.label),
    subtitle: Text(
      '${_fmt(event.start)} – ${_fmt(event.end)}  (${event.duration.toStringAsFixed(1)}s)',
      style: const TextStyle(fontSize: 12),
    ),
    trailing: const Icon(Icons.play_circle_outline),
    onTap: () => onSeek(event.start),
  );

  @override
  Widget build(BuildContext context) {
    final sorted = [...tab.events]..sort((a, b) => a.start.compareTo(b.start));

    if (tab.heatmapData != null) {
      return Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: _GazeHeatmap(
              heatmapData: tab.heatmapData!,
              audienceZone: tab.audienceZone,
            ),
          ),
          const Divider(height: 8),
          Expanded(
            child: sorted.isEmpty
                ? const Center(child: Text('No eye contact issues detected.'))
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: sorted.length,
                    itemBuilder: (ctx, i) => _buildEventTile(ctx, sorted[i]),
                  ),
          ),
        ],
      );
    }

    if (sorted.isEmpty) {
      return Center(child: Text('No ${tab.description.toLowerCase()} detected.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: sorted.length,
      itemBuilder: (context, i) => _buildEventTile(context, sorted[i]),
    );
  }

  String _fmt(double s) {
    final d = Duration(milliseconds: (s * 1000).round());
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final sec = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$sec';
  }
}

// ─── Gaze heatmap ─────────────────────────────────────────────────────────────

class _GazeHeatmap extends StatelessWidget {
  const _GazeHeatmap({required this.heatmapData, this.audienceZone});

  final Map<String, dynamic> heatmapData;
  final Map<String, dynamic>? audienceZone;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          'Gaze Heatmap',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 6),
        SizedBox(
          height: 160,
          width: double.infinity,
          child: CustomPaint(
            painter: _HeatmapPainter(heatmapData, audienceZone),
          ),
        ),
        const SizedBox(height: 6),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Less time', style: TextStyle(fontSize: 10, color: Colors.black54)),
            const SizedBox(width: 6),
            Container(
              width: 100,
              height: 10,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Colors.black, Colors.red, Colors.orange, Colors.yellow, Colors.white],
                ),
                border: Border.all(color: Colors.grey, width: 0.5),
              ),
            ),
            const SizedBox(width: 6),
            const Text('More time', style: TextStyle(fontSize: 10, color: Colors.black54)),
          ],
        ),
      ],
    );
  }
}

class _HeatmapPainter extends CustomPainter {
  _HeatmapPainter(this.heatmapData, this.audienceZone);

  final Map<String, dynamic> heatmapData;
  final Map<String, dynamic>? audienceZone;

  @override
  void paint(Canvas canvas, Size size) {
    final rawMatrix = heatmapData['duration_matrix'] as List<dynamic>;
    final yawBins = (heatmapData['yaw_bins'] as List<dynamic>)
        .map((v) => (v as num).toDouble())
        .toList();
    final pitchBins = (heatmapData['pitch_bins'] as List<dynamic>)
        .map((v) => (v as num).toDouble())
        .toList();

    final nPitch = rawMatrix.length;
    if (nPitch == 0) return;
    final nYaw = (rawMatrix[0] as List<dynamic>).length;
    if (nYaw == 0) return;

    double maxVal = 0;
    for (final row in rawMatrix) {
      for (final v in row as List<dynamic>) {
        final d = (v as num).toDouble();
        if (d > maxVal) maxVal = d;
      }
    }

    const leftPad = 28.0;
    const bottomPad = 18.0;
    const topPad = 2.0;
    const rightPad = 2.0;
    final plotW = size.width - leftPad - rightPad;
    final plotH = size.height - topPad - bottomPad;
    final cellW = plotW / nYaw;
    final cellH = plotH / nPitch;

    // Draw cells — row 0 = lowest pitch bin (bottom of screen)
    for (int pi = 0; pi < nPitch; pi++) {
      final row = rawMatrix[pi] as List<dynamic>;
      for (int yi = 0; yi < nYaw; yi++) {
        final val = (row[yi] as num).toDouble();
        final t = maxVal > 0 ? (val / maxVal).clamp(0.0, 1.0) : 0.0;
        canvas.drawRect(
          Rect.fromLTWH(
            leftPad + yi * cellW,
            topPad + (nPitch - 1 - pi) * cellH,
            cellW,
            cellH,
          ),
          Paint()..color = _hotColor(t),
        );
      }
    }

    // Border
    canvas.drawRect(
      Rect.fromLTWH(leftPad, topPad, plotW, plotH),
      Paint()
        ..color = Colors.grey.shade400
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1,
    );

    // Center crosshairs
    final yawRange = yawBins.last - yawBins.first;
    final pitchRange = pitchBins.last - pitchBins.first;
    final cx = leftPad + (0 - yawBins.first) / yawRange * plotW;
    final cy = topPad + (pitchBins.last - 0) / pitchRange * plotH;
    final crossPaint = Paint()
      ..color = Colors.white.withOpacity(0.4)
      ..strokeWidth = 0.8;
    canvas.drawLine(Offset(leftPad, cy), Offset(leftPad + plotW, cy), crossPaint);
    canvas.drawLine(Offset(cx, topPad), Offset(cx, topPad + plotH), crossPaint);

    // Audience zone rectangle
    if (audienceZone != null) {
      final az = audienceZone!;
      final yMin = (az['yaw_min'] as num).toDouble();
      final yMax = (az['yaw_max'] as num).toDouble();
      final pMin = (az['pitch_min'] as num).toDouble();
      final pMax = (az['pitch_max'] as num).toDouble();
      canvas.drawRect(
        Rect.fromLTRB(
          leftPad + (yMin - yawBins.first) / yawRange * plotW,
          topPad + (pitchBins.last - pMax) / pitchRange * plotH,
          leftPad + (yMax - yawBins.first) / yawRange * plotW,
          topPad + (pitchBins.last - pMin) / pitchRange * plotH,
        ),
        Paint()
          ..color = Colors.green
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2,
      );
    }

    // Axis labels
    final tp = TextPainter(textDirection: TextDirection.ltr);
    const labelStyle = TextStyle(fontSize: 8, color: Colors.black54);

    // Yaw labels at bin edges (every 30°)
    for (int i = 0; i < yawBins.length; i++) {
      final yaw = yawBins[i];
      if (yaw.round() % 30 == 0) {
        final x = leftPad + i / nYaw * plotW;
        tp.text = TextSpan(text: '${yaw.round()}', style: labelStyle);
        tp.layout();
        tp.paint(canvas, Offset(x - tp.width / 2, topPad + plotH + 2));
      }
    }

    // Pitch labels at bin edges (every 15°)
    for (int i = 0; i < pitchBins.length; i++) {
      final pitch = pitchBins[i];
      if (pitch.round() % 15 == 0) {
        final y = topPad + (pitchBins.last - pitch) / pitchRange * plotH;
        tp.text = TextSpan(text: '${pitch.round()}°', style: labelStyle);
        tp.layout();
        tp.paint(canvas, Offset(leftPad - tp.width - 2, y - tp.height / 2));
      }
    }
  }

  Color _hotColor(double t) {
    if (t <= 0) return Colors.black;
    if (t >= 1) return Colors.white;
    if (t < 1 / 3) {
      return Color.fromARGB(255, (t * 3 * 255).round(), 0, 0);
    } else if (t < 2 / 3) {
      return Color.fromARGB(255, 255, ((t - 1 / 3) * 3 * 255).round(), 0);
    } else {
      return Color.fromARGB(255, 255, 255, ((t - 2 / 3) * 3 * 255).round());
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
