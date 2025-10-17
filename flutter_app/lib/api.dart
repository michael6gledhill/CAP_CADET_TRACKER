import 'dart:convert';
import 'package:http/http.dart' as http;

class Api {
  final String baseUrl;
  Api({this.baseUrl = 'http://127.0.0.1:5057'});

  Uri _uri(String path, [Map<String, dynamic>? query]) => Uri.parse('$baseUrl$path').replace(queryParameters: query?.map((k, v) => MapEntry(k, v?.toString() ?? '')));

  Future<dynamic> _get(String path, [Map<String, dynamic>? query]) async {
    return await _request(() => http.get(_uri(path, query)), 'GET', path);
  }

  Future<dynamic> _post(String path, Map<String, dynamic> body) async {
    return await _request(() => http.post(Uri.parse('$baseUrl$path'), headers: {'Content-Type': 'application/json'}, body: jsonEncode(body)), 'POST', path);
  }

  Future<dynamic> _put(String path, Map<String, dynamic> body) async {
    return await _request(() => http.put(Uri.parse('$baseUrl$path'), headers: {'Content-Type': 'application/json'}, body: jsonEncode(body)), 'PUT', path);
  }

  Future<dynamic> _delete(String path, [Map<String, dynamic>? query]) async {
    final uri = _uri(path, query);
    return await _request(() => http.delete(uri), 'DELETE', path);
  }

  Future<dynamic> _request(Future<http.Response> Function() fn, String method, String path) async {
    const int maxAttempts = 4;
    int attempt = 0;
    while (true) {
      attempt++;
      try {
        final r = await fn();
        if (r.statusCode != 200) throw Exception('$method $path failed: ${r.statusCode} ${r.body}');
        return jsonDecode(r.body);
      } catch (e) {
        // If we've exhausted attempts, rethrow for UI to show
        if (attempt >= maxAttempts) rethrow;
        // Wait with exponential backoff before retrying
        final waitMs = 150 * (1 << (attempt - 1));
        await Future.delayed(Duration(milliseconds: waitMs));
      }
    }
  }

  // Ranks & Requirements
  Future<List<Map<String, dynamic>>> listRanks() async {
    final body = await _get('/api/ranks');
    return (body as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<List<Map<String, dynamic>>> listRequirementsForRank(int rankId) async {
    final body = await _get('/api/requirements', {'rank_id': rankId});
    return (body as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<int?> createRequirement(String name, String? desc, {int? linkRankId}) async {
    final body = <String, dynamic>{'requirement_name': name, 'description': desc};
    if (linkRankId != null) body['rank_id'] = linkRankId.toString();
    final r = await _post('/api/requirements', body);
    return (r as Map)['requirement_id'] as int?;
  }

  Future<void> unlinkRequirementFromRank(int rankId, int reqId) async {
    await _delete('/api/requirements/unlink', {'rank_id': rankId, 'req_id': reqId});
  }

  // Cadets
  Future<List<Map<String, dynamic>>> listCadets() async {
    final body = await _get('/api/cadets');
    return (body as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<List<Map<String, dynamic>>> searchCadets(String q) async {
    final body = await _get('/api/cadets/search', {'q': q});
    return (body as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<Map<String, dynamic>> getCadetProfile(int id) async {
    final body = await _get('/api/cadets/$id/profile');
    return Map<String, dynamic>.from(body as Map);
  }

  Future<Map<String, dynamic>?> findCadetByCapId(String capid) async {
    try {
      final body = await _get('/api/cadets/by-capid/$capid');
      return Map<String, dynamic>.from(body as Map);
    } catch (_) {
      return null;
    }
  }

  Future<List<int>> cadetRanks(int cadetId) async {
    final body = await _get('/api/cadets/$cadetId/ranks');
    return (body as List).map((e) => int.parse((e ?? '').toString())).toList();
  }

  Future<List<int>> cadetCompletedRequirements(int cadetId) async {
    final body = await _get('/api/cadets/$cadetId/requirements');
    return (body as List).map((e) => int.parse((e ?? '').toString())).toList();
  }

  Future<void> toggleRequirementForCadet(int cadetId, int reqId, bool completed) async {
    await _post('/api/cadets/$cadetId/requirements/$reqId', {'completed': completed});
  }

  // Inspections
  Future<List<Map<String, dynamic>>> listInspectionsForCadet(int cadetId) async {
    final body = await _get('/api/cadets/$cadetId/inspections');
    return (body as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<Map<String, dynamic>?> createInspection(Map<String, dynamic> payload) async {
    final r = await _post('/api/inspections', payload);
    return r as Map<String, dynamic>?;
  }

  Future<void> deleteInspection(int id) async {
    await _delete('/api/inspections/$id');
  }

  // Reports
  Future<List<Map<String, dynamic>>> listReports() async {
    final body = await _get('/api/reports');
    return (body as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<int?> createReport(Map<String, dynamic> payload) async {
    final r = await _post('/api/reports', payload);
    return (r as Map)['report_id'] as int?;
  }

  Future<void> deleteReport(int id) async {
    await _delete('/api/reports/$id');
  }

  // Positions
  Future<List<Map<String, dynamic>>> listPositions() async {
    final body = await _get('/api/positions');
    return (body as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<int?> createPosition(Map<String, dynamic> payload) async {
    final r = await _post('/api/positions', payload);
    return (r as Map)['position_id'] as int?;
  }

  Future<void> updatePosition(int id, Map<String, dynamic> payload) async {
    await _put('/api/positions/$id', payload);
  }

  Future<void> deletePosition(int id) async {
    await _delete('/api/positions/$id');
  }

  // Test
  Future<bool> testConnection() async {
    try {
      final body = await _get('/api/test');
      return (body is Map) && (body['ok'] == 1 || body['ok'] == true);
    } catch (_) {
      return false;
    }
  }
}

// default singleton
final api = Api();
