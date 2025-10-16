import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import tkinter.font as tkfont
import mysql.connector
from mysql.connector import Error, IntegrityError
import datetime
import re
import logging
import traceback
import sys
try:
    # Windows 11-like theme helpers (safe no-op if not present)
    from ui_theme import apply_accent, setup as theme_setup
except Exception:
    def apply_accent(_btn):
        return
    def theme_setup(_root, dark=False):
        return

# Database configuration - using credentials you provided
DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cap_cadet_tracker_3.0',
}


# configure basic logging to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# ensure uncaught exceptions are printed to the terminal with tracebacks
def _excepthook(exc_type, exc_value, exc_tb):
    logging.error('Uncaught exception', exc_info=(exc_type, exc_value, exc_tb))
    # also print to stderr for visibility
    traceback.print_exception(exc_type, exc_value, exc_tb)

sys.excepthook = _excepthook


def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        # show GUI error and also log full traceback to terminal
        messagebox.showerror("Database Error", f"Could not connect to database:\n{e}")
        logging.exception('Could not connect to database')
        return None


def fetch_flights():
    # flights are not used in the new schema; keep for backward compatibility but return empty
    return []


def fetch_positions():
    """Return list of (position_id, position_name) from `position` table."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        # try to include the 'line' column if present to allow categorization
        try:
            cur.execute("SELECT position_id, position_name, line, level FROM `position` ORDER BY position_id")
            rows = cur.fetchall()
            # return tuples (id, name, line)
            return rows
        except Exception:
            # fallback to older schema without 'line' flag
            cur.execute("SELECT position_id, position_name, level FROM `position` ORDER BY position_id")
            rows = cur.fetchall()
            # normalize to (id, name, None)
            return [(r[0], r[1], None) for r in rows]
    except Error as e:
        messagebox.showerror("Database Error", f"Error fetching positions:\n{e}")
        logging.exception('Error fetching positions')
        return []
    finally:
        conn.close()


def fetch_ranks():
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC")
        rows = cur.fetchall()
        return rows
    except Error as e:
        messagebox.showerror("Database Error", f"Error fetching ranks:\n{e}")
        logging.exception('Error fetching ranks')
        return []
    finally:
        conn.close()


def fetch_cadet_ranks(cadet_id: int):
    """Return a list of rank ids attached to a cadet from `rank_has_cadet`."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT rank_rank_id FROM rank_has_cadet WHERE cadet_cadet_id = %s", (cadet_id,))
        rows = cur.fetchall()
        return [r[0] for r in rows]
    except Error:
        logging.exception('Error fetching cadet ranks')
        return []
    finally:
        conn.close()


def fetch_cadet_positions(cadet_id: int):
    """Return a list of position ids attached to a cadet from `position_has_cadet`.
    Most recent entries will be first if `start_date` is available.
    """
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT position_position_id FROM position_has_cadet WHERE cadet_cadet_id = %s ORDER BY start_date DESC", (cadet_id,))
        rows = cur.fetchall()
        return [r[0] for r in rows]
    except Error:
        logging.exception('Error fetching cadet positions')
        return []
    finally:
        conn.close()


