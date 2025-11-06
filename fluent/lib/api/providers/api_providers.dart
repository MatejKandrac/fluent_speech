import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/environment.dart';
import '../clients/video_api_client.dart';

// Provider for Dio instance
final dioProvider = Provider<Dio>((ref) {
  print('🔧 Creating Dio with baseUrl: ${Environment.serverUrl}');

  final dio = Dio(BaseOptions(
    baseUrl: Environment.serverUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
    sendTimeout: const Duration(minutes: 5), // Longer timeout for video uploads
  ));

  // Add interceptors for logging (optional)
  dio.interceptors.add(LogInterceptor(
    requestBody: true,
    responseBody: true,
    error: true,
    requestHeader: true,
    logPrint: (obj) {
      print('🌐 DIO: $obj');
    },
  ));

  return dio;
});

// Provider for VideoApiClient
final videoApiClientProvider = Provider<VideoApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  print('🔧 Creating VideoApiClient with baseUrl: ${Environment.serverUrl}');
  return VideoApiClient(dio, baseUrl: Environment.serverUrl);
});