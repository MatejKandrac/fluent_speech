class Environment {
  // Read SERVER_URL from dart-define, with fallback to localhost
  static const String serverUrl = String.fromEnvironment(
    'SERVER_URL',
    defaultValue: 'http://localhost:8080',
  );

  // Debug method to print the actual server URL
  static void printServerUrl() {
    print('🔧 Environment.serverUrl = $serverUrl');
  }
}