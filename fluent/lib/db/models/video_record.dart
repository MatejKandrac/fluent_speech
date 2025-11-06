class VideoRecord {
  final String? id; // SQLite auto-increment id
  final String mongoId; // ID from MongoDB
  final String name; // User-defined name
  final String filename; // Filename from backend
  final DateTime createdAt;

  VideoRecord({
    this.id,
    required this.mongoId,
    required this.name,
    required this.filename,
    required this.createdAt,
  });

  // Convert to Map for SQLite insertion
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'mongo_id': mongoId,
      'name': name,
      'filename': filename,
      'created_at': createdAt.toIso8601String(),
    };
  }

  // Convert from Map for SQLite query
  factory VideoRecord.fromMap(Map<String, dynamic> map) {
    return VideoRecord(
      id: map['id']?.toString(),
      mongoId: map['mongo_id'] as String,
      name: map['name'] as String,
      filename: map['filename'] as String,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }
}