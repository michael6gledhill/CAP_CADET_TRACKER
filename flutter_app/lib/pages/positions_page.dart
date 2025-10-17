import 'package:flutter/material.dart';
import '../api.dart';
import '../utils/dialogs.dart';

class PositionsPage extends StatefulWidget {
  const PositionsPage({super.key});

  @override
  State<PositionsPage> createState() => _PositionsPageState();
}

class _PositionsPageState extends State<PositionsPage> {
  bool _loading = false;
  List<Map<String, dynamic>> _rows = [];

  final _nameCtrl = TextEditingController();
  final _typeCtrl = TextEditingController(text: '0');
  final _levelCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final rows = await api.listPositions();
      _rows = rows
          .map((r) => {
                'position_id': r['position_id'] ?? r['id'],
                'position_name': r['position_name'] ?? r['name'],
                'line': r['line'],
                'level': r['level']?.toString() ?? ''
              })
          .toList();
    } catch (e, st) {
      if (mounted) {
        await showErrorDialog(context, 'Failed to load positions', e, st);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _add() async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Position name required')));
      return;
    }
    final line = int.tryParse(_typeCtrl.text.trim()) ?? 0;
    final level = _levelCtrl.text.trim().isEmpty ? null : _levelCtrl.text.trim();
    try {
      await api.createPosition({'position_name': name, 'line': line, 'level': level});
      _nameCtrl.clear();
      _typeCtrl.text = '0';
      _levelCtrl.clear();
      _load();
    } catch (e, st) {
      await showErrorDialog(context, 'Failed to add position', e, st);
    }
  }

  Future<void> _edit(Map<String, dynamic> row) async {
    final id = row['position_id'] as int;
    final name = _nameCtrl.text.trim().isEmpty ? row['position_name'] : _nameCtrl.text.trim();
    final line = int.tryParse(_typeCtrl.text.trim()) ?? (row['line'] ?? 0);
    final level = _levelCtrl.text.trim().isEmpty ? row['level'] : _levelCtrl.text.trim();
    try {
      await api.updatePosition(id, {'position_name': name, 'line': line, 'level': level});
      _load();
    } catch (e, st) {
      await showErrorDialog(context, 'Failed to update position', e, st);
    }
  }

  Future<void> _delete(int id) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete position?'),
        content: Text('Delete position #$id? This will also unlink cadets from this position.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Delete')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      // server-side deletePosition will unlink cadets and delete the position
      await api.deletePosition(id);
      _load();
    } catch (e, st) {
      await showErrorDialog(context, 'Failed to delete position', e, st);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              SizedBox(width: 280, child: TextField(controller: _nameCtrl, decoration: const InputDecoration(labelText: 'Position name'))),
              SizedBox(width: 160, child: TextField(controller: _typeCtrl, decoration: const InputDecoration(labelText: 'Type (1=Line/Staff, 0=Support)'))),
              SizedBox(width: 160, child: TextField(controller: _levelCtrl, decoration: const InputDecoration(labelText: 'Level (optional)'))),
              FilledButton(onPressed: _loading ? null : _add, child: const Text('Add Position')),
              OutlinedButton(onPressed: _loading ? null : _load, child: const Text('Refresh')),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : SingleChildScrollView(
                    child: DataTable(
                      columns: const [
                        DataColumn(label: Text('ID')),
                        DataColumn(label: Text('Name')),
                        DataColumn(label: Text('Type')),
                        DataColumn(label: Text('Level')),
                        DataColumn(label: Text('Actions')),
                      ],
                      rows: _rows
                          .map((r) => DataRow(cells: [
                                DataCell(Text(r['position_id'].toString())),
                                DataCell(Text(r['position_name'].toString())),
                                DataCell(Text((r['line'] == 1) ? 'Line/Staff' : 'Support')),
                                DataCell(Text(r['level'].toString())),
                                DataCell(Row(children: [
                                  OutlinedButton(onPressed: () => _edit(r), child: const Text('Edit')),
                                  const SizedBox(width: 8),
                                  OutlinedButton(onPressed: () => _delete(r['position_id'] as int), child: const Text('Delete')),
                                ])),
                              ]))
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
    _nameCtrl.dispose();
    _typeCtrl.dispose();
    _levelCtrl.dispose();
    super.dispose();
  }
}
