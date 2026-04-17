import 'package:json_annotation/json_annotation.dart';

part 'processing_status_response.g.dart';

@JsonSerializable()
class ProcessingStatusResponse {
  final bool success;
  @JsonKey(name: 'recording_id')
  final int? recordingId;
  @JsonKey(name: 'video_processing_finished')
  final bool videoProcessingFinished;
  @JsonKey(name: 'audio_processing_finished')
  final bool audioProcessingFinished;
  @JsonKey(name: 'transcript_processing_finished')
  final bool transcriptProcessingFinished;

  ProcessingStatusResponse({
    required this.success,
    this.recordingId,
    required this.videoProcessingFinished,
    required this.audioProcessingFinished,
    required this.transcriptProcessingFinished,
  });

  bool get allFinished =>
      videoProcessingFinished &&
      audioProcessingFinished &&
      transcriptProcessingFinished;

  factory ProcessingStatusResponse.fromJson(Map<String, dynamic> json) =>
      _$ProcessingStatusResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ProcessingStatusResponseToJson(this);
}
