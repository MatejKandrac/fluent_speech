import 'package:flutter/material.dart';
import '../capture/capture_view.dart';
import '../recording_detail/recording_detail_view.dart';
import '../widgets/large_app_bar.dart';
import '../../core/detection_mode.dart';
import '../../db/database_helper.dart';
import '../../db/models/video_record.dart';

class DashboardView extends StatefulWidget {
  const DashboardView({super.key});

  @override
  State<DashboardView> createState() => _DashboardViewState();
}

class _DashboardViewState extends State<DashboardView> {
  late Future<List<VideoRecord>> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _future = DatabaseHelper().getAllVideoRecords();
  }

  void _startRecording() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => const CaptureView(mode: DetectionMode.stage),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: LargeAppBar(
          title: Text(
            'Recordings',
            style: Theme.of(context)
                .textTheme
                .headlineLarge
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
        ),
        floatingActionButton: FloatingActionButton(
          onPressed: _startRecording,
          child: const Icon(Icons.add),
        ),
        body: FutureBuilder<List<VideoRecord>>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            final records = snapshot.data ?? [];
            if (records.isEmpty) {
              return const Center(
                child: Text(
                  'No recordings yet.\nTap + to record a presentation.',
                  textAlign: TextAlign.center,
                ),
              );
            }
            return RefreshIndicator(
              onRefresh: () async => setState(_load),
              child: ListView.builder(
                itemCount: records.length,
                itemBuilder: (context, i) {
                  final record = records[i];
                  return ListTile(
                    leading: const CircleAvatar(child: Icon(Icons.videocam)),
                    title: Text(record.name),
                    subtitle: Text(
                      record.createdAt.toLocal().toString().substring(0, 16),
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => RecordingDetailView(record: record),
                        ),
                      );
                      setState(_load);
                    },
                  );
                },
              ),
            );
          },
        ),
      );
}