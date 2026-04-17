import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import 'models/video_record.dart';

class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  static Database? _database;

  factory DatabaseHelper() => _instance;

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
      version: 2,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE video_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        filename TEXT NOT NULL,
        local_path TEXT,
        created_at TEXT NOT NULL
      )
    ''');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      await db.execute('ALTER TABLE video_records ADD COLUMN local_path TEXT');
    }
  }

  Future<int> insertVideoRecord(VideoRecord record) async {
    final db = await database;
    return db.insert(
      'video_records',
      record.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<VideoRecord>> getAllVideoRecords() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'video_records',
      orderBy: 'created_at DESC',
    );
    return maps.map(VideoRecord.fromMap).toList();
  }

  Future<VideoRecord?> getVideoRecord(int id) async {
    final db = await database;
    final maps = await db.query(
      'video_records',
      where: 'id = ?',
      whereArgs: [id],
    );
    if (maps.isEmpty) return null;
    return VideoRecord.fromMap(maps.first);
  }

  Future<VideoRecord?> getVideoRecordByServerId(int serverId) async {
    final db = await database;
    final maps = await db.query(
      'video_records',
      where: 'video_id = ?',
      whereArgs: [serverId],
    );
    if (maps.isEmpty) return null;
    return VideoRecord.fromMap(maps.first);
  }

  Future<int> updateVideoRecord(VideoRecord record) async {
    final db = await database;
    return await db.update(
      'video_records',
      record.toMap(),
      where: 'id = ?',
      whereArgs: [record.id],
    );
  }

  Future<int> deleteVideoRecord(int id) async {
    final db = await database;
    return await db.delete(
      'video_records',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> close() async {
    final db = await database;
    await db.close();
  }
}
