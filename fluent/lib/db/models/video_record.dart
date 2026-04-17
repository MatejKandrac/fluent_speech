class VideoRecord {
  final int? id;
  final int remoteId;
  final String name;
  final String filename;
  final String? localPath;
  final DateTime createdAt;

  VideoRecord({
    this.id,
    required this.remoteId,
    required this.name,
    required this.filename,
    this.localPath,
    required this.createdAt,
  });

  VideoRecord copyWith({
    int? id,
    int? remoteId,
    String? name,
    String? filename,
    String? localPath,
    DateTime? createdAt,
  }) => VideoRecord(
        id: id ?? this.id,
        remoteId: remoteId ?? this.remoteId,
        name: name ?? this.name,
        filename: filename ?? this.filename,
        localPath: localPath ?? this.localPath,
        createdAt: createdAt ?? this.createdAt,
      );

  Map<String, dynamic> toMap() => {
        'id': id,
        'video_id': remoteId,
        'name': name,
        'filename': filename,
        'local_path': localPath,
        'created_at': createdAt.toIso8601String(),
      };

  factory VideoRecord.fromMap(Map<String, dynamic> map) => VideoRecord(
        id: map['id'] as int?,
        remoteId: map['video_id'] as int,
        name: map['name'] as String,
        filename: map['filename'] as String,
        localPath: map['local_path'] as String?,
        createdAt: DateTime.parse(map['created_at'] as String),
      );
}
