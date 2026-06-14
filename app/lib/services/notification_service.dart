import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:url_launcher/url_launcher.dart';

import 'storage.dart';
import '../utils/slug.dart';

class NotificationService {
  static final _local = FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    await _local.initialize(
      const InitializationSettings(android: androidInit),
      onDidReceiveNotificationResponse: _onLocalNotifTap,
    );

    const channel = AndroidNotificationChannel(
      'falta_agua_channel',
      'Alertas Falta de Água',
      description: 'Notificações de falta de água na sua região',
      importance: Importance.max,
      enableVibration: true,
      playSound: true,
    );
    await _local
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);

    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission(alert: true, badge: true, sound: true);

    FirebaseMessaging.instance.onTokenRefresh.listen(_onTokenRefresh);
    FirebaseMessaging.onMessage.listen(_onForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_onMessageOpenedApp);

    final initial = await FirebaseMessaging.instance.getInitialMessage();
    if (initial != null) _onMessageOpenedApp(initial);
  }

  static void _onMessageOpenedApp(RemoteMessage m) {
    final link = m.data['link'];
    if (link is String && link.isNotEmpty) {
      launchUrl(Uri.parse(link), mode: LaunchMode.externalApplication);
    }
  }

  static void _onLocalNotifTap(NotificationResponse resp) {
    final payload = resp.payload;
    if (payload != null && payload.isNotEmpty) {
      launchUrl(Uri.parse(payload), mode: LaunchMode.externalApplication);
    }
  }

  static Future<void> requestBatteryExemption() async {
    final status = await Permission.ignoreBatteryOptimizations.status;
    if (!status.isGranted) {
      await Permission.ignoreBatteryOptimizations.request();
    }
  }

  static Future<void> _onTokenRefresh(String token) async {
    final city = await Storage.getCity();
    final nb = await Storage.getNeighborhood();
    if (city != null && nb != null) {
      await registerUser(city, nb);
    }
  }

  static Future<void> _onForegroundMessage(RemoteMessage m) async {
    final notif = m.notification;
    if (notif == null) return;
    await _local.show(
      notif.hashCode,
      notif.title,
      notif.body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'falta_agua_channel',
          'Alertas Falta de Água',
          importance: Importance.max,
          priority: Priority.high,
        ),
      ),
      payload: m.data['link'] as String?,
    );
  }

  static Future<void> registerUser(String city, String neighborhood) async {
    final messaging = FirebaseMessaging.instance;
    final token = await messaging.getToken();

    final prevCity = await Storage.getPrevTopicCity();
    if (prevCity != null && prevCity != city) {
      await messaging.unsubscribeFromTopic(cityTopic(prevCity));
    }
    await messaging.subscribeToTopic(cityTopic(city));
    await Storage.savePrevTopicCity(city);

    if (token != null) {
      await FirebaseFirestore.instance.collection('users').doc(token).set({
        'city': city.toLowerCase(),
        'neighborhood': neighborhood.toLowerCase(),
        'city_slug': slugify(city),
        'fcm_token': token,
        'updated_at': FieldValue.serverTimestamp(),
      });
    }
  }
}
