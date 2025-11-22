class VideoRecord {
  final int? id; // SQLite auto-increment id
  final int remoteId; // ID from MongoDB
  final String name; // User-defined name
  final String filename; // Filename from backend
  final DateTime createdAt;

  VideoRecord({
    this.id,
    required this.remoteId,
    required this.name,
    required this.filename,
    required this.createdAt,
  });

  // Convert to Map for SQLite insertion
  Map<String, dynamic> toMap() => {
      'id': id,
      'video_id': remoteId,
      'name': name,
      'filename': filename,
      'created_at': createdAt.toIso8601String(),
    };

  // Convert from Map for SQLite query
  factory VideoRecord.fromMap(Map<String, dynamic> map) => VideoRecord(
      id: map['id'] as int?,
      remoteId: map['video_id'] as int,
      name: map['name'] as String,
      filename: map['filename'] as String,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
}