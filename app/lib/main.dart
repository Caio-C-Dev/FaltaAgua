import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'screens/setup_screen.dart';
import 'screens/home_screen.dart';
import 'services/storage.dart';
import 'services/notification_service.dart';

@pragma('vm:entry-point')
Future<void> _bgHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  FirebaseMessaging.onBackgroundMessage(_bgHandler);
  await NotificationService.init();
  runApp(const FaltaAguaApp());
}

class FaltaAguaApp extends StatelessWidget {
  const FaltaAguaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Alerta Falta de Água BH',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const RootGate(),
    );
  }
}

class RootGate extends StatefulWidget {
  const RootGate({super.key});
  @override
  State<RootGate> createState() => _RootGateState();
}

class _RootGateState extends State<RootGate> {
  bool? _hasSetup;

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final city = await Storage.getCity();
    setState(() => _hasSetup = city != null);
  }

  @override
  Widget build(BuildContext context) {
    if (_hasSetup == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _hasSetup! ? const HomeScreen() : const SetupScreen();
  }
}