def fetch_cadet_by_capid(capid: int):
    """Return a cadet row by `cap_id` or None.

    Row format: (cadet_id, cap_id, first_name, last_name, date_of_birth, join_date)
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT cadet_id, cap_id, first_name, last_name, date_of_birth, join_date FROM cadet WHERE cap_id = %s",
            (capid,)
        )
        row = cur.fetchone()
        return row
    except Error:
        logging.exception('Error fetching cadet by cap_id')
        return None
    finally:
        conn.close()


class CadetForm(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(padx=18, pady=18)
        self._suppress_traces = False
        self._current_existing_cadet_id = None
        self.create_widgets()
        self.load_lookups()

    def create_widgets(self):
        # fonts and styles
        header_font = tkfont.Font(size=16, weight='bold')
        label_font = tkfont.Font(size=10)
        entry_width = 32

        # top header
        header = ttk.Label(self, text="Add A Cadet", font=header_font)
        header.grid(row=0, column=0, columnspan=2, pady=(0,16))

        # Personal info frame
        personal = ttk.Labelframe(self, text='Personal Information', padding=(16, 12))
        personal.grid(row=1, column=0, columnspan=2, sticky='ew', padx=4, pady=4)
        personal.columnconfigure(1, weight=1)

        ttk.Label(personal, text='CAP ID:', font=label_font).grid(row=0, column=0, sticky='e', padx=(0,8), pady=8)
        self.capid_var = tk.StringVar()
        ttk.Entry(personal, textvariable=self.capid_var, width=entry_width).grid(row=0, column=1, sticky='w', padx=(0,12), pady=8)
        try:
            self.capid_var.trace_add('write', lambda *a: self._on_capid_change())
        except Exception:
            self.capid_var.trace('w', lambda *a: self._on_capid_change())

        ttk.Label(personal, text='First name:', font=label_font).grid(row=1, column=0, sticky='e', padx=(0,8), pady=8)
        self.fname_var = tk.StringVar()
        ttk.Entry(personal, textvariable=self.fname_var, width=entry_width).grid(row=1, column=1, sticky='w', padx=(0,12), pady=8)

        ttk.Label(personal, text='Last name:', font=label_font).grid(row=2, column=0, sticky='e', padx=(0,8), pady=8)
        self.lname_var = tk.StringVar()
        ttk.Entry(personal, textvariable=self.lname_var, width=entry_width).grid(row=2, column=1, sticky='w', padx=(0,12), pady=8)

        # Dates frame
        dates = ttk.Labelframe(self, text='Dates', padding=(16, 12))
        dates.grid(row=2, column=0, columnspan=2, sticky='ew', padx=4, pady=6)
        dates.columnconfigure(1, weight=1)

        ttk.Label(dates, text='Date of birth (YYYY-MM-DD):', font=label_font).grid(row=0, column=0, sticky='e', padx=(0,8), pady=8)
        self.bday_var = tk.StringVar()
        ttk.Entry(dates, textvariable=self.bday_var, width=entry_width).grid(row=0, column=1, sticky='w', padx=(0,12), pady=8)

        ttk.Label(dates, text='Join date (YYYY-MM-DD):', font=label_font).grid(row=1, column=0, sticky='e', padx=(0,8), pady=8)
        self.join_date_var = tk.StringVar()
        ttk.Entry(dates, textvariable=self.join_date_var, width=entry_width).grid(row=1, column=1, sticky='w', padx=(0,12), pady=8)

        # Assignment frame
        assign = ttk.Labelframe(self, text='Assignment', padding=(16, 12))
        assign.grid(row=3, column=0, columnspan=2, sticky='ew', padx=4, pady=6)
        assign.columnconfigure(1, weight=1)

        # Line/Staff and Support positions
        ttk.Label(assign, text='Line/Staff Position:', font=label_font).grid(row=0, column=0, sticky='e', padx=(0,8), pady=8)
        self.linepos_cb = ttk.Combobox(assign, state='readonly', width=entry_width-2)
        self.linepos_cb.grid(row=0, column=1, sticky='w', padx=(0,12), pady=8)

        ttk.Label(assign, text='Support Position:', font=label_font).grid(row=1, column=0, sticky='e', padx=(0,8), pady=8)
        self.staffpos_cb = ttk.Combobox(assign, state='readonly', width=entry_width-2)
        self.staffpos_cb.grid(row=1, column=1, sticky='w', padx=(0,12), pady=8)

        ttk.Label(assign, text='Rank:', font=label_font).grid(row=2, column=0, sticky='e', padx=(0,8), pady=8)
        self.rank_cb = ttk.Combobox(assign, state='readonly', width=entry_width-2)
        self.rank_cb.grid(row=2, column=1, sticky='w', padx=(0,12), pady=8)

        # Button bar
        btn_frame = ttk.Frame(self, padding=(0,12))
        btn_frame.grid(row=4, column=0, columnspan=2, sticky='ew')
        btn_frame.columnconfigure((0,1,2), weight=1)

        self.submit_btn = ttk.Button(btn_frame, text='Save', command=self.submit)
        self.submit_btn.grid(row=0, column=0, padx=6, sticky='e')
        # Accent primary action
        try:
            apply_accent(self.submit_btn)
        except Exception:
            pass

        self.clear_btn = ttk.Button(btn_frame, text='Clear', command=self._clear_form)
        self.clear_btn.grid(row=0, column=1, padx=6)

        self.refresh_btn = ttk.Button(btn_frame, text='Refresh lookups', command=self.load_lookups)
        self.refresh_btn.grid(row=0, column=2, padx=6, sticky='w')

        # status bar
        self.status_var = tk.StringVar()
        status = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w')
        status.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(12,0), ipady=4)

    def load_lookups(self):
        # populate positions
        positions = fetch_positions()
        if positions:
            # positions may include a 'line' flag: positions -> list of (id, name, line)
            self.position_map = {str(r[0]): r[1] for r in positions}
            self.position_ids = [str(r[0]) for r in positions]
            names = [r[1] or f"Position {r[0]}" for r in positions]
            # split positions into line/staff (line flag == 1) and support (line flag != 1)
            line_names = [r[1] or f"Position {r[0]}" for r in positions if (r[2] if len(r) > 2 else None) == 1]
            support_names = [r[1] or f"Position {r[0]}" for r in positions if (r[2] if len(r) > 2 else None) != 1]
            self.linepos_cb['values'] = line_names
            self.staffpos_cb['values'] = support_names
            # set sensible defaults where possible
            # no generic position defaults required
            if line_names:
                try:
                    self.linepos_cb.current(0)
                except Exception:
                    pass
            if support_names:
                try:
                    self.staffpos_cb.current(0)
                except Exception:
                    pass
            self.status_var.set(f'Loaded {len(positions)} positions')
        else:
            self.position_map = {}
            self.position_ids = []
            self.linepos_cb['values'] = []
            self.staffpos_cb['values'] = []

        ranks = fetch_ranks()
        if ranks:
            self.rank_map = {str(r[0]): r[1] for r in ranks}
            self.rank_ids = [str(r[0]) for r in ranks]
            names = [r[1] or f"Rank {r[0]}" for r in ranks]
            self.rank_cb['values'] = names
            if names:
                self.rank_cb.current(0)
            # append to status
            self.status_var.set((self.status_var.get() + ', ' if self.status_var.get() else '') + f'{len(ranks)} ranks')
        else:
            self.rank_map = {}
            self.rank_ids = []
            self.rank_cb['values'] = []

    def _populate_from_row(self, row):
        # row: (cadet_id, cap_id, first_name, last_name, date_of_birth, join_date)
        if not row:
            return
        try:
            self._suppress_traces = True
            self._current_existing_cadet_id = row[0]
            self.capid_var.set(str(row[1]))
            self.fname_var.set(row[2] or "")
            self.lname_var.set(row[3] or "")
            # set dates
            self.bday_var.set(row[4].isoformat() if row[4] is not None else "")
            self.join_date_var.set(row[5].isoformat() if row[5] is not None else "")
            # select position and rank in comboboxes by value
            try:
                cadet_positions = fetch_cadet_positions(row[0])
                if cadet_positions:
                    pos_id = cadet_positions[0]
                    positions = fetch_positions()
                    # build lookup by id
                    pos_lookup = {p[0]: p for p in positions}
                    if pos_id in pos_lookup:
                        p = pos_lookup[pos_id]
                        pname = p[1]
                        # if line flag present, prefer setting line/staff accordingly
                        try:
                            line_flag = p[2] if len(p) > 2 else None
                            if line_flag == 1:
                                # position name should exist in linepos list
                                vals = list(self.linepos_cb['values'])
                                if pname in vals:
                                    self.linepos_cb.current(vals.index(pname))
                            else:
                                vals = list(self.staffpos_cb['values'])
                                if pname in vals:
                                    self.staffpos_cb.current(vals.index(pname))
                        except Exception:
                            pass
                # select rank if cadet has one
                cadet_ranks = fetch_cadet_ranks(row[0])
                if cadet_ranks:
                    rank_id = cadet_ranks[0]
                    ranks = fetch_ranks()
                    for rid, rname in ranks:
                        if rid == rank_id:
                            vals = list(self.rank_cb['values'])
                            if rname in vals:
                                self.rank_cb.current(vals.index(rname))
                            break
            except Exception:
                logging.exception('Error selecting lookup values')
        finally:
            self._suppress_traces = False

    def _clear_form(self):
        self._current_existing_cadet_id = None
        self.capid_var.set("")
        self.fname_var.set("")
        self.lname_var.set("")
        self.bday_var.set("")
        self.join_date_var.set("")
        # reset comboboxes
        try:
            self.position_cb.set('')
        except Exception:
            pass
        try:
            self.rank_cb.set('')
        except Exception:
            pass

    def _on_capid_change(self):
        if getattr(self, '_suppress_traces', False):
            return
        val = self.capid_var.get().strip()
        if not val or not val.isdigit():
            return
        capid = int(val)
        row = fetch_cadet_by_capid(capid)
        if row:
            # populate the form with existing values
            self._populate_from_row(row)
        else:
            # clear existing id so submit will insert
            self._current_existing_cadet_id = None

    def submit(self):
        # Gather and validate inputs
        try:
            capid = int(self.capid_var.get())
        except ValueError:
            messagebox.showerror("Validation", "CAP ID must be an integer.")
            return

        fname = self.fname_var.get().strip()
        lname = self.lname_var.get().strip()
        bday = self.bday_var.get().strip()
        join_date = self.join_date_var.get().strip()

        if not fname or not lname:
            messagebox.showerror("Validation", "First name and last name are required.")
            return

        # validate dates if provided
        if bday:
            try:
                datetime.datetime.strptime(bday, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Validation", "Date of birth must be in YYYY-MM-DD format.")
                return
        else:
            bday = None

        if join_date:
            try:
                datetime.datetime.strptime(join_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Validation", "Join date must be in YYYY-MM-DD format.")
                return
        else:
            join_date = None

        # Resolve selected rank id
        rank_name = self.rank_cb.get() if hasattr(self, 'rank_cb') else ''
        rank_id = None
        if rank_name and hasattr(self, 'rank_ids'):
            ranks = fetch_ranks()
            for rid, rname in ranks:
                if (rname or f"Rank {rid}") == rank_name:
                    rank_id = rid
                    break

        # If this CAP ID already exists, offer to edit the existing record
        if getattr(self, '_current_existing_cadet_id', None):
            if messagebox.askyesno('Edit existing cadet', 'A cadet with this CAP ID exists.\nDo you want to edit the existing record?'):
                # perform UPDATE
                conn = get_connection()
                if not conn:
                    return
                try:
                    cur = conn.cursor()
                    sql = ("UPDATE cadet SET first_name=%s, last_name=%s, date_of_birth=%s, join_date=%s WHERE cadet_id=%s")
                    params = (fname, lname, bday, join_date, self._current_existing_cadet_id)
                    cur.execute(sql, params)
                    conn.commit()
                    # update rank_has_cadet: remove old and insert new if selected
                    try:
                        cur.execute('DELETE FROM rank_has_cadet WHERE cadet_cadet_id = %s', (self._current_existing_cadet_id,))
                        if rank_id:
                            cur.execute('INSERT INTO rank_has_cadet (rank_rank_id, cadet_cadet_id, date_received) VALUES (%s, %s, NOW())', (rank_id, self._current_existing_cadet_id))
                            conn.commit()
                    except Exception:
                        logging.exception('Could not update cadet ranks')
                    # update position_has_cadet: remove old and insert new if selected
                    try:
                        cur.execute('DELETE FROM position_has_cadet WHERE cadet_cadet_id = %s', (self._current_existing_cadet_id,))
                        # insert mappings from Line/Staff and Support selections
                        insert_ids = []
                        try:
                            lsel = self.linepos_cb.get().strip() if hasattr(self, 'linepos_cb') else ''
                            ssel = self.staffpos_cb.get().strip() if hasattr(self, 'staffpos_cb') else ''
                            positions = fetch_positions()
                            for p in positions:
                                pid = p[0]
                                pname = p[1]
                                if pname == lsel and pid not in insert_ids:
                                    insert_ids.append(pid)
                                if pname == ssel and pid not in insert_ids:
                                    insert_ids.append(pid)
                        except Exception:
                            logging.exception('Error resolving additional position selections')
                        for pid in insert_ids:
                            cur.execute('INSERT INTO position_has_cadet (position_position_id, cadet_cadet_id, start_date, end_date, notes) VALUES (%s, %s, %s, NULL, NULL)', (pid, self._current_existing_cadet_id, join_date))
                        conn.commit()
                    except Exception:
                        logging.exception('Could not update cadet position')
                    messagebox.showinfo('Success', 'Cadet updated successfully.')
                    self._clear_form()
                except Error as e:
                    messagebox.showerror('Database Error', f'Could not update cadet:\n{e}')
                    logging.exception('Could not update cadet')
                finally:
                    conn.close()
            else:
                # user cancelled edit
                return
        else:
            # Insert new cadet
            conn = get_connection()
            if not conn:
                return
            try:
                cur = conn.cursor()
                sql = ("INSERT INTO cadet (first_name, last_name, date_of_birth, join_date, cap_id) "
                       "VALUES (%s, %s, %s, %s, %s)")
                params = (fname, lname, bday, join_date, capid)
                cur.execute(sql, params)
                conn.commit()
                # insert rank and position mappings if selected
                try:
                    new_id = cur.lastrowid
                    if rank_id:
                        cur.execute('INSERT INTO rank_has_cadet (rank_rank_id, cadet_cadet_id, date_received) VALUES (%s, %s, NOW())', (rank_id, new_id))
                        conn.commit()
                    # insert position mappings: include position_id and additional selections
                    insert_ids = []
                    try:
                        # flight removed: only consider line and support/staff selections
                        lsel = self.linepos_cb.get().strip() if hasattr(self, 'linepos_cb') else ''
                        ssel = self.staffpos_cb.get().strip() if hasattr(self, 'staffpos_cb') else ''
                        positions = fetch_positions()
                        for p in positions:
                            pid = p[0]
                            pname = p[1]
                            if pname == lsel and pid not in insert_ids:
                                insert_ids.append(pid)
                            if pname == ssel and pid not in insert_ids:
                                insert_ids.append(pid)
                    except Exception:
                        logging.exception('Error resolving additional position selections')
                    for pid in insert_ids:
                        cur.execute('INSERT INTO position_has_cadet (position_position_id, cadet_cadet_id, start_date, end_date, notes) VALUES (%s, %s, %s, NULL, NULL)', (pid, new_id, join_date))
                        conn.commit()
                except Exception:
                    logging.exception('Could not insert cadet mapping rows')
                messagebox.showinfo('Success', 'Cadet added successfully.')
                # clear form
                self._clear_form()
            except IntegrityError as e:
                messagebox.showerror('Database Error', f'Insert failed due to constraint (duplicate or invalid data):\n{e}')
                logging.exception('Integrity error inserting cadet')
            except Error as e:
                messagebox.showerror('Database Error', f'Could not insert cadet:\n{e}')
                logging.exception('Could not insert cadet')
            finally:
                conn.close()

    def _clean_name(self, s: str) -> str:
        # lowercase, strip spaces, remove non-alphanumeric characters except hyphen/underscore
        s = (s or "").strip().lower()
        # keep letters, digits, hyphen and underscore
        return re.sub(r'[^a-z0-9_-]', '', s)

    def generate_email(self) -> str:
        # legacy email generation removed for new schema
        return ""


def main():
    root = tk.Tk()
    root.title("CAP Cadet Tracker")
    # Apply Windows 11-like theme if available (safe fallback inside theme_setup)
    try:
        theme_setup(root, dark=False)
    except Exception:
        try:
            style = ttk.Style()
            style.theme_use('clam')
        except Exception:
            pass
    root.geometry('550x600')
    root.resizable(True, True)
    root.iconbitmap('my_icon.ico') 
    app = CadetForm(master=root)
    root.mainloop()


if __name__ == '__main__':
    main()
