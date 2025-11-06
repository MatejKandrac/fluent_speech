import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../database_helper.dart';

// Provider for DatabaseHelper
final databaseHelperProvider = Provider<DatabaseHelper>((ref) {
  return DatabaseHelper();
});