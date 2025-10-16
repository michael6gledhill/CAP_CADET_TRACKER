import 'package:flutter/material.dart';
import '../db.dart';
import '../utils/dialogs.dart';

class RequirementsPage extends StatefulWidget {
  const RequirementsPage({super.key});

  @override
  State<RequirementsPage> createState() => _RequirementsPageState();
}

class _RequirementsPageState extends State<RequirementsPage> {
  bool _loading = false;
  List<Map<String, dynamic>> _ranks = [];
  int? _selectedRankId;
  List<Map<String, dynamic>> _requirements = [];

  final _reqNameCtrl = TextEditingController();
  final _reqDescCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadRanks();
  }

  Future<void> _loadRanks() async {
    setState(() => _loading = true);
    try {
      final ranks = await DB.run((c) async {
        final res = await c.query('SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC');
        return res.map((r) => {'id': r['rank_id'] as int, 'name': r['rank_name'] as String}).toList();
      });
      _ranks = ranks;
      if (_ranks.isNotEmpty) {
        _selectedRankId = _ranks.first['id'] as int;
        await _loadRequirements();
      }
    } catch (e, st) {
      if (mounted) await showErrorDialog(context, 'Failed to load ranks', e, st);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadRequirements() async {
    if (_selectedRankId == null) return;
    setState(() => _loading = true);
    try {
      final reqs = await DB.run((c) async {
        final res = await c.query(DB.sql('''
          SELECT r.requirement_id, r.requirement_name, r.description
          FROM rank_has_requirement rr
          JOIN requirement r ON rr.rank_requirement_requirement_id = r.requirement_id
          WHERE rr.rank_rank_id = ?
          ORDER BY r.requirement_id
        ''', [_selectedRankId]));
        return res
            .map((r) => {
                  'id': r['requirement_id'] as int,
                  'name': r['requirement_name']?.toString() ?? '',
                  'desc': r['description']?.toString() ?? '',
                })
            .toList();
      });
      _requirements = reqs;
    } catch (e, st) {
      if (mounted) await showErrorDialog(context, 'Failed to load requirements', e, st);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _createAndLink() async {
    final name = _reqNameCtrl.text.trim();
    final desc = _reqDescCtrl.text.trim();
    if (name.isEmpty || _selectedRankId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Requirement name and rank required')));
      return;
    }
    try {
      await DB.run((c) async {
        final ins = await c.query(DB.sql('INSERT INTO requirement (requirement_name, description) VALUES (?, ?)', [name, desc]));
        final reqId = ins.insertId;
        await Future<void>.delayed(const Duration(milliseconds: 10));
        await c.query(DB.sql('INSERT INTO rank_has_requirement (rank_rank_id, rank_requirement_requirement_id) VALUES (?, ?)', [_selectedRankId, reqId]));
        return 0; // satisfy generic type
      });
      _reqNameCtrl.clear();
      _reqDescCtrl.clear();
      _loadRequirements();
    } catch (e, st) {
      await showErrorDialog(context, 'Failed to create/link', e, st);
    }
  }

  Future<void> _unlink(int reqId) async {
    if (_selectedRankId == null) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Unlink requirement?'),
        content: Text('Unlink requirement #$reqId from this rank?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Unlink')),
        ],
      ),
    );
    if (ok != true) return;
    try {
  await DB.run((c) => c.query(DB.sql('DELETE FROM rank_has_requirement WHERE rank_rank_id=? AND rank_requirement_requirement_id=?', [_selectedRankId, reqId])));
      _loadRequirements();
    } catch (e, st) {
      await showErrorDialog(context, 'Failed to unlink', e, st);
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
              const Text('Rank:'),
              const SizedBox(width: 8),
              DropdownButton<int>(
                value: _selectedRankId,
                items: _ranks
                    .map((r) => DropdownMenuItem<int>(value: r['id'] as int, child: Text(r['name'] as String)))
                    .toList(),
                onChanged: (v) {
                  setState(() => _selectedRankId = v);
                  _loadRequirements();
                },
              ),
              const Spacer(),
              FilledButton(onPressed: _loading ? null : _loadRequirements, child: const Text('Refresh')),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              SizedBox(width: 260, child: TextField(controller: _reqNameCtrl, decoration: const InputDecoration(labelText: 'Requirement name'))),
              SizedBox(width: 440, child: TextField(controller: _reqDescCtrl, decoration: const InputDecoration(labelText: 'Description'))),
              FilledButton(onPressed: _loading ? null : _createAndLink, child: const Text('Create & Link')),
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
                        DataColumn(label: Text('Requirement')),
                        DataColumn(label: Text('Description')),
                        DataColumn(label: Text('Actions')),
                      ],
                      rows: _requirements
                          .map((r) => DataRow(cells: [
                                DataCell(Text(r['id'].toString())),
                                DataCell(Text(r['name'].toString())),
                                DataCell(Text(r['desc'].toString())),
                                DataCell(OutlinedButton(onPressed: () => _unlink(r['id'] as int), child: const Text('Unlink'))),
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
    _reqNameCtrl.dispose();
    _reqDescCtrl.dispose();
    super.dispose();
  }
}
