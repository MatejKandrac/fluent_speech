
abstract class CalibratorBase<T, D> {

  List<T> requiredLandmarks();
  List<T> getLandmarks(D data);

  List<T> getMissingLandmarks(D data) {
    final required = requiredLandmarks();
    final current = getLandmarks(data);

    final missing = <T>[];
    for (var element in required) {
      if(!current.contains(element)) missing.add(element);
    }

    return missing;
  }
}