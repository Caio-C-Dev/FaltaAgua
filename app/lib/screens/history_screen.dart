import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../utils/slug.dart';

class HistoryScreen extends StatelessWidget {
  final String city;
  const HistoryScreen({super.key, required this.city});

  @override
  Widget build(BuildContext context) {
    final slug = slugify(city);
    final stream = FirebaseFirestore.instance
        .collection('sent_alerts')
        .where('cidades_slug', arrayContains: slug)
        .orderBy('created_at', descending: true)
        .limit(50)
        .snapshots();

    return Scaffold(
      appBar: AppBar(title: Text('Histórico - $city')),
      body: StreamBuilder<QuerySnapshot>(
        stream: stream,
        builder: (ctx, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Erro: ${snap.error}'));
          }
          final docs = snap.data?.docs ?? [];
          if (docs.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'Nenhum alerta registrado ainda.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          return ListView.separated(
            itemCount: docs.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (_, i) {
              final d = docs[i].data() as Map<String, dynamic>;
              final tipo = d['tipo'] ?? '';
              final titulo = d['titulo'] ?? '';
              final link = d['link'] ?? '';
              final ts = d['created_at'] as Timestamp?;
              final when = ts != null
                  ? DateFormat('dd/MM/yyyy HH:mm').format(ts.toDate())
                  : '';
              final isAlerta = tipo == 'ALERTA';
              return ListTile(
                leading: Icon(
                  isAlerta ? Icons.warning_amber : Icons.check_circle,
                  color: isAlerta ? Colors.red : Colors.green,
                ),
                title: Text(titulo, maxLines: 2, overflow: TextOverflow.ellipsis),
                subtitle: Text(when),
                onTap: link.isNotEmpty
                    ? () => launchUrl(Uri.parse(link),
                        mode: LaunchMode.externalApplication)
                    : null,
              );
            },
          );
        },
      ),
    );
  }
}
