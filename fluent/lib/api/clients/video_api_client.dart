import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/video_upload_response.dart';

part 'video_api_client.g.dart';

@RestApi()
abstract class VideoApiClient {
  factory VideoApiClient(Dio dio, {String baseUrl}) = _VideoApiClient;

  @POST('/api/v1/videos/upload')
  @MultiPart()
  Future<VideoUploadResponse> uploadVideo({
    @Part(name: 'video') required MultipartFile video,
  });

  @DELETE('/api/v1/videos/{filename}')
  Future<void> deleteVideo({
    @Path('filename') required String filename,
  });
}