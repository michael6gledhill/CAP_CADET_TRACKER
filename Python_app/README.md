CAP Cadet Tracker - Add Cadet GUI

This is a minimal Tkinter GUI to add cadets to the `cap_cadet_tracker_2.0` MySQL database.

Prerequisites
- Python 3.8+
- MySQL server running on localhost

Install dependencies

Open a command prompt in the project folder and run:

pip install -r requirements.txt

Usage

Edit `main.py` if you need to change database credentials. Then run:

python main.py

The GUI allows adding a cadet with CAP ID, name, email, phone, birthday, and picking a flight and line position from the drop-downs. Click "Refresh lookups" if the lists are empty or you've added flights/positions in the database manually.

Notes
- The app uses the MySQL user `Michael` and password `hogbog89` by default, against database `cap_cadet_tracker_2.0` on localhost.
- Ensure the database and lookup tables (`flight`, `line_position`) exist before using the GUI.
- This is a minimal example for local use; do not expose credentials in production.
