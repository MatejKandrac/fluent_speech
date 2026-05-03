import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../capture/capture_view.dart';
import '../recording_detail/recording_detail_view.dart';
import '../summarise/summarise_view.dart';
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

  Future<void> _pickFromGallery() async {
    final video = await ImagePicker().pickVideo(source: ImageSource.gallery);
    if (video == null || !mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => SummariseView(
          mode: DetectionMode.stage,
          filePath: video.path,
        ),
      ),
    );
  }

  void _showAddOptions() {
    showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.videocam),
              title: const Text('Natočiť video'),
              onTap: () {
                Navigator.of(ctx).pop();
                _startRecording();
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Vybrať z galérie'),
              onTap: () {
                Navigator.of(ctx).pop();
                _pickFromGallery();
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: LargeAppBar(
          title: Text(
            'Nahrávky',
            style: Theme.of(context)
                .textTheme
                .headlineLarge
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
        ),
        floatingActionButton: FloatingActionButton(
          onPressed: _showAddOptions,
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
                  'Zatiaľ ziadne nahrávky.\nStlač + pre nahratie prezentácie.',
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