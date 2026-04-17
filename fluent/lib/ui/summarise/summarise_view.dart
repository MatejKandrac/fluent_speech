import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/services/video_upload_service.dart';
import '../../core/detection_mode.dart';
import '../../db/database_helper.dart';
import '../../db/models/video_record.dart';
import '../../localizations/localizations.dart';
import '../recording_detail/recording_detail_view.dart';
import '../widgets/large_app_bar.dart';

class SummariseView extends ConsumerStatefulWidget {
  const SummariseView({
    super.key,
    required this.mode,
    required this.filePath,
  });

  final String filePath;
  final DetectionMode mode;

  @override
  ConsumerState<SummariseView> createState() => _SummariseViewState();
}

class _SummariseViewState extends ConsumerState<SummariseView> {
  final TextEditingController _nameController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _handleUpload(BuildContext context) async {
    if (!_formKey.currentState!.validate()) return;

    // Save locally immediately with remoteId = -1 (not yet uploaded)
    final localRecord = VideoRecord(
      remoteId: -1,
      name: _nameController.text.trim(),
      filename: '',
      localPath: widget.filePath,
      createdAt: DateTime.now(),
    );

    final db = DatabaseHelper();
    final localId = await db.insertVideoRecord(localRecord);
    final savedRecord = localRecord.copyWith(id: localId);

    // Attempt upload
    final notifier = ref.read(videoUploadNotifierProvider.notifier);
    await notifier.uploadVideo(widget.filePath);

    final state = ref.read(videoUploadNotifierProvider);
    if (!context.mounted) return;

    VideoRecord finalRecord = savedRecord;

    if (state.response != null && state.response!.success &&
        state.response!.id != null && state.response!.filename != null) {
      // Upload succeeded — update the local record with server data
      finalRecord = savedRecord.copyWith(
        remoteId: state.response!.id!,
        filename: state.response!.filename!,
      );
      await db.updateVideoRecord(finalRecord);
    } else if (state.error != null) {
      // Show snackbar — ScaffoldMessenger survives pushReplacement
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Upload failed: ${state.error}'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }

    if (context.mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => RecordingDetailView(record: finalRecord),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final uploadState = ref.watch(videoUploadNotifierProvider);

    return Scaffold(
      appBar: LargeAppBar(
        title: Text(
          AppTexts.of(context).summary,
          style: Theme.of(context).textTheme.headlineLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 16),
                        Text(
                          'Recording Name',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 8),
                        TextFormField(
                          controller: _nameController,
                          enabled: !uploadState.isUploading,
                          decoration: const InputDecoration(
                            hintText: 'Enter a name for this recording',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.videocam),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return 'Please enter a recording name';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 24),
                        if (uploadState.isUploading) ...[
                          const Center(
                            child: Column(
                              children: [
                                CircularProgressIndicator(),
                                SizedBox(height: 16),
                                Text('Uploading video...'),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: uploadState.isUploading ? null : () => _handleUpload(context),
                    child: Text(
                      uploadState.isUploading
                          ? 'Uploading...'
                          : AppTexts.of(context).sendForAnalysis,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
