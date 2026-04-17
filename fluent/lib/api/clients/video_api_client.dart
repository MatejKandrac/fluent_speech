import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/video_upload_response.dart';
import '../models/processing_status_response.dart';

part 'video_api_client.g.dart';

@RestApi()
abstract class VideoApiClient {
  factory VideoApiClient(Dio dio, {String baseUrl}) = _VideoApiClient;

  @POST('/api/v1/processing/upload')
  @MultiPart()
  Future<VideoUploadResponse> uploadVideo({
    @Part(name: 'video') required MultipartFile video,
  });

  @GET('/api/v1/processing/status/{recording-id}')
  Future<ProcessingStatusResponse> getProcessingStatus({
    @Path('recording-id') required int recordingId,
  });
}
