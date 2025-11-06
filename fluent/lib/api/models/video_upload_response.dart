import 'package:json_annotation/json_annotation.dart';

part 'video_upload_response.g.dart';

@JsonSerializable()
class VideoUploadResponse {
  final bool success;
  final String message;
  final String? id;
  final String? filename;
  final int? fileSize;
  final String? uploadedAt;

  VideoUploadResponse({
    required this.success,
    required this.message,
    this.id,
    this.filename,
    this.fileSize,
    this.uploadedAt,
  });

  factory VideoUploadResponse.fromJson(Map<String, dynamic> json) =>
      _$VideoUploadResponseFromJson(json);

  Map<String, dynamic> toJson() => _$VideoUploadResponseToJson(this);
}