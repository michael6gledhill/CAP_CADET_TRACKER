import 'package:flutter/material.dart';
import '../api.dart';
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
      List<Map<String, dynamic>> rows;
      if (q != null && q.isNotEmpty) {
        final r = await api.searchCadets(q);
        rows = r
            .map((r) => {
                  'cadet_id': r['cadet_id'] ?? r['id'],
                  'cap_id': r['cap_id'] ?? r['cap'],
                  'first_name': r['first_name'] ?? r['first'],
                  'last_name': r['last_name'] ?? r['last'],
                  'dob': (r['date_of_birth'] ?? r['dob'])?.toString() ?? ''
                })
            .toList();
      } else {
        final r = await api.listCadets();
        rows = r
            .map((r) => {
                  'cadet_id': r['cadet_id'] ?? r['id'],
                  'cap_id': r['cap_id'] ?? r['cap'],
                  'first_name': r['first_name'] ?? r['first'],
                  'last_name': r['last_name'] ?? r['last'],
                  'dob': (r['date_of_birth'] ?? r['dob'])?.toString() ?? ''
                })
            .toList();
      }
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
                          final ok = await api.testConnection();
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('API test => $ok')),
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
