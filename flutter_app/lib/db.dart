import 'dart:async';
import 'package:mysql1/mysql1.dart' as mysql;

class DB {
  static const String schema = 'cadet_tracker';
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
  static Future<T> run<T>(Future<T> Function(mysql.MySqlConnection) action) {
    final completer = Completer<T>();
    // Chain onto the queue and always resolve to keep the chain alive even on errors
    _queue = _queue.then((_) async {
      // Small delay to reduce chances of back-to-back handshake interleaving on some servers
      await Future<void>.delayed(const Duration(milliseconds: 25));
      mysql.MySqlConnection? conn;
      try {
        conn = await _open();
        final res = await action(conn);
        if (!completer.isCompleted) completer.complete(res);
      } catch (e, st) {
        if (!completer.isCompleted) completer.completeError(e, st);
      } finally {
        try { await conn?.close(); } catch (_) {}
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
