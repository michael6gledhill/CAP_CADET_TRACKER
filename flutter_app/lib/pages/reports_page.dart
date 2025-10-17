import 'package:flutter/material.dart';
import '../api.dart';

class ReportsPage extends StatefulWidget {
  const ReportsPage({super.key});

  @override
  State<ReportsPage> createState() => _ReportsPageState();
}

class _ReportsPageState extends State<ReportsPage> {
  bool _loading = false;
  List<Map<String, dynamic>> _rows = [];

  final _cadetCtrl = TextEditingController();
  final _typeCtrl = TextEditingController(text: 'Negative');
  final _dateCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _resolvedByCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final rows = await api.listReports();
      _rows = rows
          .map((r) => {
                'report_id': r['report_id'] ?? r['id'],
                'cadet_cadet_id': r['cadet_cadet_id'] ?? r['cadet_id'] ?? r['cadet'],
                'report_type': r['report_type'] ?? r['type'],
                'Incident_date': (r['Incident_date'] ?? r['date'])?.toString() ?? '',
                'resolved': (r['resolved'] == 1 || r['resolved'] == true) ? 'Yes' : 'No'
              })
          .toList();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to load reports: $e')));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    final idStr = _cadetCtrl.text.trim();
    if (idStr.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cadet ID required')));
      return;
    }
    final cadetId = int.tryParse(idStr);
    if (cadetId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cadet ID must be a number')));
      return;
    }
    try {
      final payload = {
        'cadet_cadet_id': cadetId,
        'report_type': _typeCtrl.text.trim(),
        'description': _descCtrl.text.trim(),
        'created_by': null,
        'Incident_date': _dateCtrl.text.trim().isEmpty ? null : _dateCtrl.text.trim(),
        'resolved': 0,
        'resolved_by': _resolvedByCtrl.text.trim().isEmpty ? null : _resolvedByCtrl.text.trim(),
      };
      await api.createReport(payload);
      _cadetCtrl.clear();
      _typeCtrl.text = 'Negative';
      _dateCtrl.clear();
      _descCtrl.clear();
      _resolvedByCtrl.clear();
      _load();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to save: $e')));
    }
  }

  Future<void> _delete(int reportId) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete report?'),
        content: Text('Delete report #$reportId?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Delete')),
        ],
      ),
    );
    if (ok != true) return;

    try {
      await api.deleteReport(reportId);
      _load();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to delete: $e')));
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
            runSpacing: 8,
            spacing: 8,
            children: [
              SizedBox(width: 120, child: TextField(controller: _cadetCtrl, decoration: const InputDecoration(labelText: 'Cadet ID'))),
              SizedBox(width: 180, child: TextField(controller: _typeCtrl, decoration: const InputDecoration(labelText: 'Type (Negative/Positive)'))),
              SizedBox(width: 180, child: TextField(controller: _dateCtrl, decoration: const InputDecoration(labelText: 'Incident Date YYYY-MM-DD'))),
              SizedBox(width: 300, child: TextField(controller: _descCtrl, decoration: const InputDecoration(labelText: 'Description'))),
              SizedBox(width: 160, child: TextField(controller: _resolvedByCtrl, decoration: const InputDecoration(labelText: 'Resolved By (CAPID)'))),
              FilledButton(onPressed: _loading ? null : _save, child: const Text('Save Report')),
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
                        DataColumn(label: Text('Cadet')),
                        DataColumn(label: Text('Type')),
                        DataColumn(label: Text('Date')),
                        DataColumn(label: Text('Resolved')),
                        DataColumn(label: Text('Actions')),
                      ],
                      rows: _rows
                          .map((r) => DataRow(cells: [
                                DataCell(Text(r['report_id'].toString())),
                                DataCell(Text(r['cadet_cadet_id'].toString())),
                                DataCell(Text(r['report_type'].toString())),
                                DataCell(Text(r['Incident_date'].toString())),
                                DataCell(Text(r['resolved'].toString())),
                                DataCell(Row(children: [
                                  OutlinedButton(
                                    onPressed: () => _delete(r['report_id'] as int),
                                    child: const Text('Delete'),
                                  )
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
    _cadetCtrl.dispose();
    _typeCtrl.dispose();
    _dateCtrl.dispose();
    _descCtrl.dispose();
    _resolvedByCtrl.dispose();
    super.dispose();
  }
}
