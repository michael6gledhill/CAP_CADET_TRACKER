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

# Database configuration - using credentials you provided
DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cap_cadet_tracker_2.0',
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
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT idflight, flight_name FROM flight")
        rows = cur.fetchall()
        return rows
    except Error as e:
        messagebox.showerror("Database Error", f"Error fetching flights:\n{e}")
        logging.exception('Error fetching flights')
        return []
    finally:
        conn.close()


def fetch_line_positions():
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT idline_position, position_name FROM line_position")
        rows = cur.fetchall()
        return rows
    except Error as e:
        messagebox.showerror("Database Error", f"Error fetching line positions:\n{e}")
        logging.exception('Error fetching line positions')
        return []
    finally:
        conn.close()


def fetch_cadet_by_capid(capid: int):
    """Return a cadet row by cadet_capid or None."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT idcadet, cadet_capid, cadet_fname, cadet_lname, cadet_email, cadet_phone, cadet_birthday, line_position_idline_position, flight_idflight FROM cadet WHERE cadet_capid = %s",
            (capid,)
        )
        row = cur.fetchone()
        return row
    except Error:
        logging.exception('Error fetching cadet by capid')
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
        header_font = tkfont.Font(size=12, weight='bold')
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
        try:
            self.fname_var.trace_add('write', lambda *a: self.update_email())
        except Exception:
            self.fname_var.trace('w', lambda *a: self.update_email())

        ttk.Label(personal, text='Last name:', font=label_font).grid(row=2, column=0, sticky='e', padx=(0,8), pady=8)
        self.lname_var = tk.StringVar()
        ttk.Entry(personal, textvariable=self.lname_var, width=entry_width).grid(row=2, column=1, sticky='w', padx=(0,12), pady=8)
        try:
            self.lname_var.trace_add('write', lambda *a: self.update_email())
        except Exception:
            self.lname_var.trace('w', lambda *a: self.update_email())

        # Contact frame
        contact = ttk.Labelframe(self, text='Contact', padding=(16, 12))
        contact.grid(row=2, column=0, columnspan=2, sticky='ew', padx=4, pady=6)
        contact.columnconfigure(1, weight=1)

        ttk.Label(contact, text='Email:', font=label_font).grid(row=0, column=0, sticky='e', padx=(0,8), pady=8)
        self.email_var = tk.StringVar()
        ttk.Entry(contact, textvariable=self.email_var, width=entry_width).grid(row=0, column=1, sticky='w', padx=(0,12), pady=8)

        ttk.Label(contact, text='Phone:', font=label_font).grid(row=1, column=0, sticky='e', padx=(0,8), pady=8)
        self.phone_var = tk.StringVar()
        ttk.Entry(contact, textvariable=self.phone_var, width=entry_width).grid(row=1, column=1, sticky='w', padx=(0,12), pady=8)

        ttk.Label(contact, text='Birthday:', font=label_font).grid(row=2, column=0, sticky='e', padx=(0,8), pady=8)
        self.bday_var = tk.StringVar()
        ttk.Entry(contact, textvariable=self.bday_var, width=entry_width).grid(row=2, column=1, sticky='w', padx=(0,12), pady=8)

        # Assignment frame
        assign = ttk.Labelframe(self, text='Assignment', padding=(16, 12))
        assign.grid(row=3, column=0, columnspan=2, sticky='ew', padx=4, pady=6)
        assign.columnconfigure(1, weight=1)

        ttk.Label(assign, text='Flight:', font=label_font).grid(row=0, column=0, sticky='e', padx=(0,8), pady=8)
        self.flight_cb = ttk.Combobox(assign, state='readonly', width=entry_width-2)
        self.flight_cb.grid(row=0, column=1, sticky='w', padx=(0,12), pady=8)

        ttk.Label(assign, text='Line position:', font=label_font).grid(row=1, column=0, sticky='e', padx=(0,8), pady=8)
        self.linepos_cb = ttk.Combobox(assign, state='readonly', width=entry_width-2)
        self.linepos_cb.grid(row=1, column=1, sticky='w', padx=(0,12), pady=8)

        # Button bar
        btn_frame = ttk.Frame(self, padding=(0,12))
        btn_frame.grid(row=4, column=0, columnspan=2, sticky='ew')
        btn_frame.columnconfigure((0,1,2), weight=1)

        self.submit_btn = ttk.Button(btn_frame, text='Save', command=self.submit)
        self.submit_btn.grid(row=0, column=0, padx=6, sticky='e')

        self.clear_btn = ttk.Button(btn_frame, text='Clear', command=self._clear_form)
        self.clear_btn.grid(row=0, column=1, padx=6)

        self.refresh_btn = ttk.Button(btn_frame, text='Refresh lookups', command=self.load_lookups)
        self.refresh_btn.grid(row=0, column=2, padx=6, sticky='w')

        # status bar
        self.status_var = tk.StringVar()
        status = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w')
        status.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(12,0), ipady=4)

    def load_lookups(self):
        flights = fetch_flights()
        if flights:
            # store mapping id -> name and set combobox values
            self.flight_map = {str(r[0]): r[1] for r in flights}
            # show names but keep ids in a list in same order
            self.flight_ids = [str(r[0]) for r in flights]
            names = [r[1] or f"Flight {r[0]}" for r in flights]
            self.flight_cb['values'] = names
            if names:
                self.flight_cb.current(0)
            self.status_var.set(f'Loaded {len(flights)} flights')
        else:
            self.flight_map = {}
            self.flight_ids = []
            self.flight_cb['values'] = []

        line_positions = fetch_line_positions()
        if line_positions:
            self.line_map = {str(r[0]): r[1] for r in line_positions}
            self.line_ids = [str(r[0]) for r in line_positions]
            names = [r[1] or f"Position {r[0]}" for r in line_positions]
            self.linepos_cb['values'] = names
            if names:
                self.linepos_cb.current(0)
            self.status_var.set(self.status_var.get() + f', {len(line_positions)} line positions')
        else:
            self.line_map = {}
            self.line_ids = []
            self.linepos_cb['values'] = []

    def _populate_from_row(self, row):
        # row: (idcadet, cadet_capid, cadet_fname, cadet_lname, cadet_email, cadet_phone, cadet_birthday, line_position_idline_position, flight_idflight)
        if not row:
            return
        try:
            self._suppress_traces = True
            self._current_existing_cadet_id = row[0]
            self.capid_var.set(str(row[1]))
            self.fname_var.set(row[2] or "")
            self.lname_var.set(row[3] or "")
            self.email_var.set(row[4] or "")
            self.phone_var.set(str(row[5]) if row[5] is not None else "")
            self.bday_var.set(row[6].isoformat() if row[6] is not None else "")
            # select flight and line position in comboboxes by value
            try:
                if row[8] is not None:
                    # find flight name for id
                    flights = fetch_flights()
                    for fid, fname in flights:
                        if fid == row[8]:
                            vals = list(self.flight_cb['values'])
                            if fname in vals:
                                self.flight_cb.current(vals.index(fname))
                            break
                if row[7] is not None:
                    lps = fetch_line_positions()
                    for lid, lname in lps:
                        if lid == row[7]:
                            vals = list(self.linepos_cb['values'])
                            if lname in vals:
                                self.linepos_cb.current(vals.index(lname))
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
        self.email_var.set("")
        self.phone_var.set("")
        self.bday_var.set("")

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
        email = self.email_var.get().strip()
        phone = self.phone_var.get().strip()
        bday = self.bday_var.get().strip()

        if not fname or not lname or not email:
            messagebox.showerror("Validation", "First name, last name and email are required.")
            return

        if phone:
            # allow typical phone formatting (digits, spaces, dashes, parentheses, +)
            phone_str = phone.strip()
            # enforce a maximum length that matches your VARCHAR(15)
            if len(phone_str) > 15:
                messagebox.showerror("Validation", "Phone is too long (max 15 characters).")
                return
            phone_val = phone_str
        else:
            phone_val = None

        if bday:
            try:
                datetime.datetime.strptime(bday, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Validation", "Birthday must be in YYYY-MM-DD format.")
                return
        else:
            bday = None

        # Ensure email is up-to-date (auto-generated)
        self.update_email()

        # Resolve selected flight and line position ids
        flight_name = self.flight_cb.get()
        line_name = self.linepos_cb.get()

        flight_id = None
        line_id = None

        # find id by name from current loaded lists
        if flight_name and hasattr(self, 'flight_ids'):
            # match by name
            flights = fetch_flights()
            for fid, fname_item in flights:
                if (fname_item or f"Flight {fid}") == flight_name:
                    flight_id = fid
                    break

        if line_name and hasattr(self, 'line_ids'):
            line_positions = fetch_line_positions()
            for lid, lname_item in line_positions:
                if (lname_item or f"Position {lid}") == line_name:
                    line_id = lid
                    break

        if flight_id is None or line_id is None:
            messagebox.showerror("Validation", "Please select a valid flight and line position (use Refresh if lists are empty).")
            return

        # If this CAP ID already exists, offer to edit the existing record
        if getattr(self, '_current_existing_cadet_id', None):
            if messagebox.askyesno('Edit existing cadet', 'A cadet with this CAP ID exists.\nDo you want to edit the existing record?'):
                # perform UPDATE
                conn = get_connection()
                if not conn:
                    return
                try:
                    cur = conn.cursor()
                    sql = ("UPDATE cadet SET cadet_fname=%s, cadet_lname=%s, cadet_email=%s, "
                           "cadet_phone=%s, cadet_birthday=%s, line_position_idline_position=%s, flight_idflight=%s "
                           "WHERE idcadet=%s")
                    params = (fname, lname, email, phone_val, bday, line_id, flight_id, self._current_existing_cadet_id)
                    cur.execute(sql, params)
                    conn.commit()
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
                sql = ("INSERT INTO cadet (cadet_capid, cadet_fname, cadet_lname, cadet_email, "
                       "cadet_phone, cadet_birthday, flight_line_position_idline_position, "
                       "line_position_idline_position, flight_idflight) "
                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")
                params = (capid, fname, lname, email, phone_val, bday, line_id, line_id, flight_id)
                cur.execute(sql, params)
                conn.commit()
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
        # Default format: c_[fi][ln]@kywg.cap.gov
        fmt = "c_[fi][ln]@kywg.cap.gov"
        fname = self.fname_var.get().strip()
        lname = self.lname_var.get().strip()
        if not fname or not lname:
            return ""
        fi = self._clean_name(fname)[0] if self._clean_name(fname) else ''
        ln = self._clean_name(lname)
        email = fmt.replace('[fi]', fi).replace('[ln]', ln)
        return email

    def update_email(self):
        # Do not auto-update email while we're programmatically populating fields
        if getattr(self, '_suppress_traces', False):
            return
        try:
            new_email = self.generate_email()
            current = self.email_var.get().strip()
            # Always auto-update email as the user types. If user edits manually afterwards,
            # their change will be overwritten next time name fields change.
            if new_email and current != new_email:
                self.email_var.set(new_email)
        except Exception:
            logging.exception('Error generating email')


def main():
    root = tk.Tk()
    root.title("CAP Cadet Tracker")
    # use a modern theme if available
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
