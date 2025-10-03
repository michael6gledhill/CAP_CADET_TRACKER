"""
Inspection form GUI for "Personal Appearance & Uniform Inspection Form".

Behavior / assumptions:
- Uses MySQL on localhost with user Michael and password hogbog89 (same DB as other scripts).
- When submitting, the script:
  1. Looks up the cadet by CAP ID (cadet_capid). If not found, the user is shown an error.
  2. Inserts an aggregate row into `inspection_score` (category = 'aggregate', score = total_score).
  3. Inserts a single row into `inspection` with the aggregate score id in inspection_score_idinspection_score.
  4. Links the cadet and inspection by inserting into `cadet_has_inspection`.

- Rating calculation: total score is out of 60 (20 items * 0-3). Mapping used:
    45-60: Excellent
    30-44: Meets Standard
    16-29: Needs Improvement
     0-15: Unacceptable

This file is intentionally conservative about DB changes (it only inserts an aggregate score row and one inspection row).

Requirements: mysql-connector-python must be installed in your environment.

Save as: inspection_form.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import datetime
import mysql.connector
import traceback
import logging
import sys

# --- DB config (same as other scripts) ------------------------------------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cap_cadet_tracker_2.0',
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        logging.exception('DB connection failed')
        messagebox.showerror('Database Error', f'Could not connect to database:\n{e}')
        return None


# --- Rating helpers -------------------------------------------------------
def compute_rating(total, max_total=60):
    if total >= 45:
        return 'Excellent'
    if total >= 30:
        return 'Meets Standard'
    if total >= 16:
        return 'Needs Improvement'
    return 'Unacceptable'


# --- The form -------------------------------------------------------------
class InspectionForm(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.master = master
        self.pack(fill='both', expand=True)

        self.header_font = tkfont.Font(size=14, weight='bold')
        # used to avoid recursive trace callbacks when we programmatically set vars
        self._suppress_traces = False
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self, text='Personal Appearance & Uniform Inspection Form', font=self.header_font)
        title.grid(row=0, column=0, columnspan=4, pady=(0, 12))

        # Top info row
        ttk.Label(self, text='Name:').grid(row=1, column=0, sticky='e')
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(self, textvariable=self.name_var, width=30)
        name_entry.grid(row=1, column=1, sticky='w')

        # trace changes: if user types a name, try to fill CAP ID
        try:
            self.name_var.trace_add('write', lambda *a: self._on_name_change())
        except Exception:
            self.name_var.trace('w', lambda *a: self._on_name_change())

        ttk.Label(self, text='Date:').grid(row=1, column=2, sticky='e')
        self.date_var = tk.StringVar(value=datetime.date.today().isoformat())
        ttk.Entry(self, textvariable=self.date_var, width=20).grid(row=1, column=3, sticky='w')

        ttk.Label(self, text='CAP ID:').grid(row=2, column=0, sticky='e')
        self.capid_var = tk.StringVar()
        capid_entry = ttk.Entry(self, textvariable=self.capid_var, width=20)
        capid_entry.grid(row=2, column=1, sticky='w')

        # trace changes: if user types CAP ID, try to fill Name
        try:
            self.capid_var.trace_add('write', lambda *a: self._on_capid_change())
        except Exception:
            self.capid_var.trace('w', lambda *a: self._on_capid_change())

        ttk.Label(self, text='Inspector (CAP ID):').grid(row=2, column=2, sticky='e')
        self.inspector_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.inspector_var, width=20).grid(row=2, column=3, sticky='w')

        row_idx = 4

        # Score control: group of 0-3 buttons
        COLORS = ['#d9534f', '#f0ad4e', '#5bc0de', '#5cb85c']  # red, orange, blue, green

        class ScoreControl:
            def __init__(self, parent, initial=0):
                self.var = tk.IntVar(value=initial)
                self.frame = ttk.Frame(parent)
                self.buttons = {}
                for i in range(4):
                    b = tk.Button(self.frame, text=str(i), width=3, relief='raised', command=lambda v=i: self.set(v))
                    b.pack(side='left', padx=2)
                    self.buttons[i] = b
                self._apply_highlight()

            def set(self, v):
                try:
                    self.var.set(int(v))
                except Exception:
                    self.var.set(0)
                self._apply_highlight()

            def get(self):
                return int(self.var.get())

            def _apply_highlight(self):
                sel = self.var.get()
                for i, btn in self.buttons.items():
                    if i == sel:
                        # selected color and sunken relief
                        btn.config(bg=COLORS[i], relief='sunken')
                    else:
                        # default
                        btn.config(bg='SystemButtonFace', relief='raised')

        # Section helper
        def make_section(title_text, items):
            nonlocal row_idx
            section_lbl = ttk.Label(self, text=title_text, font=tkfont.Font(weight='bold'))
            section_lbl.grid(row=row_idx, column=0, sticky='w', pady=(10,2))
            row_idx += 1

            for label_text in items:
                lbl = ttk.Label(self, text=label_text + ':')
                lbl.grid(row=row_idx, column=0, sticky='e', padx=(0,6))
                control = ScoreControl(self, initial=2)
                control.frame.grid(row=row_idx, column=1, sticky='w')
                comment = ttk.Entry(self, width=56)
                comment.grid(row=row_idx, column=2, columnspan=2, sticky='w', padx=(8,0))
                row_idx += 1
                yield control, comment

        # Define sections and items
        self.inputs = []

        personal_items = ['Haircut', 'Cleanliness', 'Shave/Cosmetics']
        garments_items = ['Cleanliness', 'Press/Ironing', 'No loose strings/frays', 'Shirt tucked properly',
                          'Proper sizing/fit', 'No unauthorized bracelets', 'Sleeves rolled properly (cuff visible)', 'Undershirt correct (color/cut)']
        accouterments_items = ['Patches', 'Insignia', 'Ribbons/order', 'Gig line']
        footwear_items = ['Boot blousing', 'Shine / Cleanliness']
        military_items = ['Posture', 'Hands at seam', 'Focus / Bearing']

        # Personal Appearance
        for s, c in make_section('Personal Appearance', personal_items):
            self.inputs.append(('Personal Appearance', s, c))

        # Garments
        for s, c in make_section('Garments', garments_items):
            self.inputs.append(('Garments', s, c))

        # Accouterments
        for s, c in make_section('Accouterments', accouterments_items):
            self.inputs.append(('Accouterments', s, c))

        # Footwear
        for s, c in make_section('Footwear', footwear_items):
            self.inputs.append(('Footwear', s, c))

        # Military Bearing
        for s, c in make_section('Military Bearing', military_items):
            self.inputs.append(('Military Bearing', s, c))

        # Total, rating, signatures
        ttk.Label(self, text='Total Score:').grid(row=row_idx, column=0, sticky='e', pady=(10,2))
        self.total_var = tk.StringVar(value='0')
        ttk.Entry(self, textvariable=self.total_var, width=10, state='readonly').grid(row=row_idx, column=1, sticky='w')

        ttk.Label(self, text='Overall Rating:').grid(row=row_idx, column=2, sticky='e')
        self.rating_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.rating_var, width=30, state='readonly').grid(row=row_idx, column=3, sticky='w')
        row_idx += 1

        ttk.Label(self, text='Inspector Signature:').grid(row=row_idx, column=0, sticky='e', pady=(8,0))
        self.signature_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.signature_var, width=30).grid(row=row_idx, column=1, sticky='w', pady=(8,0))

        ttk.Label(self, text='Overall Comments:').grid(row=row_idx, column=2, sticky='e')
        self.overall_comments = ttk.Entry(self, width=35)
        self.overall_comments.grid(row=row_idx, column=3, sticky='w')
        row_idx += 1

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row_idx, column=0, columnspan=4, pady=(12,0))

        calc_btn = ttk.Button(btn_frame, text='Calculate Total', command=self.calculate_total)
        calc_btn.grid(row=0, column=0, padx=6)

        submit_btn = ttk.Button(btn_frame, text='Submit', command=self.submit)
        submit_btn.grid(row=0, column=1, padx=6)

        clear_btn = ttk.Button(btn_frame, text='Clear', command=self.clear_form)
        clear_btn.grid(row=0, column=2, padx=6)

        self.status_var = tk.StringVar()
        status = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w')
        status.grid(row=row_idx+1, column=0, columnspan=4, sticky='ew', pady=(8,0), ipady=4)
        # calculate initial totals based on default=2
        self.calculate_total()

    def calculate_total(self):
        try:
            total = 0
            for section, control, comment in self.inputs:
                v = int(control.get())
                total += v
            self.total_var.set(str(total))
            self.rating_var.set(compute_rating(total))
            self.status_var.set(f'Calculated total = {total}')
        except Exception:
            logging.exception('Error calculating total')
            messagebox.showerror('Error', 'Could not calculate total (see terminal).')

    def clear_form(self):
        self.name_var.set('')
        self.date_var.set(datetime.date.today().isoformat())
        self.capid_var.set('')
        self.inspector_var.set('')
        for section, control, comment in self.inputs:
            try:
                control.set(2)
            except Exception:
                try:
                    # fallback if control doesn't have set
                    control.var.set(2)
                except Exception:
                    pass
            comment.delete(0, 'end')
        self.total_var.set('0')
        self.rating_var.set('')
        self.signature_var.set('')
        self.overall_comments.delete(0, 'end')
        self.status_var.set('')

    def submit(self):
        # calculate totals first
        self.calculate_total()
        try:
            capid_text = self.capid_var.get().strip()
            if not capid_text.isdigit():
                messagebox.showerror('Validation', 'CAP ID must be numeric and present.')
                return
            capid = int(capid_text)

            # find cadet id
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            cur.execute('SELECT idcadet, cadet_fname, cadet_lname FROM cadet WHERE cadet_capid = %s', (capid,))
            cadet_row = cur.fetchone()
            if not cadet_row:
                messagebox.showerror('Not found', f'No cadet found with CAP ID {capid}.')
                conn.close()
                return
            cadet_id = cadet_row[0]

            total = int(self.total_var.get())
            rating = self.rating_var.get() or compute_rating(total)
            inspector_capid = int(self.inspector_var.get()) if self.inspector_var.get().strip().isdigit() else None
            inspection_date = self.date_var.get().strip() or datetime.date.today().isoformat()
            # combine comments
            comments_parts = []
            for section, control, comment in self.inputs:
                try:
                    v = control.get()
                except Exception:
                    v = '0'
                c = comment.get().strip()
                if c:
                    comments_parts.append(f'{section} - {c}')
            overall_comments = self.overall_comments.get().strip()
            if overall_comments:
                comments_parts.append('Overall: ' + overall_comments)
            comments_combined = ' | '.join(comments_parts)[:255]

            try:
                # insert aggregate inspection_score
                cur.execute('INSERT INTO inspection_score (inspection_score_category, inspection_score_score) VALUES (%s,%s)',
                            ('aggregate', total))
                score_id = cur.lastrowid

                # insert inspection
                cur.execute(
                    'INSERT INTO inspection (inspection_date, inspection_inspector_capid, inspection_total_score, inspection_rating, inspection_coments, inspection_score_idinspection_score) VALUES (%s,%s,%s,%s,%s,%s)',
                    (inspection_date, inspector_capid, total, rating, comments_combined, score_id)
                )
                inspection_id = cur.lastrowid

                # link cadet <-> inspection
                cur.execute('INSERT INTO cadet_has_inspection (cadet_idcadet, inspection_idinspection) VALUES (%s,%s)',
                            (cadet_id, inspection_id))

                conn.commit()
                messagebox.showinfo('Success', f'Inspection saved (id {inspection_id}).')
                self.status_var.set(f'Saved inspection id {inspection_id} for cadet id {cadet_id}')
                self.clear_form()
            except Exception:
                conn.rollback()
                logging.exception('Error saving inspection')
                messagebox.showerror('Database Error', 'Failed to save inspection (see terminal).')
            finally:
                conn.close()

        except Exception:
            logging.exception('Unexpected error on submit')
            messagebox.showerror('Error', 'Unexpected error (see terminal).')

    # --- autofill helpers -------------------------------------------------
    def _on_capid_change(self):
        if getattr(self, '_suppress_traces', False):
            return
        val = self.capid_var.get().strip()
        if not val or not val.isdigit():
            return
        capid = int(val)
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('SELECT cadet_fname, cadet_lname FROM cadet WHERE cadet_capid = %s', (capid,))
            row = cur.fetchone()
            if row:
                # prevent trace recursion while setting name
                try:
                    self._suppress_traces = True
                    fname, lname = row[0] or '', row[1] or ''
                    name = (fname + ' ' + lname).strip()
                    self.name_var.set(name)
                finally:
                    self._suppress_traces = False
        except Exception:
            logging.exception('Error looking up cadet by capid')
        finally:
            conn.close()

    def _on_name_change(self):
        if getattr(self, '_suppress_traces', False):
            return
        name = self.name_var.get().strip()
        if not name:
            return
        # attempt to split into first and last name; use first token as first name and last token as last name
        parts = name.split()
        if len(parts) == 0:
            return
        fname = parts[0]
        lname = parts[-1] if len(parts) > 1 else ''
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            # look for matching cadet by first and last name (case-insensitive)
            cur.execute('SELECT cadet_capid FROM cadet WHERE LOWER(cadet_fname) = LOWER(%s) AND LOWER(cadet_lname) = LOWER(%s) LIMIT 1', (fname, lname))
            row = cur.fetchone()
            if row:
                try:
                    self._suppress_traces = True
                    self.capid_var.set(str(row[0]))
                finally:
                    self._suppress_traces = False
        except Exception:
            logging.exception('Error looking up cadet by name')
        finally:
            conn.close()


def main():
    root = tk.Tk()
    root.title('Inspection Form')
    root.iconbitmap('my_icon.ico') 
    # make window taller and thinner
    root.geometry('800x950')
    root.minsize(480, 700)
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except Exception:
        pass
    app = InspectionForm(root)
    root.mainloop()


if __name__ == '__main__':
    main()
