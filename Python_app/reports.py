import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging
try:
    from ui_theme import apply_accent, setup as theme_setup
except Exception:
    def apply_accent(_btn):
        return
    def theme_setup(_root, dark=False):
        return

# DB helper (use same credentials as other modules)
try:
    import mysql.connector
    from mysql.connector import Error
except Exception:
    mysql = None

DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cap_cadet_tracker_3.0',
}


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        logging.exception('DB connect failed')
        messagebox.showerror('DB Error', f'Could not connect to DB:\n{e}')
        return None


class ReportForm(tk.Toplevel):
    """A simple incident/report form to record Good/Bad reports with witnesses and a resolution flow.

    The form will create tables if they do not exist:
      - incident_report
      - incident_witness

    Fields saved:
      - cadet_idcadet (nullable)
      - report_type ('Good'/'Bad')
      - title, description
      - reported_by_capid
      - report_date
      - resolved (0/1)
      - resolved_by_capid, resolution_notes, resolved_date

    Witnesses are stored in incident_witness (one row per witness name/capid).
    """

    def __init__(self, master=None, selected_cadet=None, report_id: int = None):
        super().__init__(master)
        self.title('Submit Report')
        self.geometry('700x600')
        self.selected_cadet = selected_cadet
        self.report_id = report_id
        self._build_ui()
        self._ensure_tables()
        if self.report_id:
            self._load_report(self.report_id)

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill='both', expand=True)

        # Cadet selector (REQUIRED) - prefill if dashboard passed selected cadet
        ttk.Label(frm, text='Cadet (required):').grid(row=0, column=0, sticky='e')
        self.cadet_var = tk.StringVar()
        self.cadet_entry = ttk.Entry(frm, textvariable=self.cadet_var, width=30)
        self.cadet_entry.grid(row=0, column=1, sticky='w')
        self.cadet_entry.bind('<FocusOut>', lambda e: self._autofill_cadet())
        self.cadet_entry.bind('<Return>', lambda e: self._autofill_cadet())
        if self.selected_cadet:
            try:
                self.cadet_var.set(f"{self.selected_cadet[2]} {self.selected_cadet[3]} ({self.selected_cadet[1]})")
            except Exception:
                pass
        
        ttk.Label(frm, text='Enter CAP ID or Last Name', font=('Arial', 8, 'italic')).grid(row=0, column=2, sticky='w', padx=(5,0))

        ttk.Label(frm, text='Report Type:').grid(row=1, column=0, sticky='e')
        self.type_var = tk.StringVar(value='Bad')
        self.type_cb = ttk.Combobox(frm, textvariable=self.type_var, values=['Bad', 'Good'], state='readonly', width=20)
        self.type_cb.grid(row=1, column=1, sticky='w')

        ttk.Label(frm, text='Title:').grid(row=2, column=0, sticky='e')
        self.title_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.title_var, width=60).grid(row=2, column=1, sticky='w', pady=6)

        ttk.Label(frm, text='Description:').grid(row=3, column=0, sticky='ne')
        self.desc_text = tk.Text(frm, width=60, height=8)
        self.desc_text.grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frm, text='Witnesses (one per line, optional - Name or CAPID):').grid(row=4, column=0, sticky='ne')
        self.witness_text = tk.Text(frm, width=60, height=6)
        self.witness_text.grid(row=4, column=1, sticky='w', pady=6)

        ttk.Label(frm, text='Reported by (CAP ID):').grid(row=5, column=0, sticky='e')
        self.reporter_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.reporter_var, width=20).grid(row=5, column=1, sticky='w')

        ttk.Label(frm, text='Report Date:').grid(row=6, column=0, sticky='e')
        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        ttk.Entry(frm, textvariable=self.date_var, width=20).grid(row=6, column=1, sticky='w')

        # Resolution area
        res_frame = ttk.Labelframe(frm, text='Resolution (optional)', padding=8)
        res_frame.grid(row=7, column=0, columnspan=2, sticky='ew', pady=8)
        res_frame.columnconfigure(1, weight=1)

        self.resolved_var = tk.IntVar(value=0)
        ttk.Checkbutton(res_frame, text='Resolved', variable=self.resolved_var).grid(row=0, column=0, sticky='w')
        ttk.Label(res_frame, text='Resolved by (CAP ID):').grid(row=1, column=0, sticky='e')
        self.res_by_var = tk.StringVar()
        ttk.Entry(res_frame, textvariable=self.res_by_var, width=20).grid(row=1, column=1, sticky='w')
        ttk.Label(res_frame, text='Resolution notes:').grid(row=2, column=0, sticky='ne')
        self.res_notes = tk.Text(res_frame, width=50, height=4)
        self.res_notes.grid(row=2, column=1, sticky='w')

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(12,0))
        btn_save = ttk.Button(btn_frame, text='Save Report', command=self.save_report)
        btn_save.grid(row=0, column=0, padx=6)
        try:
            apply_accent(btn_save)
        except Exception:
            pass
        ttk.Button(btn_frame, text='Cancel', command=self.destroy).grid(row=0, column=1, padx=6)

    def _ensure_tables(self):
        # The new schema provides a `report` table. No creation is necessary here.
        return

    def _autofill_cadet(self):
        """Auto-populate cadet name from CAP ID or vice versa."""
        text = self.cadet_var.get().strip()
        if not text:
            return
        
        # If it already looks like "FirstName LastName (CAPID)", leave it
        if '(' in text and ')' in text:
            return
        
        conn = get_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            # Try as CAP ID first (numeric)
            if text.isdigit():
                capid = int(text)
                cur.execute('SELECT cadet_id, cap_id, first_name, last_name FROM cadet WHERE cap_id = %s LIMIT 1', (capid,))
                row = cur.fetchone()
                if row:
                    self.cadet_var.set(f"{row[2]} {row[3]} ({row[1]})")
                    return
            
            # Try as last name (partial match)
            cur.execute('SELECT cadet_id, cap_id, first_name, last_name FROM cadet WHERE last_name LIKE %s ORDER BY last_name, first_name LIMIT 1', (f'%{text}%',))
            row = cur.fetchone()
            if row:
                self.cadet_var.set(f"{row[2]} {row[3]} ({row[1]})")
        except Exception:
            logging.exception('Error auto-filling cadet')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def save_report(self):
        # gather inputs
        cadet_text = self.cadet_var.get().strip()
        if not cadet_text:
            messagebox.showerror('Validation', 'Cadet field is required. Please enter a CAP ID or name.')
            return
        
        cadet_id = None
        if '(' in cadet_text and ')' in cadet_text:
            # try to extract capid inside parens
            try:
                inside = cadet_text.split('(')[-1].split(')')[0]
                # inside might be capid
                if inside.isdigit():
                    capid_val = int(inside)
                    # try to resolve cadet id
                    conn = get_connection()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute('SELECT cadet_id FROM cadet WHERE cap_id = %s LIMIT 1', (capid_val,))
                            rr = cur.fetchone()
                            if rr:
                                cadet_id = rr[0]
                        except Exception:
                            logging.exception('Error resolving cadet by capid')
                        finally:
                            try:
                                conn.close()
                            except Exception:
                                pass
            except Exception:
                pass
        
        if not cadet_id:
            messagebox.showerror('Validation', 'Could not find cadet in database. Please enter a valid CAP ID or use the auto-fill.')
            return

        # Map UI Good/Bad to schema values if necessary; schema uses 'Positive'/'Negative'
        ui_type = self.type_var.get()
        if ui_type.lower() in ('good', 'positive'):
            rtype = 'Positive'
        else:
            rtype = 'Negative'
        title = self.title_var.get().strip() or None
        desc = self.desc_text.get('1.0', 'end').strip() or ''
        # Append witnesses (if any) into the description to preserve that data
        witnesses_raw = self.witness_text.get('1.0', 'end').strip()
        witnesses = [w.strip() for w in witnesses_raw.splitlines() if w.strip()]
        if witnesses:
            desc = desc + '\n\nWitnesses:\n' + '\n'.join(witnesses)
        # Append resolution notes (if any) into the description as well so data isn't lost
        res_notes = self.res_notes.get('1.0', 'end').strip() or None
        if res_notes:
            desc = (desc or '') + '\n\nResolution Notes:\n' + res_notes
        if not desc:
            desc = None
        reporter = self.reporter_var.get().strip() or None
        date_str = self.date_var.get().strip() or None
        try:
            report_date = None
            if date_str:
                report_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            messagebox.showerror('Validation', 'Report date must be YYYY-MM-DD')
            return

        resolved = 1 if self.resolved_var.get() else 0
        res_by = self.res_by_var.get().strip() or None
        res_notes = self.res_notes.get('1.0', 'end').strip() or None
        resolved_date = datetime.datetime.now() if resolved else None

        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            if self.report_id:
                # update existing report row in new schema
                cur.execute('''UPDATE report SET report_type=%s, description=%s, created_by=%s, cadet_cadet_id=%s, Incident_date=%s, resolved=%s, resolved_by=%s WHERE report_id = %s''',
                            (rtype, desc, reporter, cadet_id, report_date, resolved, res_by, self.report_id))
                conn.commit()
                messagebox.showinfo('Saved', f'Report updated (id {self.report_id})')
                self.destroy()
                return
            # insert new into `report` table
            cur.execute('''INSERT INTO report (report_type, description, created_by, cadet_cadet_id, Incident_date, resolved, resolved_by) VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                        (rtype, desc, reporter, cadet_id, report_date, resolved, res_by))
            report_id = cur.lastrowid
            conn.commit()
            messagebox.showinfo('Saved', f'Report saved (id {report_id})')
            self.destroy()
        except Exception:
            conn.rollback()
            logging.exception('Error saving report')
            messagebox.showerror('DB Error', 'Could not save report (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass


class ReportFormFrame(ttk.Frame):
    """Embeddable version of the Report form to be used inside a tab without opening a new window.

    on_close: optional callback called after successful save to allow parent to refresh UI.
    """
    def __init__(self, master=None, selected_cadet=None, report_id: int = None, on_close=None):
        super().__init__(master)
        self.selected_cadet = selected_cadet
        self.report_id = report_id
        self._on_close_cb = on_close
        self._build_ui()
        if self.report_id:
            self._load_report(self.report_id)

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text='Cadet (required):').grid(row=0, column=0, sticky='e')
        self.cadet_var = tk.StringVar()
        self.cadet_entry = ttk.Entry(frm, textvariable=self.cadet_var, width=30)
        self.cadet_entry.grid(row=0, column=1, sticky='w')
        self.cadet_entry.bind('<FocusOut>', lambda e: self._autofill_cadet())
        self.cadet_entry.bind('<Return>', lambda e: self._autofill_cadet())
        if self.selected_cadet:
            try:
                self.cadet_var.set(f"{self.selected_cadet[2]} {self.selected_cadet[3]} ({self.selected_cadet[1]})")
            except Exception:
                pass
        ttk.Label(frm, text='Enter CAP ID or Last Name', font=('Arial', 8, 'italic')).grid(row=0, column=2, sticky='w', padx=(5,0))

        ttk.Label(frm, text='Report Type:').grid(row=1, column=0, sticky='e')
        self.type_var = tk.StringVar(value='Bad')
        self.type_cb = ttk.Combobox(frm, textvariable=self.type_var, values=['Bad', 'Good'], state='readonly', width=20)
        self.type_cb.grid(row=1, column=1, sticky='w')

        ttk.Label(frm, text='Title:').grid(row=2, column=0, sticky='e')
        self.title_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.title_var, width=60).grid(row=2, column=1, sticky='w', pady=6)

        ttk.Label(frm, text='Description:').grid(row=3, column=0, sticky='ne')
        self.desc_text = tk.Text(frm, width=60, height=8)
        self.desc_text.grid(row=3, column=1, sticky='w', pady=6)

        ttk.Label(frm, text='Witnesses (one per line, optional - Name or CAPID):').grid(row=4, column=0, sticky='ne')
        self.witness_text = tk.Text(frm, width=60, height=6)
        self.witness_text.grid(row=4, column=1, sticky='w', pady=6)

        ttk.Label(frm, text='Reported by (CAP ID):').grid(row=5, column=0, sticky='e')
        self.reporter_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.reporter_var, width=20).grid(row=5, column=1, sticky='w')

        ttk.Label(frm, text='Report Date:').grid(row=6, column=0, sticky='e')
        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        ttk.Entry(frm, textvariable=self.date_var, width=20).grid(row=6, column=1, sticky='w')

        res_frame = ttk.Labelframe(frm, text='Resolution (optional)', padding=8)
        res_frame.grid(row=7, column=0, columnspan=2, sticky='ew', pady=8)
        res_frame.columnconfigure(1, weight=1)
        self.resolved_var = tk.IntVar(value=0)
        ttk.Checkbutton(res_frame, text='Resolved', variable=self.resolved_var).grid(row=0, column=0, sticky='w')
        ttk.Label(res_frame, text='Resolved by (CAP ID):').grid(row=1, column=0, sticky='e')
        self.res_by_var = tk.StringVar()
        ttk.Entry(res_frame, textvariable=self.res_by_var, width=20).grid(row=1, column=1, sticky='w')
        ttk.Label(res_frame, text='Resolution notes:').grid(row=2, column=0, sticky='ne')
        self.res_notes = tk.Text(res_frame, width=50, height=4)
        self.res_notes.grid(row=2, column=1, sticky='w')

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(12,0))
        btn_save = ttk.Button(btn_frame, text='Save Report', command=self._save_and_close)
        btn_save.grid(row=0, column=0, padx=6)
        try:
            apply_accent(btn_save)
        except Exception:
            pass
        ttk.Button(btn_frame, text='Clear', command=self._clear_form).grid(row=0, column=1, padx=6)

    # Shared logic: reuse ReportForm's methods by copying, adapted for frame
    def _autofill_cadet(self):
        text = self.cadet_var.get().strip()
        if not text:
            return
        if '(' in text and ')' in text:
            return
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            if text.isdigit():
                capid = int(text)
                cur.execute('SELECT cadet_id, cap_id, first_name, last_name FROM cadet WHERE cap_id = %s LIMIT 1', (capid,))
                row = cur.fetchone()
                if row:
                    self.cadet_var.set(f"{row[2]} {row[3]} ({row[1]})")
                    return
            cur.execute('SELECT cadet_id, cap_id, first_name, last_name FROM cadet WHERE last_name LIKE %s ORDER BY last_name, first_name LIMIT 1', (f'%{text}%',))
            row = cur.fetchone()
            if row:
                self.cadet_var.set(f"{row[2]} {row[3]} ({row[1]})")
        except Exception:
            logging.exception('Error auto-filling cadet')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _save_and_close(self):
        ok = self._save_report_internal()
        if ok:
            if callable(self._on_close_cb):
                try:
                    self._on_close_cb()
                except Exception:
                    pass

    def _clear_form(self):
        try:
            self.cadet_var.set('')
            self.type_var.set('Bad')
            self.title_var.set('')
            self.desc_text.delete('1.0', 'end')
            self.witness_text.delete('1.0', 'end')
            self.reporter_var.set('')
            self.date_var.set(datetime.date.today().isoformat())
            self.resolved_var.set(0)
            self.res_by_var.set('')
            self.res_notes.delete('1.0', 'end')
        except Exception:
            pass

    def _save_report_internal(self) -> bool:
        cadet_text = self.cadet_var.get().strip()
        if not cadet_text:
            messagebox.showerror('Validation', 'Cadet field is required. Please enter a CAP ID or name.')
            return False
        cadet_id = None
        if '(' in cadet_text and ')' in cadet_text:
            try:
                inside = cadet_text.split('(')[-1].split(')')[0]
                if inside.isdigit():
                    capid_val = int(inside)
                    conn = get_connection()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute('SELECT cadet_id FROM cadet WHERE cap_id = %s LIMIT 1', (capid_val,))
                            rr = cur.fetchone()
                            if rr:
                                cadet_id = rr[0]
                        finally:
                            try:
                                conn.close()
                            except Exception:
                                pass
            except Exception:
                pass
        if not cadet_id:
            messagebox.showerror('Validation', 'Could not find cadet in database. Please enter a valid CAP ID or use the auto-fill.')
            return False

        ui_type = self.type_var.get()
        rtype = 'Positive' if ui_type.lower() in ('good', 'positive') else 'Negative'
        title = self.title_var.get().strip() or None
        desc = self.desc_text.get('1.0', 'end').strip() or ''
        witnesses_raw = self.witness_text.get('1.0', 'end').strip()
        witnesses = [w.strip() for w in witnesses_raw.splitlines() if w.strip()]
        if witnesses:
            desc = desc + '\n\nWitnesses:\n' + '\n'.join(witnesses)
        res_notes = self.res_notes.get('1.0', 'end').strip() or None
        if res_notes:
            desc = (desc or '') + '\n\nResolution Notes:\n' + res_notes
        if not desc:
            desc = None
        reporter = self.reporter_var.get().strip() or None
        date_str = self.date_var.get().strip() or None
        try:
            report_date = None
            if date_str:
                report_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            messagebox.showerror('Validation', 'Report date must be YYYY-MM-DD')
            return False
        resolved = 1 if self.resolved_var.get() else 0
        res_by = self.res_by_var.get().strip() or None
        conn = get_connection()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            if self.report_id:
                cur.execute('''UPDATE report SET report_type=%s, description=%s, created_by=%s, cadet_cadet_id=%s, Incident_date=%s, resolved=%s, resolved_by=%s WHERE report_id = %s''',
                            (rtype, desc, reporter, cadet_id, report_date, resolved, res_by, self.report_id))
                conn.commit()
                messagebox.showinfo('Saved', f'Report updated (id {self.report_id})')
                return True
            cur.execute('''INSERT INTO report (report_type, description, created_by, cadet_cadet_id, Incident_date, resolved, resolved_by) VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                        (rtype, desc, reporter, cadet_id, report_date, resolved, res_by))
            rid = cur.lastrowid
            conn.commit()
            messagebox.showinfo('Saved', f'Report saved (id {rid})')
            return True
        except Exception:
            conn.rollback()
            logging.exception('Error saving report')
            messagebox.showerror('DB Error', 'Could not save report (see terminal).')
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _load_report(self, report_id: int):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('SELECT cadet_cadet_id, report_type, description, created_by, Incident_date, resolved, resolved_by FROM report WHERE report_id = %s', (report_id,))
            row = cur.fetchone()
            if not row:
                return
            cadet_id, rtype, desc, reporter, report_date, resolved, res_by = row
            # set fields
            if cadet_id:
                # try to lookup capid/name
                try:
                    cur.execute('SELECT cap_id, first_name, last_name FROM cadet WHERE cadet_id = %s', (cadet_id,))
                    c = cur.fetchone()
                    if c:
                        self.cadet_var.set(f"{c[1]} {c[2]} ({c[0]})")
                except Exception:
                    pass
            # map DB enum to UI choices
            if rtype and rtype.lower() == 'positive':
                self.type_var.set('Good')
            else:
                self.type_var.set('Bad')
            # description may contain appended witnesses and/or resolution notes; try to split them out
            main_desc = desc or ''
            witness_block = ''
            res_block = ''
            if main_desc:
                # extract witnesses block if present
                if '\n\nWitnesses:\n' in main_desc:
                    main_desc, rest = main_desc.split('\n\nWitnesses:\n', 1)
                    # rest may also contain resolution notes
                    if '\n\nResolution Notes:\n' in rest:
                        witness_block, res_block = rest.split('\n\nResolution Notes:\n', 1)
                    else:
                        witness_block = rest
                else:
                    # maybe resolution notes appended directly
                    if '\n\nResolution Notes:\n' in main_desc:
                        main_desc, res_block = main_desc.split('\n\nResolution Notes:\n', 1)
            # set description and witness/resolution fields
            self.desc_text.delete('1.0', 'end')
            self.desc_text.insert('1.0', main_desc)
            self.witness_text.delete('1.0', 'end')
            if witness_block:
                self.witness_text.insert('1.0', witness_block)
            self.res_notes.delete('1.0', 'end')
            if res_block:
                self.res_notes.insert('1.0', res_block)
            self.reporter_var.set(reporter or '')
            self.date_var.set(report_date.isoformat() if isinstance(report_date, datetime.date) else (report_date or ''))
            self.resolved_var.set(1 if resolved else 0)
            self.res_by_var.set(res_by or '')
            # resolution notes already set above from parsed description (res_block)
            # no separate witness table in new schema; witnesses may be embedded in description
        except Exception:
            logging.exception('Error loading report')
        finally:
            try:
                conn.close()
            except Exception:
                pass


