import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mysql1/mysql1.dart' as mysql;

// Lightweight remote SQL executor used when REMOTE_MODE is true.
class RemoteConn {
  final String baseUrl;
  RemoteConn(this.baseUrl);

  /// Execute a SQL string (already interpolated) and return rows as List<Map>
  Future<List<Map<String, dynamic>>> query(String sql) async {
    final uri = Uri.parse('$baseUrl/api/sql');
    final r = await http.post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode({'sql': sql}));
    if (r.statusCode != 200) throw Exception('Remote SQL failed: ${r.statusCode} ${r.body}');
    final body = jsonDecode(r.body) as Map<String, dynamic>;
    final rows = (body['rows'] as List<dynamic>?) ?? [];
    // Normalize rows to List<Map<String,dynamic>>
    return rows.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<void> close() async {
    // nothing to close for HTTP
  }
}

class DB {
  static const String schema = 'cadet_tracker';
  // If true, use the local HTTP API at http://127.0.0.1:5057/api/sql
  // to execute SQL instead of direct MySQL connections. Set to true to
  // avoid mysql1 driver issues on some platforms. The Node API must be running.
  static const bool REMOTE_MODE = true;
  // Serialize DB operations to avoid concurrent packet interleaving
  static Future _queue = Future.value();

  static mysql.ConnectionSettings baseSettings() {
    return mysql.ConnectionSettings(
      host: 'localhost',
      user: 'root',
      password: 'h0gBog89!',
      port: 3306,
    );
  }

  // Build a text SQL by safely interpolating params, avoiding prepared statements.
  // This reduces chances of protocol/packet issues in some mysql1 environments.
  static String sql(String template, List<dynamic> params) {
    String esc(dynamic v) {
      if (v == null) return 'NULL';
      if (v is bool) return v ? '1' : '0';
      if (v is num) return v.toString();
      // Accept pre-formatted date strings as-is with quotes
      final s = v.toString().replaceAll('\\', r'\\').replaceAll("'", "''");
      return "'$s'";
    }

    final parts = template.split('?');
    if (parts.length == 1) return template; // no params
    final b = StringBuffer();
    final count = params.length;
    for (var i = 0; i < count; i++) {
      b.write(parts[i]);
      b.write(esc(params[i]));
    }
    // Append remainder (if mismatched counts, this still returns something sensible)
    if (parts.length > count) b.write(parts.sublist(count).join('?'));
    return b.toString();
  }

  // Run an action against MySQL serialized in a queue; uses a new connection per action.
  static Future<T> run<T>(Future<T> Function(dynamic /* mysql.MySqlConnection | RemoteConn */) action) {
    final completer = Completer<T>();
    // Chain onto the queue and always resolve to keep the chain alive even on errors
    _queue = _queue.then((_) async {
      // Small delay to reduce chances of back-to-back handshake interleaving on some servers
      await Future<void>.delayed(const Duration(milliseconds: 25));
      mysql.MySqlConnection? conn;
      RemoteConn? rconn;
      try {
        if (REMOTE_MODE) {
          rconn = RemoteConn('http://127.0.0.1:5057');
          final res = await action(rconn);
          if (!completer.isCompleted) completer.complete(res);
        } else {
          conn = await _open();
          final res = await action(conn);
          if (!completer.isCompleted) completer.complete(res);
        }
      } catch (e, st) {
        if (!completer.isCompleted) completer.completeError(e, st);
      } finally {
        try {
          await conn?.close();
        } catch (_) {}
        try {
          await rconn?.close();
        } catch (_) {}
      }
    }).catchError((_) {
      // Swallow to keep queue intact; individual futures already completed with error
    });
    return completer.future;
  }

  static Future<mysql.MySqlConnection> _open() async {
    // Simplest possible: direct connect, no retries, no handshake queries.
    return await mysql.MySqlConnection.connect(baseSettings());
  }
}
