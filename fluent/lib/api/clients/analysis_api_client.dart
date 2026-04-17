import 'package:dio/dio.dart';

/// Direct Dio client for the analysis endpoint.
/// Uses a long receive timeout (10 min) because the analysis pipeline
/// calls 6 services in parallel and can take several minutes.
class AnalysisApiClient {
  final Dio _dio;

  AnalysisApiClient(this._dio);

  Future<Map<String, dynamic>> runAnalysis(int recordingId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/analysis/analyze',
      queryParameters: {'recording-id': recordingId},
      options: Options(
        receiveTimeout: const Duration(minutes: 10),
        sendTimeout: const Duration(seconds: 30),
      ),
    );
    return response.data ?? {};
  }
}
