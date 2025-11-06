import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../clients/video_api_client.dart';
import '../models/video_upload_response.dart';
import '../providers/api_providers.dart';

class VideoUploadService {
  final VideoApiClient _apiClient;

  VideoUploadService(this._apiClient);

  Future<VideoUploadResponse> uploadVideo(String filePath) async {
    final file = File(filePath);

    if (!await file.exists()) {
      throw Exception('Video file not found at: $filePath');
    }

    final multipartFile = await MultipartFile.fromFile(
      filePath,
      filename: file.path.split('/').last,
    );

    return _apiClient.uploadVideo(video: multipartFile);
  }

  Future<void> deleteVideo(String filename) async {
    await _apiClient.deleteVideo(filename: filename);
  }
}

// Provider for VideoUploadService
final videoUploadServiceProvider = Provider<VideoUploadService>((ref) {
  final apiClient = ref.watch(videoApiClientProvider);
  return VideoUploadService(apiClient);
});

// StateNotifier for handling upload state
class VideoUploadState {
  final bool isUploading;
  final VideoUploadResponse? response;
  final String? error;
  final double? progress;

  VideoUploadState({
    this.isUploading = false,
    this.response,
    this.error,
    this.progress,
  });

  VideoUploadState copyWith({
    bool? isUploading,
    VideoUploadResponse? response,
    String? error,
    double? progress,
  }) => VideoUploadState(
      isUploading: isUploading ?? this.isUploading,
      response: response ?? this.response,
      error: error ?? this.error,
      progress: progress ?? this.progress,
    );
}

class VideoUploadNotifier extends StateNotifier<VideoUploadState> {
  final VideoUploadService _service;

  VideoUploadNotifier(this._service) : super(VideoUploadState());

  Future<void> uploadVideo(String filePath) async {
    state = VideoUploadState(isUploading: true, progress: 0);

    try {
      final response = await _service.uploadVideo(filePath);
      state = VideoUploadState(
        isUploading: false,
        response: response,
        progress: 1.0,
      );
    } catch (e) {
      state = VideoUploadState(
        isUploading: false,
        error: e.toString(),
      );
    }
  }

  void reset() {
    state = VideoUploadState();
  }
}

// Provider for VideoUploadNotifier
final videoUploadNotifierProvider =
    StateNotifierProvider<VideoUploadNotifier, VideoUploadState>((ref) {
  final service = ref.watch(videoUploadServiceProvider);
  return VideoUploadNotifier(service);
});