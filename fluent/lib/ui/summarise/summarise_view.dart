import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/services/video_upload_service.dart';
import '../../core/detection_mode.dart';
import '../../db/database_helper.dart';
import '../../db/models/video_record.dart';
import '../../localizations/localizations.dart';
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
    // Validate the form
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final notifier = ref.read(videoUploadNotifierProvider.notifier);

    await notifier.uploadVideo(widget.filePath);

    final state = ref.read(videoUploadNotifierProvider);

    if (!context.mounted) return;

    if (state.error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Upload failed: ${state.error}'),
          backgroundColor: Colors.red,
        ),
      );
    } else if (state.response != null && state.response!.success) {
      // Save to local database
      if (state.response!.id != null && state.response!.filename != null) {
        final record = VideoRecord(
          mongoId: state.response!.id!,
          name: _nameController.text.trim(),
          filename: state.response!.filename!,
          createdAt: DateTime.now(),
        );

        try {
          await DatabaseHelper().insertVideoRecord(record);
          print('✅ Video record saved to local database');
        } catch (e) {
          print('❌ Failed to save video record: $e');
        }
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Upload successful: ${state.response!.message}'),
          backgroundColor: Colors.green,
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
                        Text(
                          'File Path',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 8),
                        SelectableText(
                          widget.filePath,
                          style: Theme.of(context).textTheme.bodySmall,
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
                        if (uploadState.response != null && !uploadState.isUploading) ...[
                          Center(
                            child: Column(
                              children: [
                                Icon(
                                  uploadState.response!.success ? Icons.check_circle : Icons.error,
                                  color: uploadState.response!.success ? Colors.green : Colors.red,
                                  size: 48,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  uploadState.response!.message,
                                  textAlign: TextAlign.center,
                                ),
                                if (uploadState.response!.filename != null) ...[
                                  const SizedBox(height: 8),
                                  Text(
                                    'Filename: ${uploadState.response!.filename}',
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                ],
                                if (uploadState.response!.id != null) ...[
                                  const SizedBox(height: 4),
                                  Text(
                                    'ID: ${uploadState.response!.id}',
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ],
                        if (uploadState.error != null && !uploadState.isUploading) ...[
                          const Center(
                            child: Column(
                              children: [
                                Icon(
                                  Icons.error,
                                  color: Colors.red,
                                  size: 48,
                                ),
                                SizedBox(height: 8),
                              ],
                            ),
                          ),
                          Text(
                            'Error: ${uploadState.error}',
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: uploadState.isUploading
                        ? null
                        : () => _handleUpload(context),
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
