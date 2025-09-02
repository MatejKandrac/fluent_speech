import 'package:flutter/material.dart';
import 'config/theme.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final brightness = View.of(context).platformDispatcher.platformBrightness;

    MaterialTheme theme = MaterialTheme();

    return MaterialApp(
      title: 'Fluent',
      theme: brightness == Brightness.light ? theme.light() : theme.dark(),
      home: Scaffold(
        appBar: AppBar(
          title: Text("test")
        )
      ),
    );
  }
}
