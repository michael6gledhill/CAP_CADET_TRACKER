# CAP Cadet Tracker — Flutter (Desktop)

A native desktop app for Windows/macOS built with Flutter (no web). It connects directly to your MySQL database.

## Prereqs
- Flutter SDK (3.2+ recommended)
- Windows 10/11 for Windows desktop, macOS 12+ for macOS desktop
- MySQL database with schema `cap_cadet_tracker_3.0`

## Init
```powershell
# From flutter_app folder
flutter pub get
```

## Run (Windows)
```powershell
flutter config --enable-windows-desktop
flutter run -d windows
```

## Run (macOS)
```bash
flutter config --enable-macos-desktop
flutter run -d macos
```

## Build
```powershell
flutter build windows
# or
flutter build macos
```

## Notes
- The app uses the `mysql1` package to connect directly to MySQL from Dart.
- Update DB settings in `lib/db.dart` to match your credentials.
- Initial screens included: Cadets, Reports, Positions.
