import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

Future<void> showErrorDialog(BuildContext context, String title, Object error, [StackTrace? stack]) async {
  final buf = StringBuffer()
    ..writeln(error.toString());
  if (stack != null) {
    buf
      ..writeln('\nStack trace:')
      ..writeln(stack.toString());
  }
  final text = buf.toString();
  await showDialog(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(title),
      content: SizedBox(
        width: 640,
        child: SingleChildScrollView(
          child: SelectableText(text),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () async {
            await Clipboard.setData(ClipboardData(text: text));
            if (ctx.mounted) {
              ScaffoldMessenger.of(ctx).showSnackBar(const SnackBar(content: Text('Error copied to clipboard')));
            }
          },
          child: const Text('Copy'),
        ),
        TextButton(
          onPressed: () => Navigator.of(ctx).pop(),
          child: const Text('Close'),
        ),
      ],
    ),
  );
}
