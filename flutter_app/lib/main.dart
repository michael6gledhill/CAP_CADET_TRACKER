import 'package:flutter/material.dart';
import 'pages/cadets_page.dart';
import 'pages/reports_page.dart';
import 'pages/positions_page.dart';
import 'pages/requirements_page.dart';

void main() {
  runApp(const CadetTrackerApp());
}

class CadetTrackerApp extends StatefulWidget {
  const CadetTrackerApp({super.key});

  @override
  State<CadetTrackerApp> createState() => _CadetTrackerAppState();
}

class _CadetTrackerAppState extends State<CadetTrackerApp> {
  ThemeMode _mode = ThemeMode.light;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CAP Cadet Tracker',
      theme: ThemeData(colorSchemeSeed: const Color(0xFF2563EB), brightness: Brightness.light),
      darkTheme: ThemeData(colorSchemeSeed: const Color(0xFF3B82F6), brightness: Brightness.dark),
      themeMode: _mode,
      home: MainHome(onToggleTheme: () {
        setState(() {
          _mode = _mode == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
        });
      }),
    );
  }
}

class MainHome extends StatefulWidget {
  final VoidCallback onToggleTheme;
  const MainHome({super.key, required this.onToggleTheme});

  @override
  State<MainHome> createState() => _MainHomeState();
}

class _MainHomeState extends State<MainHome> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      const CadetsPage(),
      const ReportsPage(),
      const PositionsPage(),
      const RequirementsPage(),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('CAP Cadet Tracker'),
        actions: [
          IconButton(onPressed: widget.onToggleTheme, icon: const Icon(Icons.brightness_6)),
        ],
      ),
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _index,
            onDestinationSelected: (i) => setState(() => _index = i),
            labelType: NavigationRailLabelType.all,
            destinations: const [
              NavigationRailDestination(icon: Icon(Icons.people), label: Text('Cadets')),
              NavigationRailDestination(icon: Icon(Icons.report), label: Text('Reports')),
              NavigationRailDestination(icon: Icon(Icons.work), label: Text('Positions')),
              NavigationRailDestination(icon: Icon(Icons.checklist), label: Text('Requirements')),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(child: pages[_index]),
        ],
      ),
    );
  }
}
