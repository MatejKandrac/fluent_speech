import 'package:flutter/cupertino.dart';

final class Log {

  static void i(String tag, String message) {
    debugPrint('${tag.toUpperCase()}: $message');
  }

  static void e(String tag, String message, [Error? exception]) {
    debugPrint('${tag.toUpperCase()}: $message');
    if (exception == null) return;
    debugPrintStack(stackTrace: exception.stackTrace);
  }

}