def fetch_reports(limit=200, sort_by='date', order='DESC'):
    """Fetch recent reports with optional sorting.

    sort_by is one of: 'id', 'cadet_id', 'type', 'title', 'date', 'resolved'.
    order is 'ASC' or 'DESC'. Defaults to date DESC.
    """
    # map friendly keys to actual DB columns (whitelist to prevent SQL injection)
    col_map = {
        'id': 'report_id',
        'cadet_id': 'cadet_cadet_id',
        'type': 'report_type',
        'date': 'Incident_date',
        'resolved': 'resolved'
    }
    dbcol = col_map.get(sort_by, 'Incident_date')
    order = 'ASC' if str(order).upper() == 'ASC' else 'DESC'

    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        # safe because dbcol is chosen from a whitelist
        sql = f"SELECT report_id, cadet_cadet_id, report_type, LEFT(description,255), Incident_date, resolved FROM report ORDER BY {dbcol} {order} LIMIT %s"
        cur.execute(sql, (limit,))
        return cur.fetchall()
    except Exception:
        logging.exception('Error fetching reports')
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def delete_report(report_id: int):
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM report WHERE report_id = %s', (report_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        logging.exception('Error deleting report')
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    root = tk.Tk()
    try:
        theme_setup(root, dark=False)
    except Exception:
        pass
    root.withdraw()
    ReportForm(master=root)
    root.mainloop()
