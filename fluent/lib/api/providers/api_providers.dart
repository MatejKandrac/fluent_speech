import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/environment.dart';
import '../clients/video_api_client.dart';
import '../clients/analysis_api_client.dart';

// Provider for Dio instance
final dioProvider = Provider<Dio>((ref) {
  print('🔧 Creating Dio with baseUrl: ${Environment.serverUrl}');

  final dio = Dio(BaseOptions(
    baseUrl: Environment.serverUrl,
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
    sendTimeout: const Duration(minutes: 5),
  ));

  dio.interceptors.add(LogInterceptor(
    requestBody: false,
    responseBody: false,
    error: true,
    requestHeader: false,
    logPrint: (obj) => print('🌐 DIO: $obj'),
  ));

  return dio;
});

// Provider for VideoApiClient
final videoApiClientProvider = Provider<VideoApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return VideoApiClient(dio, baseUrl: Environment.serverUrl);
});

// Provider for AnalysisApiClient
final analysisApiClientProvider = Provider<AnalysisApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return AnalysisApiClient(dio);
});
