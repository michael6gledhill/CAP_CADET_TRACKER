import 'package:flutter/material.dart';
import '../db.dart';
import '../utils/dialogs.dart';

class CadetsPage extends StatefulWidget {
  const CadetsPage({super.key});

  @override
  State<CadetsPage> createState() => _CadetsPageState();
}

class _CadetsPageState extends State<CadetsPage> {
  final _searchCtrl = TextEditingController();
  bool _loading = false;
  List<Map<String, dynamic>> _rows = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load([String? q]) async {
    setState(() => _loading = true);
    try {
      final rows = await DB.run((conn) async {
        if (q != null && q.isNotEmpty) {
          final like = '%$q%';
          final sql = DB.sql('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE CONCAT(first_name, " ", last_name) LIKE ? OR CAST(cap_id AS CHAR) LIKE ? ORDER BY last_name, first_name LIMIT 200', [like, like]);
          final res = await conn.query(sql);
          return res
              .map((r) => {
                    'cadet_id': r['cadet_id'],
                    'cap_id': r['cap_id'],
                    'first_name': r['first_name'],
                    'last_name': r['last_name'],
                    'dob': (r['date_of_birth'] is DateTime)
                        ? (r['date_of_birth'] as DateTime).toIso8601String().split('T').first
                        : (r['date_of_birth']?.toString() ?? ''),
                  })
              .toList();
        } else {
          final res = await conn.query('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet ORDER BY last_name, first_name LIMIT 200');
          return res
              .map((r) => {
                    'cadet_id': r['cadet_id'],
                    'cap_id': r['cap_id'],
                    'first_name': r['first_name'],
                    'last_name': r['last_name'],
                    'dob': (r['date_of_birth'] is DateTime)
                        ? (r['date_of_birth'] as DateTime).toIso8601String().split('T').first
                        : (r['date_of_birth']?.toString() ?? ''),
                  })
              .toList();
        }
      });
      _rows = rows;
    } catch (e, st) {
      if (mounted) {
        await showErrorDialog(context, 'Failed to load cadets', e, st);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchCtrl,
                  decoration: const InputDecoration(labelText: 'Search name or CAP ID'),
                  onSubmitted: (v) => _load(v.trim()),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton(
                onPressed: _loading ? null : () => _load(_searchCtrl.text.trim()),
                child: const Text('Search'),
              ),
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: _loading
                    ? null
                    : () {
                        _searchCtrl.clear();
                        _load();
                      },
                child: const Text('Clear'),
              ),
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: _loading
                    ? null
                    : () async {
                        try {
                          final ok = await DB.run((c) async {
                            final r = await c.query('SELECT 1 as ok');
                            return r.isNotEmpty ? r.first['ok'] : null;
                          });
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('DB OK (SELECT 1) => $ok')),
                            );
                          }
                        } catch (e, st) {
                          if (mounted) {
                            await showErrorDialog(context, 'DB connection failed', e, st);
                          }
                        }
                      },
                child: const Text('Test Connection'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : SingleChildScrollView(
                    child: DataTable(
                      columns: const [
                        DataColumn(label: Text('CAP ID')),
                        DataColumn(label: Text('First')),
                        DataColumn(label: Text('Last')),
                        DataColumn(label: Text('DOB')),
                      ],
                      rows: _rows
                          .map(
                            (r) => DataRow(cells: [
                              DataCell(Text(r['cap_id']?.toString() ?? '')),
                              DataCell(Text(r['first_name']?.toString() ?? '')),
                              DataCell(Text(r['last_name']?.toString() ?? '')),
                              DataCell(Text(r['dob']?.toString() ?? '')),
                            ]),
                          )
                          .toList(),
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }
}
