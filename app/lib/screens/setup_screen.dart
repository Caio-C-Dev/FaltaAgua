import 'package:flutter/material.dart';

import '../data/cities.dart';
import '../services/storage.dart';
import '../services/notification_service.dart';
import 'home_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});
  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  String? _city;
  final _neighborhood = TextEditingController();
  bool _saving = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cadastro')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Receba alertas de falta de água na sua região.'),
            const SizedBox(height: 24),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(labelText: 'Cidade'),
              value: _city,
              items: grandeBHCities
                  .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                  .toList(),
              onChanged: (v) => setState(() => _city = v),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _neighborhood,
              decoration: const InputDecoration(
                labelText: 'Bairro',
                hintText: 'Ex: Savassi',
              ),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const CircularProgressIndicator()
                  : const Text('Salvar'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (_city == null || _neighborhood.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Preencha cidade e bairro')),
      );
      return;
    }
    setState(() => _saving = true);
    await Storage.save(_city!, _neighborhood.text.trim());
    await NotificationService.registerUser(_city!, _neighborhood.text.trim());
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }
}
