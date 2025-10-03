import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging

# DB helper (use same credentials as other modules)
try:
    import mysql.connector
    from mysql.connector import Error
except Exception:
    mysql = None

DB_CONFIG = {
    'host': 'sql5.freesqldatabase.com',
    'user': 'sql5801111',
    'password': 'yhMJiGDnTE',
    'database': 'sql5801111',
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

        # Cadet selector (optional) - prefill if dashboard passed selected cadet
        ttk.Label(frm, text='Cadet (optional):').grid(row=0, column=0, sticky='e')
        self.cadet_var = tk.StringVar()
        self.cadet_entry = ttk.Entry(frm, textvariable=self.cadet_var, width=30)
        self.cadet_entry.grid(row=0, column=1, sticky='w')
        if self.selected_cadet:
            try:
                self.cadet_var.set(f"{self.selected_cadet[2]} {self.selected_cadet[3]} ({self.selected_cadet[1]})")
            except Exception:
                pass

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
        ttk.Button(btn_frame, text='Save Report', command=self.save_report).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text='Cancel', command=self.destroy).grid(row=0, column=1, padx=6)

    def _ensure_tables(self):
        """Create incident_report and incident_witness tables if they do not exist."""
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS incident_report (
                    idincident_report INT AUTO_INCREMENT PRIMARY KEY,
                    cadet_idcadet INT NULL,
                    report_type VARCHAR(16) NOT NULL,
                    title VARCHAR(255),
                    description TEXT,
                    reported_by_capid VARCHAR(32),
                    report_date DATE,
                    resolved TINYINT(1) DEFAULT 0,
                    resolved_by_capid VARCHAR(32),
                    resolution_notes TEXT,
                    resolved_date DATETIME NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS incident_witness (
                    idincident_witness INT AUTO_INCREMENT PRIMARY KEY,
                    incident_report_id INT NOT NULL,
                    witness_text VARCHAR(255),
                    FOREIGN KEY (incident_report_id) REFERENCES incident_report(idincident_report) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            conn.commit()
        except Exception:
            conn.rollback()
            logging.exception('Error creating report tables')
            messagebox.showerror('DB Error', 'Could not create report tables (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def save_report(self):
        # gather inputs
        cadet_text = self.cadet_var.get().strip() or None
        cadet_id = None
        if cadet_text and '(' in cadet_text and ')' in cadet_text:
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
                            cur.execute('SELECT idcadet FROM cadet WHERE cadet_capid = %s LIMIT 1', (capid_val,))
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

        rtype = self.type_var.get()
        title = self.title_var.get().strip() or None
        desc = self.desc_text.get('1.0', 'end').strip() or None
        witnesses_raw = self.witness_text.get('1.0', 'end').strip()
        witnesses = [w.strip() for w in witnesses_raw.splitlines() if w.strip()]
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
                # update existing report
                cur.execute('''UPDATE incident_report SET cadet_idcadet=%s, report_type=%s, title=%s, description=%s, reported_by_capid=%s, report_date=%s, resolved=%s, resolved_by_capid=%s, resolution_notes=%s, resolved_date=%s WHERE idincident_report = %s''',
                            (cadet_id, rtype, title, desc, reporter, report_date, resolved, res_by, res_notes, resolved_date, self.report_id))
                # replace witnesses
                cur.execute('DELETE FROM incident_witness WHERE incident_report_id = %s', (self.report_id,))
                if witnesses:
                    for w in witnesses:
                        cur.execute('INSERT INTO incident_witness (incident_report_id, witness_text) VALUES (%s,%s)', (self.report_id, w))
                conn.commit()
                messagebox.showinfo('Saved', f'Report updated (id {self.report_id})')
                self.destroy()
                return
            # insert new
            cur.execute('''INSERT INTO incident_report (cadet_idcadet, report_type, title, description, reported_by_capid, report_date, resolved, resolved_by_capid, resolution_notes, resolved_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                        (cadet_id, rtype, title, desc, reporter, report_date, resolved, res_by, res_notes, resolved_date))
            report_id = cur.lastrowid
            if witnesses:
                for w in witnesses:
                    cur.execute('INSERT INTO incident_witness (incident_report_id, witness_text) VALUES (%s,%s)', (report_id, w))
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

    def _load_report(self, report_id: int):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('SELECT cadet_idcadet, report_type, title, description, reported_by_capid, report_date, resolved, resolved_by_capid, resolution_notes, resolved_date FROM incident_report WHERE idincident_report = %s', (report_id,))
            row = cur.fetchone()
            if not row:
                return
            cadet_id, rtype, title, desc, reporter, report_date, resolved, res_by, res_notes, resolved_date = row
            # set fields
            if cadet_id:
                # try to lookup capid/name
                try:
                    cur.execute('SELECT cadet_capid, cadet_fname, cadet_lname FROM cadet WHERE idcadet = %s', (cadet_id,))
                    c = cur.fetchone()
                    if c:
                        self.cadet_var.set(f"{c[1]} {c[2]} ({c[0]})")
                except Exception:
                    pass
            self.type_var.set(rtype or 'Bad')
            self.title_var.set(title or '')
            if desc:
                self.desc_text.delete('1.0', 'end')
                self.desc_text.insert('1.0', desc)
            self.reporter_var.set(reporter or '')
            self.date_var.set(report_date.isoformat() if isinstance(report_date, datetime.date) else (report_date or ''))
            self.resolved_var.set(1 if resolved else 0)
            self.res_by_var.set(res_by or '')
            if res_notes:
                self.res_notes.delete('1.0', 'end')
                self.res_notes.insert('1.0', res_notes)
            # load witnesses
            cur.execute('SELECT witness_text FROM incident_witness WHERE incident_report_id = %s ORDER BY idincident_witness', (report_id,))
            wrows = cur.fetchall()
            if wrows:
                self.witness_text.delete('1.0', 'end')
                self.witness_text.insert('1.0', '\n'.join([w[0] for w in wrows if w[0]]))
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
        'id': 'idincident_report',
        'cadet_id': 'cadet_idcadet',
        'type': 'report_type',
        'title': 'title',
        'date': 'report_date',
        'resolved': 'resolved'
    }
    dbcol = col_map.get(sort_by, 'report_date')
    order = 'ASC' if str(order).upper() == 'ASC' else 'DESC'

    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        # safe because dbcol is chosen from a whitelist
        sql = f"SELECT idincident_report, cadet_idcadet, report_type, title, report_date, resolved FROM incident_report ORDER BY {dbcol} {order} LIMIT %s"
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
        cur.execute('DELETE FROM incident_report WHERE idincident_report = %s', (report_id,))
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
    root.withdraw()
    ReportForm(master=root)
    root.mainloop()
