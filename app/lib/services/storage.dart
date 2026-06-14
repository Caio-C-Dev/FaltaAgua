import 'package:shared_preferences/shared_preferences.dart';

class Storage {
  static const _kCity = 'city';
  static const _kNeighborhood = 'neighborhood';
  static const _kPrevTopicCity = 'prev_topic_city';

  static Future<String?> getPrevTopicCity() async {
    final p = await SharedPreferences.getInstance();
    return p.getString(_kPrevTopicCity);
  }

  static Future<void> savePrevTopicCity(String city) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kPrevTopicCity, city);
  }

  static Future<String?> getCity() async {
    final p = await SharedPreferences.getInstance();
    return p.getString(_kCity);
  }

  static Future<String?> getNeighborhood() async {
    final p = await SharedPreferences.getInstance();
    return p.getString(_kNeighborhood);
  }

  static Future<void> save(String city, String neighborhood) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kCity, city);
    await p.setString(_kNeighborhood, neighborhood);
  }
}
