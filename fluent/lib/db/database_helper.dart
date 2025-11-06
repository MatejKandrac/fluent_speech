import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import 'models/video_record.dart';

class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  static Database? _database;

  factory DatabaseHelper() {
    return _instance;
  }

  DatabaseHelper._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, 'fluent.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE video_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mongo_id TEXT NOT NULL,
        name TEXT NOT NULL,
        filename TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    ''');
  }

  // Insert a video record
  Future<int> insertVideoRecord(VideoRecord record) async {
    final db = await database;
    return await db.insert(
      'video_records',
      record.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  // Get all video records
  Future<List<VideoRecord>> getAllVideoRecords() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'video_records',
      orderBy: 'created_at DESC',
    );

    return List.generate(maps.length, (i) {
      return VideoRecord.fromMap(maps[i]);
    });
  }

  // Get a single video record by SQLite id
  Future<VideoRecord?> getVideoRecord(int id) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'video_records',
      where: 'id = ?',
      whereArgs: [id],
    );

    if (maps.isEmpty) return null;
    return VideoRecord.fromMap(maps.first);
  }

  // Get a video record by MongoDB id
  Future<VideoRecord?> getVideoRecordByMongoId(String mongoId) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'video_records',
      where: 'mongo_id = ?',
      whereArgs: [mongoId],
    );

    if (maps.isEmpty) return null;
    return VideoRecord.fromMap(maps.first);
  }

  // Update a video record
  Future<int> updateVideoRecord(VideoRecord record) async {
    final db = await database;
    return await db.update(
      'video_records',
      record.toMap(),
      where: 'id = ?',
      whereArgs: [record.id],
    );
  }

  // Delete a video record
  Future<int> deleteVideoRecord(int id) async {
    final db = await database;
    return await db.delete(
      'video_records',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  // Delete a video record by MongoDB id
  Future<int> deleteVideoRecordByMongoId(String mongoId) async {
    final db = await database;
    return await db.delete(
      'video_records',
      where: 'mongo_id = ?',
      whereArgs: [mongoId],
    );
  }

  // Close the database
  Future<void> close() async {
    final db = await database;
    await db.close();
  }
}