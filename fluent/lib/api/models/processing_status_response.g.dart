// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'processing_status_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProcessingStatusResponse _$ProcessingStatusResponseFromJson(
  Map<String, dynamic> json,
) => ProcessingStatusResponse(
  success: json['success'] as bool,
  recordingId: (json['recording_id'] as num?)?.toInt(),
  videoProcessingFinished: json['video_processing_finished'] as bool,
  audioProcessingFinished: json['audio_processing_finished'] as bool,
  transcriptProcessingFinished: json['transcript_processing_finished'] as bool,
);

Map<String, dynamic> _$ProcessingStatusResponseToJson(
  ProcessingStatusResponse instance,
) => <String, dynamic>{
  'success': instance.success,
  'recording_id': instance.recordingId,
  'video_processing_finished': instance.videoProcessingFinished,
  'audio_processing_finished': instance.audioProcessingFinished,
  'transcript_processing_finished': instance.transcriptProcessingFinished,
};
