import 'package:flutter/material.dart';

import '../services/storage.dart';
import '../services/notification_service.dart';
import 'history_screen.dart';
import 'setup_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String? _city;
  String? _neighborhood;

  @override
  void initState() {
    super.initState();
    _load();
    WidgetsBinding.instance.addPostFrameCallback((_) => _askBatteryExemption());
  }

  Future<void> _askBatteryExemption() async {
    if (!mounted) return;
    final accepted = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Notificações sempre ativas'),
        content: const Text(
          'Para receber alertas mesmo sem abrir o app, desative a otimização '
          'de bateria para este app. Sem isso, o Android pode bloquear '
          'notificações após dias parado.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Agora não'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Permitir'),
          ),
        ],
      ),
    );
    if (accepted == true) {
      await NotificationService.requestBatteryExemption();
    }
  }

  Future<void> _load() async {
    final c = await Storage.getCity();
    final n = await Storage.getNeighborhood();
    setState(() {
      _city = c;
      _neighborhood = n;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alerta Falta de Água'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const SetupScreen()),
            ),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.water_drop, size: 80, color: Colors.blue),
            const SizedBox(height: 16),
            Text('Monitorando',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text('${_neighborhood ?? "..."} - ${_city ?? "..."}',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center),
            const SizedBox(height: 32),
            const Text(
              'Agora é só aguardar. Quando houver falta de água na sua região, nós te notificaremos.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 15),
            ),
            const SizedBox(height: 32),
            if (_city != null)
              OutlinedButton.icon(
                icon: const Icon(Icons.history),
                label: const Text('Ver histórico'),
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => HistoryScreen(city: _city!),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
