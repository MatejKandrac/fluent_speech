// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'video_upload_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

VideoUploadResponse _$VideoUploadResponseFromJson(Map<String, dynamic> json) =>
    VideoUploadResponse(
      success: json['success'] as bool,
      message: json['message'] as String?,
      id: (json['recording_id'] as num?)?.toInt(),
      filename: json['filename'] as String?,
      fileSize: (json['fileSize'] as num?)?.toInt(),
      uploadedAt: json['uploadedAt'] as String?,
    );

Map<String, dynamic> _$VideoUploadResponseToJson(
  VideoUploadResponse instance,
) => <String, dynamic>{
  'success': instance.success,
  'message': instance.message,
  'recording_id': instance.id,
  'filename': instance.filename,
  'fileSize': instance.fileSize,
  'uploadedAt': instance.uploadedAt,
};
