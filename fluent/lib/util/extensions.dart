extension IntToTime on int {
  String getFormattedTime() {
    var minutes = this ~/ 60;
    var seconds = this % 60;
    return "${minutes < 10 ? "0" : ""}$minutes:${seconds < 10 ? "0" : ""}$seconds";
  }
}
