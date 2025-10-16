import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging
try:
    # Theming helpers (safe no-ops if module not present)
    from ui_theme import apply_accent, enable_alt_row_colors
except Exception:
    def apply_accent(_btn):
        return
    def enable_alt_row_colors(_tv):
        return

# reuse DB helper from add_cadet if available
try:
    from add_cadet import get_connection
except Exception:
    # fallback - simple local connector if import fails; inform user when used
    import mysql.connector
    from mysql.connector import Error

    DB_CONFIG = {
        'host': 'localhost',
        'user': 'Michael',
        'password': 'hogbog89',
        'database': 'cap_cadet_tracker_3.0',
    }



    def get_connection():
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Exception as e:
            logging.exception('DB connect failed')
            messagebox.showerror('DB Error', f'Could not connect to DB:\n{e}')
            return None


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


class Dashboard(ttk.Frame):
    """Main dashboard: 2x2 grid of widgets.

    Top-left: cadet list
    Top-right: inspections for selected cadet (editable)
    Bottom-right: cadet profile (editable)
    Bottom-left: promotion requirements and completion status
    """

    def __init__(self, master):
        super().__init__(master, padding=8)
        self.master = master
        self.pack(fill='both', expand=True)
        self.selected_cadet = None
        self._cadets = []
        self.requirements_state = {}
        self._build_ui()
        self.load_cadets()

    def _build_ui(self):
        # layout a 2x2 grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top-left: cadet list
        left_top = ttk.Labelframe(self, text='Cadets')
        left_top.grid(row=0, column=0, sticky='nsew', padx=6, pady=6)
        left_top.rowconfigure(1, weight=1)

        search_frame = ttk.Frame(left_top)
        search_frame.grid(row=0, column=0, sticky='ew', padx=6, pady=(6,0))
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text='Search:').grid(row=0, column=0, sticky='w')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky='ew', padx=(6,0))
        search_entry.bind('<Return>', lambda e: self.load_cadets())

        self.cadet_list = tk.Listbox(left_top)
        self.cadet_list.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)
        self.cadet_list.bind('<<ListboxSelect>>', lambda e: self.on_cadet_select())

        # Top-right: inspections
        right_top = ttk.Labelframe(self, text='Inspections')
        right_top.grid(row=0, column=1, sticky='nsew', padx=6, pady=6)
        right_top.rowconfigure(0, weight=1)

        cols = ('id', 'date', 'score', 'rating', 'comments')
        self.inspection_tv = ttk.Treeview(right_top, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            self.inspection_tv.heading(c, text=c.title())
        self.inspection_tv.grid(row=0, column=0, sticky='nsew')
        right_top.columnconfigure(0, weight=1)
        right_top.rowconfigure(0, weight=1)

        it_btn_frame = ttk.Frame(right_top)
        it_btn_frame.grid(row=1, column=0, sticky='ew', pady=(6,0))
        btn_refresh = ttk.Button(it_btn_frame, text='Refresh', command=self.load_inspections)
        btn_refresh.grid(row=0, column=0, padx=4)
        btn_edit = ttk.Button(it_btn_frame, text='Edit', command=self.edit_inspection)
        btn_edit.grid(row=0, column=1, padx=4)
        btn_delete = ttk.Button(it_btn_frame, text='Delete', command=self.delete_inspection)
        btn_delete.grid(row=0, column=2, padx=4)
        # Accent the primary action (Edit)
        try:
            apply_accent(btn_edit)
        except Exception:
            pass
        try:
            # import here to avoid a hard dependency if reports.py missing
            from reports import ReportForm
            btn_report = ttk.Button(it_btn_frame, text='Report', command=lambda: ReportForm(self.master, selected_cadet=self.selected_cadet))
            btn_report.grid(row=0, column=3, padx=4)
            try:
                apply_accent(btn_report)
            except Exception:
                pass
        except Exception:
            # if the module isn't present, just leave out the button
            pass

        # Bottom-left: requirements
        left_bottom = ttk.Labelframe(self, text='Promotion Requirements')
        left_bottom.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)
        left_bottom.rowconfigure(0, weight=1)
        self.req_canvas = tk.Canvas(left_bottom)
        self.req_frame = ttk.Frame(self.req_canvas)
        vsb = ttk.Scrollbar(left_bottom, orient='vertical', command=self.req_canvas.yview)
        self.req_canvas.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky='ns')
        self.req_canvas.grid(row=0, column=0, sticky='nsew')
        self.req_canvas.create_window((0,0), window=self.req_frame, anchor='nw')
        self.req_frame.bind('<Configure>', lambda e: self.req_canvas.configure(scrollregion=self.req_canvas.bbox('all')))

        # Bottom-right: profile
        right_bottom = ttk.Labelframe(self, text='Profile')
        right_bottom.grid(row=1, column=1, sticky='nsew', padx=6, pady=6)
        right_bottom.columnconfigure(1, weight=1)

        ttk.Label(right_bottom, text='CAP ID:').grid(row=0, column=0, sticky='e')
        self.profile_capid = tk.StringVar()
        capid_entry = ttk.Entry(right_bottom, textvariable=self.profile_capid)
        capid_entry.grid(row=0, column=1, sticky='w')
        try:
            self.profile_capid.trace_add('write', lambda *a: self._on_profile_capid_change())
        except Exception:
            self.profile_capid.trace('w', lambda *a: self._on_profile_capid_change())

        ttk.Label(right_bottom, text='First name:').grid(row=1, column=0, sticky='e')
        self.profile_fname = tk.StringVar()
        fname_entry = ttk.Entry(right_bottom, textvariable=self.profile_fname)
        fname_entry.grid(row=1, column=1, sticky='ew')
        try:
            self.profile_fname.trace_add('write', lambda *a: self.update_email())
        except Exception:
            self.profile_fname.trace('w', lambda *a: self.update_email())

        ttk.Label(right_bottom, text='Last name:').grid(row=2, column=0, sticky='e')
        self.profile_lname = tk.StringVar()
        lname_entry = ttk.Entry(right_bottom, textvariable=self.profile_lname)
        lname_entry.grid(row=2, column=1, sticky='ew')
        try:
            self.profile_lname.trace_add('write', lambda *a: self.update_email())
        except Exception:
            self.profile_lname.trace('w', lambda *a: self.update_email())

        ttk.Label(right_bottom, text='Email:').grid(row=3, column=0, sticky='e')
        self.profile_email = tk.StringVar()
        ttk.Entry(right_bottom, textvariable=self.profile_email).grid(row=3, column=1, sticky='ew')

        # additional fields: phone, birthday, rank, flight, line position, staff position
        ttk.Label(right_bottom, text='Phone:').grid(row=4, column=0, sticky='e')
        self.profile_phone = tk.StringVar()
        ttk.Entry(right_bottom, textvariable=self.profile_phone).grid(row=4, column=1, sticky='ew')

        ttk.Label(right_bottom, text='Birthday:').grid(row=5, column=0, sticky='e')
        self.profile_birthday = tk.StringVar()
        ttk.Entry(right_bottom, textvariable=self.profile_birthday).grid(row=5, column=1, sticky='ew')

        ttk.Label(right_bottom, text='Rank:').grid(row=6, column=0, sticky='e')
        self.rank_var = tk.StringVar()
        self.rank_cb = ttk.Combobox(right_bottom, textvariable=self.rank_var, state='readonly', width=36)
        self.rank_cb.grid(row=6, column=1, sticky='ew')

        ttk.Label(right_bottom, text='Line Position:').grid(row=7, column=0, sticky='e')
        self.linepos_var = tk.StringVar()
        self.linepos_cb = ttk.Combobox(right_bottom, textvariable=self.linepos_var, state='readonly', width=36)
        self.linepos_cb.grid(row=7, column=1, sticky='ew')

        ttk.Label(right_bottom, text='Staff Position:').grid(row=8, column=0, sticky='e')
        self.staffpos_var = tk.StringVar()
        self.staffpos_cb = ttk.Combobox(right_bottom, textvariable=self.staffpos_var, state='readonly', width=36)
        self.staffpos_cb.grid(row=8, column=1, sticky='ew')

        profile_btns = ttk.Frame(right_bottom)
        profile_btns.grid(row=9, column=0, columnspan=2, pady=(8,0))
        btn_save_profile = ttk.Button(profile_btns, text='Save Profile', command=self.save_profile)
        btn_save_profile.grid(row=0, column=0, padx=6)
        try:
            apply_accent(btn_save_profile)
        except Exception:
            pass
        ttk.Button(profile_btns, text='Refresh', command=self.load_profile).grid(row=0, column=1, padx=6)

        # load lookup lists for comboboxes
        self._load_lookups()

    # ---------------- DB interactions and UI callbacks ------------------
    def load_cadets(self):
        """Load cadets into the left list, optionally filtered by search."""
        self.cadet_list.delete(0, 'end')
        term = self.search_var.get().strip()
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            if term:
                like = '%' + term + '%'
                cur.execute('SELECT cadet_id, cap_id, first_name, last_name FROM cadet WHERE CONCAT(first_name, " ", last_name) LIKE %s OR cap_id LIKE %s ORDER BY last_name, first_name', (like, like))
            else:
                cur.execute('SELECT cadet_id, cap_id, first_name, last_name FROM cadet ORDER BY last_name, first_name')
            rows = cur.fetchall()
            self._cadets = rows
            for r in rows:
                display = f"{r[2]} {r[3]} ({r[1]})"
                self.cadet_list.insert('end', display)
        except Exception:
            logging.exception('Error loading cadets')
            messagebox.showerror('DB Error', 'Could not load cadets (see terminal).')
        finally:
            conn.close()

    def _load_lookups(self):
        """Load lookup lists for ranks, flights, line positions and staff positions into comboboxes.

        This version uses smaller helper fetchers and stores id->name maps and id lists so
        selections can be resolved reliably by id instead of parsing label text.
        """
        try:
            # ranks
            try:
                cur_conn = get_connection()
                if not cur_conn:
                    return
                cur = cur_conn.cursor()
                cur.execute('SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC')
                ranks = cur.fetchall()
            except Exception:
                logging.exception('Error fetching ranks')
                ranks = []
            finally:
                try:
                    cur_conn.close()
                except Exception:
                    pass

            self._rank_map = {r[0]: r[1] for r in ranks}
            self._rank_ids = [r[0] for r in ranks]
            self.rank_cb['values'] = [r[1] or f'Rank {r[0]}' for r in ranks]

            # positions (use the position table, split by 'line' flag like add_cadet.py)
            try:
                pos_conn = get_connection()
                positions = []
                if pos_conn:
                    try:
                        cur = pos_conn.cursor()
                        # try to include the 'line' column if present to allow categorization
                        try:
                            cur.execute('SELECT position_id, position_name, line, level FROM `position` ORDER BY position_id')
                            positions = cur.fetchall()
                        except Exception:
                            # fallback to older schema without 'line' flag
                            cur.execute('SELECT position_id, position_name, level FROM `position` ORDER BY position_id')
                            rows = cur.fetchall()
                            # normalize to (id, name, None)
                            positions = [(r[0], r[1], None) for r in rows]
                    finally:
                        try:
                            pos_conn.close()
                        except Exception:
                            pass
                else:
                    positions = []
            except Exception:
                logging.exception('Error fetching positions')
                positions = []

            # Split positions into line (line=1) and support (line!=1) like add_cadet.py
            line_positions = [p for p in positions if (p[2] if len(p) > 2 else None) == 1]
            support_positions = [p for p in positions if (p[2] if len(p) > 2 else None) != 1]
            
            # Store all positions for mapping
            self._position_map = {r[0]: r[1] for r in positions}
            self._position_ids = [r[0] for r in positions]
            
            # Line positions
            self._linepos_ids = [r[0] for r in line_positions]
            self.linepos_cb['values'] = [r[1] or f'Position {r[0]}' for r in line_positions]
            
            # Support positions
            self._staffpos_ids = [r[0] for r in support_positions]
            self.staffpos_cb['values'] = [r[1] or f'Position {r[0]}' for r in support_positions]

            # set defaults if available
            if self.rank_cb['values']:
                try:
                    self.rank_cb.current(0)
                except Exception:
                    pass
            if self.linepos_cb['values']:
                try:
                    self.linepos_cb.current(0)
                except Exception:
                    pass
            if self.staffpos_cb['values']:
                try:
                    self.staffpos_cb.current(0)
                except Exception:
                    pass
        except Exception:
            logging.exception('Unexpected error in _load_lookups')

    def on_cadet_select(self):
        sel = self.cadet_list.curselection()
        if not sel:
            return
        idx = sel[0]
        row = self._cadets[idx]
        # idcadet, capid, fname, lname
        self.selected_cadet = (row[0], row[1], row[2], row[3])
        self.load_inspections()
        self.load_profile()
        self.load_requirements()

    # ---------------- lookup helper methods ----------------
    def fetch_flights(self):
        # flights table not present in new schema; return empty to keep callers safe
        return []

    def fetch_line_positions(self):
        # legacy line_position table replaced by `position`. Return same as fetch_flights fallback
        return []

    def fetch_support_positions(self):
        # support_position table not present; return empty
        return []

    def fetch_ranks(self):
        conn = get_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute('SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC')
            return cur.fetchall()
        except Exception:
            logging.exception('Error fetching ranks')
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def fetch_cadet_ranks(self, cadet_id: int):
        conn = get_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute('SELECT rank_rank_id FROM rank_has_cadet WHERE cadet_cadet_id = %s', (cadet_id,))
            rows = cur.fetchall()
            return [r[0] for r in rows]
        except Exception:
            logging.exception('Error fetching cadet ranks')
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def fetch_cadet_by_capid(self, capid: int):
        conn = get_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth, join_date FROM cadet WHERE cap_id = %s', (capid,))
            return cur.fetchone()
        except Exception:
            logging.exception('Error fetching cadet by capid')
            return None
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ---------------- email generation and CAPID auto-fill ----------------
    def _clean_name(self, s: str) -> str:
        s = (s or "").strip().lower()
        import re
        return re.sub(r'[^a-z0-9_-]', '', s)

    def generate_email(self) -> str:
        fmt = "c_[fi][ln]@kywg.cap.gov"
        fname = self.profile_fname.get().strip()
        lname = self.profile_lname.get().strip()
        if not fname or not lname:
            return ""
        fi = self._clean_name(fname)[0] if self._clean_name(fname) else ''
        ln = self._clean_name(lname)
        return fmt.replace('[fi]', fi).replace('[ln]', ln)

    def update_email(self, *_):
        try:
            new_email = self.generate_email()
            current = self.profile_email.get().strip()
            if new_email and current != new_email:
                self.profile_email.set(new_email)
        except Exception:
            logging.exception('Error generating email')

    def _on_profile_capid_change(self, *_):
        # attempt to auto-fill when user types a numeric CAP ID
        val = self.profile_capid.get().strip()
        if not val or not val.isdigit():
            return
        try:
            capid = int(val)
        except Exception:
            return
        row = self.fetch_cadet_by_capid(capid)
        if row:
            # load into the profile editor
            try:
                self.selected_cadet = (row[0], row[1], row[2], row[3])
            except Exception:
                pass
            self.load_profile()

    def load_inspections(self):
        for i in self.inspection_tv.get_children():
            self.inspection_tv.delete(i)
        if not self.selected_cadet:
            return
        cadet_id = self.selected_cadet[0]
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            # Use uniform_inspection and aggregate scores from uniform_inspection_score
            cur.execute('''
                SELECT ui.inspection_id, ui.inspection_date, COALESCE(SUM(u.score),0) AS total_score, '' AS rating, ui.notes
                FROM uniform_inspection ui
                LEFT JOIN uniform_inspection_score u ON ui.inspection_id = u.uniform_inspection_inspection_id
                WHERE ui.cadet_cadet_id = %s
                GROUP BY ui.inspection_id
                ORDER BY ui.inspection_date DESC
            ''', (cadet_id,))
            rows = cur.fetchall()
            for r in rows:
                self.inspection_tv.insert('', 'end', values=(r[0], r[1], r[2], r[3], (r[4] or '')[:80]))
            try:
                enable_alt_row_colors(self.inspection_tv)
            except Exception:
                pass
        except Exception:
            logging.exception('Error loading inspections')
            messagebox.showerror('DB Error', 'Could not load inspections (see terminal).')
        finally:
            conn.close()

    def edit_inspection(self):
        sel = self.inspection_tv.selection()
        if not sel or not self.selected_cadet:
            return
        item = sel[0]
        vals = self.inspection_tv.item(item, 'values')
        insp_id = vals[0]
        # fetch full inspection row including linked inspection_score id
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            # Fetch inspection header and aggregate score from new schema
            cur.execute('''
                SELECT ui.inspection_date, ui.notes, COALESCE(SUM(u.score),0) AS total_score
                FROM uniform_inspection ui
                LEFT JOIN uniform_inspection_score u ON ui.inspection_id = u.uniform_inspection_inspection_id
                WHERE ui.inspection_id = %s
                GROUP BY ui.inspection_id
            ''', (insp_id,))
            row = cur.fetchone()
        except Exception:
            logging.exception('Error fetching inspection')
            messagebox.showerror('DB Error', 'Could not fetch inspection (see terminal).')
            conn.close()
            return

        # Build a full inspection-sheet editor (per-item controls) and allow editing personal info
        top = tk.Toplevel(self.master)
        top.title(f'Edit Inspection {insp_id}')
        top.geometry('760x820')

        # Personal info
        ttk.Label(top, text='Name:').grid(row=0, column=0, sticky='e')
        name_var = tk.StringVar()
        ttk.Entry(top, textvariable=name_var, width=36).grid(row=0, column=1, sticky='w')
        ttk.Label(top, text='CAP ID:').grid(row=0, column=2, sticky='e')
        capid_var = tk.StringVar()
        ttk.Entry(top, textvariable=capid_var, width=14).grid(row=0, column=3, sticky='w')

        ttk.Label(top, text='Date:').grid(row=1, column=0, sticky='e')
        date_var = tk.StringVar(value=str(row[0]) if row and row[0] else datetime.date.today().isoformat())
        ttk.Entry(top, textvariable=date_var).grid(row=1, column=1, sticky='w')
        ttk.Label(top, text='Inspector (CAP ID):').grid(row=1, column=2, sticky='e')
        inspector_var = tk.StringVar(value='')
        ttk.Entry(top, textvariable=inspector_var).grid(row=1, column=3, sticky='w')

        # Local ScoreControl
        COLORS = ['#d9534f', '#f0ad4e', '#5bc0de', '#5cb85c']

        class ScoreControl:
            def __init__(self, parent, initial=2):
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
                        btn.config(bg=COLORS[i], relief='sunken')
                    else:
                        btn.config(bg='SystemButtonFace', relief='raised')

        # sections/items
        personal_items = ['Haircut', 'Cleanliness', 'Shave/Cosmetics']
        garments_items = ['Cleanliness', 'Press/Ironing', 'No loose strings/frays', 'Shirt tucked properly',
                          'Proper sizing/fit', 'No unauthorized bracelets', 'Sleeves rolled properly (cuff visible)', 'Undershirt correct (color/cut)']
        accouterments_items = ['Patches', 'Insignia', 'Ribbons/order', 'Gig line']
        footwear_items = ['Boot blousing', 'Shine / Cleanliness']
        military_items = ['Posture', 'Hands at seam', 'Focus / Bearing']

        inputs = []
        r = 2

        def add_section(title_text, items):
            nonlocal r
            ttk.Label(top, text=title_text, font=('TkDefaultFont', 10, 'bold')).grid(row=r, column=0, sticky='w', pady=(8,2))
            r += 1
            for label_text in items:
                ttk.Label(top, text=label_text + ':').grid(row=r, column=0, sticky='e', padx=(0,6))
                control = ScoreControl(top, initial=2)
                control.frame.grid(row=r, column=1, sticky='w')
                comment = ttk.Entry(top, width=50)
                comment.grid(row=r, column=2, columnspan=2, sticky='w', padx=(8,0))
                inputs.append((label_text, control, comment))
                r += 1

        add_section('Personal Appearance', personal_items)
        add_section('Garments', garments_items)
        add_section('Accouterments', accouterments_items)
        add_section('Footwear', footwear_items)
        add_section('Military Bearing', military_items)

        # Attempt to load per-item scores/comments for this inspection and populate controls
        try:
            cur.execute('''
                SELECT i.item_name, u.score, u.comments
                FROM uniform_inspection_score u
                JOIN inspection_item i ON u.inspection_item_item_id = i.item_id
                WHERE u.uniform_inspection_inspection_id = %s
            ''', (insp_id,))
            score_rows = cur.fetchall()
            score_map = {r[0]: (r[1], r[2]) for r in score_rows}
            for label_text, control, comment in inputs:
                if label_text in score_map:
                    try:
                        control.set(int(score_map[label_text][0]) if score_map[label_text][0] is not None else 0)
                    except Exception:
                        logging.exception('Error setting control value for %s', label_text)
                    try:
                        comment.delete(0, 'end')
                        if score_map[label_text][1]:
                            comment.insert(0, score_map[label_text][1])
                    except Exception:
                        logging.exception('Error setting comment for %s', label_text)
            # recalc total/rating after populating per-item values
            calculate_total_local()
        except Exception:
            logging.exception('Could not load per-item scores for inspection %s', insp_id)

        total_var = tk.StringVar(value=str(row[2] if row and row[2] is not None else 0))
        rating_var = tk.StringVar(value='')
        comments_var = tk.StringVar(value=str(row[1] or ''))

        ttk.Label(top, text='Total Score:').grid(row=r, column=0, sticky='e')
        ttk.Entry(top, textvariable=total_var, width=10, state='readonly').grid(row=r, column=1, sticky='w')
        ttk.Label(top, text='Overall Rating:').grid(row=r, column=2, sticky='e')
        ttk.Entry(top, textvariable=rating_var, width=30, state='readonly').grid(row=r, column=3, sticky='w')
        r += 1

        ttk.Label(top, text='Overall Comments:').grid(row=r, column=0, sticky='e')
        ttk.Entry(top, textvariable=comments_var, width=60).grid(row=r, column=1, columnspan=3, sticky='w')
        r += 1

        def calculate_total_local():
            try:
                tot = 0
                for label_text, control, comment in inputs:
                    tot += int(control.get())
                total_var.set(str(tot))
                # compute rating mapping
                if tot >= 45:
                    rating = 'Excellent'
                elif tot >= 30:
                    rating = 'Meets Standard'
                elif tot >= 16:
                    rating = 'Needs Improvement'
                else:
                    rating = 'Unacceptable'
                rating_var.set(rating)
            except Exception:
                logging.exception('Error calculating local total')
                messagebox.showerror('Error', 'Could not calculate total')

        def do_save_full():
            # update cadet info if changed
            new_capid = capid_var.get().strip()
            new_name = name_var.get().strip()
            new_fname = ''
            new_lname = ''
            if new_name:
                parts = new_name.split()
                new_fname = parts[0]
                new_lname = parts[-1] if len(parts) > 1 else ''
            try:
                tot = int(total_var.get())
            except Exception:
                messagebox.showerror('Validation', 'Total score invalid')
                return
            new_rating = rating_var.get().strip()
            new_comments = comments_var.get().strip()
            new_date = date_var.get().strip() or None
            new_inspector = inspector_var.get().strip() or None

            try:
                # update cadet table if capid or name changed
                cur2 = conn.cursor()
                if new_capid or new_fname or new_lname:
                    cur2.execute('UPDATE cadet SET cap_id=%s, first_name=%s, last_name=%s WHERE cadet_id = %s', (new_capid or None, new_fname or None, new_lname or None, self.selected_cadet[0]))

                # update uniform_inspection header
                cur2.execute('UPDATE uniform_inspection SET inspection_date=%s, notes=%s WHERE inspection_id = %s', (new_date, new_comments, insp_id))

                # replace existing per-item scores for this inspection with the values from the inputs
                try:
                    # delete old scores
                    cur2.execute('DELETE FROM uniform_inspection_score WHERE uniform_inspection_inspection_id = %s', (insp_id,))
                    # for each input label, ensure an inspection_item exists and insert score row
                    for label_text, control, comment in inputs:
                        score_val = int(control.get()) if control else 0
                        comment_text = comment.get().strip() if comment else ''
                        # find or create inspection_item by name
                        cur2.execute('SELECT item_id FROM inspection_item WHERE item_name = %s LIMIT 1', (label_text,))
                        item_row = cur2.fetchone()
                        if item_row and item_row[0]:
                            item_id = item_row[0]
                        else:
                            cur2.execute('INSERT INTO inspection_item (item_name, description) VALUES (%s, %s)', (label_text, label_text))
                            item_id = cur2.lastrowid
                        cur2.execute('INSERT INTO uniform_inspection_score (score, comments, inspection_item_item_id, uniform_inspection_inspection_id) VALUES (%s,%s,%s,%s)', (score_val, comment_text, item_id, insp_id))
                except Exception:
                    logging.exception('Error saving per-item scores')

                conn.commit()
                messagebox.showinfo('Saved', 'Inspection and profile updated')
                top.destroy()
                self.load_inspections()
                self.load_profile()
            except Exception:
                conn.rollback()
                logging.exception('Error saving full inspection')
                messagebox.showerror('DB Error', 'Failed to save inspection (see terminal).')

        btnf = ttk.Frame(top)
        btnf.grid(row=r, column=0, columnspan=4, pady=(8,0))
        btn_calc = ttk.Button(btnf, text='Calculate Total', command=calculate_total_local)
        btn_calc.grid(row=0, column=0, padx=6)
        btn_save = ttk.Button(btnf, text='Save', command=do_save_full)
        btn_save.grid(row=0, column=1, padx=6)
        try:
            apply_accent(btn_save)
        except Exception:
            pass
        ttk.Button(btnf, text='Cancel', command=top.destroy).grid(row=0, column=2, padx=6)

        # preload name/capid from selected_cadet
        try:
            name_var.set(f"{self.selected_cadet[2]} {self.selected_cadet[3]}")
            capid_var.set(str(self.selected_cadet[1]))
        except Exception:
            pass

        # initial total/rating from fetched row
        try:
            total_var.set(str(row[2] if row and row[2] is not None else 0))
            rating_var.set(str(row[3] or ''))
            comments_var.set(str(row[4] or ''))
        except Exception:
            pass

        def on_close():
            try:
                conn.close()
            except Exception:
                pass
            top.destroy()

        top.protocol('WM_DELETE_WINDOW', on_close)

    def delete_inspection(self):
        sel = self.inspection_tv.selection()
        if not sel or not self.selected_cadet:
            return
        vals = self.inspection_tv.item(sel[0], 'values')
        insp_id = vals[0]
        if not messagebox.askyesno('Confirm', f'Delete inspection {insp_id}?'):
            return
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            # delete scores then inspection header in new schema
            cur.execute('DELETE FROM uniform_inspection_score WHERE uniform_inspection_inspection_id = %s', (insp_id,))
            cur.execute('DELETE FROM uniform_inspection WHERE inspection_id = %s', (insp_id,))
            conn.commit()
            self.load_inspections()
            messagebox.showinfo('Deleted', 'Inspection deleted')
        except Exception:
            conn.rollback()
            logging.exception('Error deleting inspection')
            messagebox.showerror('DB Error', 'Could not delete inspection (see terminal).')
        finally:
            conn.close()

    def load_profile(self):
        """Load profile for selected cadet and populate UI fields.

        Uses robust lookups to select combobox values by id rather than parsing text.
        """
        if not self.selected_cadet:
            return
        cadet_id = self.selected_cadet[0]

        # fetch cadet row
        row = self.fetch_cadet_by_capid(self.selected_cadet[1]) if self.selected_cadet and self.selected_cadet[1] else None
        # If fetch by capid didn't work (maybe capid changed), fetch by id directly
        if not row:
            conn = get_connection()
            if not conn:
                return
            try:
                cur = conn.cursor()
                cur.execute('SELECT cadet_id, cap_id, first_name, last_name, date_of_birth, join_date FROM cadet WHERE cadet_id = %s', (cadet_id,))
                row = cur.fetchone()
            except Exception:
                logging.exception('Error loading profile by id')
                messagebox.showerror('DB Error', 'Could not load profile (see terminal).')
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        if not row:
            return

        # populate fields
        try:
            self.profile_capid.set(str(row[1] or ''))
            self.profile_fname.set(row[2] or '')
            self.profile_lname.set(row[3] or '')
            # profile_email and phone no longer in new schema; clear or keep empty
            try:
                self.profile_email.set('')
            except Exception:
                pass
            try:
                self.profile_phone.set('')
            except Exception:
                pass
            # date_of_birth
            self.profile_birthday.set(row[4].isoformat() if isinstance(row[4], (datetime.date, datetime.datetime)) else (row[4] or ''))

            # select rank mapping (first rank if multiple)
            try:
                cadet_ranks = self.fetch_cadet_ranks(row[0])
                if cadet_ranks:
                    rank_id = cadet_ranks[0]
                    if hasattr(self, '_rank_ids') and rank_id in self._rank_ids:
                        pos = self._rank_ids.index(rank_id)
                        try:
                            self.rank_cb.current(pos)
                        except Exception:
                            pass
            except Exception:
                logging.exception('Error selecting rank')

            # select position mapping (first position if multiple)
            try:
                conn2 = get_connection()
                if conn2:
                    cur2 = conn2.cursor()
                    cur2.execute('SELECT position_position_id FROM position_has_cadet WHERE cadet_cadet_id = %s ORDER BY start_date DESC LIMIT 1', (row[0],))
                    r = cur2.fetchone()
                    if r and r[0] is not None:
                        pos_id = r[0]
                        # Check if it's a line position (line=1) or support position
                        # Try to set the appropriate combobox based on which list contains this position
                        if hasattr(self, '_linepos_ids') and pos_id in self._linepos_ids:
                            pos = self._linepos_ids.index(pos_id)
                            try:
                                self.linepos_cb.current(pos)
                            except Exception:
                                pass
                        elif hasattr(self, '_staffpos_ids') and pos_id in self._staffpos_ids:
                            pos = self._staffpos_ids.index(pos_id)
                            try:
                                self.staffpos_cb.current(pos)
                            except Exception:
                                pass
            except Exception:
                logging.exception('Error selecting position')
            finally:
                try:
                    conn2.close()
                except Exception:
                    pass
        except Exception:
            logging.exception('Error populating profile fields')

    def save_profile(self):
        if not self.selected_cadet:
            return
        cadet_id = self.selected_cadet[0]

        capid = self.profile_capid.get().strip()
        fname = self.profile_fname.get().strip()
        lname = self.profile_lname.get().strip()
        # email/phone removed from new schema; ignore
        birthday = self.profile_birthday.get().strip() or None

        # resolve selections to ids using loaded id lists
        sel_rank = None
        sel_linepos = None
        sel_staffpos = None

        try:
            if hasattr(self, '_rank_ids') and self.rank_cb.get():
                idx = list(self.rank_cb['values']).index(self.rank_cb.get())
                sel_rank = self._rank_ids[idx]
        except Exception:
            sel_rank = None

        try:
            if hasattr(self, '_linepos_ids') and self.linepos_cb.get():
                idx = list(self.linepos_cb['values']).index(self.linepos_cb.get())
                sel_linepos = self._linepos_ids[idx]
        except Exception:
            sel_linepos = None

        try:
            if hasattr(self, '_staffpos_ids') and self.staffpos_cb.get():
                idx = list(self.staffpos_cb['values']).index(self.staffpos_cb.get())
                sel_staffpos = self._staffpos_ids[idx]
        except Exception:
            sel_staffpos = None

        # validation
        if not capid or not fname or not lname:
            messagebox.showerror('Validation', 'CAP ID, first and last name required')
            return

        # birthday format check YYYY-MM-DD if provided
        if birthday:
            try:
                datetime.datetime.strptime(birthday, '%Y-%m-%d')
            except Exception:
                messagebox.showerror('Validation', 'Birthday must be YYYY-MM-DD')
                return

        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            # update cadet master row
            cur.execute('UPDATE cadet SET cap_id=%s, first_name=%s, last_name=%s, date_of_birth=%s WHERE cadet_id = %s', (capid or None, fname or None, lname or None, birthday, cadet_id))
            # update mappings inside transaction
            try:
                cur.execute('DELETE FROM rank_has_cadet WHERE cadet_cadet_id = %s', (cadet_id,))
                if sel_rank:
                    cur.execute('INSERT INTO rank_has_cadet (rank_rank_id, cadet_cadet_id, date_received) VALUES (%s,%s,NOW())', (sel_rank, cadet_id))

                cur.execute('DELETE FROM position_has_cadet WHERE cadet_cadet_id = %s', (cadet_id,))
                # Insert both line and support positions if selected
                if sel_linepos:
                    cur.execute('INSERT INTO position_has_cadet (position_position_id, cadet_cadet_id, start_date, end_date, notes) VALUES (%s,%s,NOW(), NULL, NULL)', (sel_linepos, cadet_id))
                if sel_staffpos:
                    cur.execute('INSERT INTO position_has_cadet (position_position_id, cadet_cadet_id, start_date, end_date, notes) VALUES (%s,%s,NOW(), NULL, NULL)', (sel_staffpos, cadet_id))
            except Exception:
                logging.exception('Error updating mappings, rolling back inner changes')
                conn.rollback()
                messagebox.showerror('DB Error', 'Failed to update related mappings (see terminal).')
                return

            conn.commit()
            messagebox.showinfo('Saved', 'Profile updated')
            self.load_cadets()
            self.load_profile()
        except Exception:
            conn.rollback()
            logging.exception('Error saving profile')
            messagebox.showerror('DB Error', 'Could not save profile (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass


    def load_requirements(self):
        # Clear previous UI
        for child in self.req_frame.winfo_children():
            child.destroy()
        if not self.selected_cadet:
            return
        cadet_id = self.selected_cadet[0]

        # Determine next rank for this cadet using rank_order
        next_rank_id = None
        next_rank_name = None
        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                # find the cadet's highest current rank_order (if any)
                cur.execute('''
                    SELECT r.rank_order
                    FROM rank_has_cadet rh
                    JOIN `rank` r ON rh.rank_rank_id = r.rank_id
                    WHERE rh.cadet_cadet_id = %s
                    ORDER BY r.rank_order DESC LIMIT 1
                ''', (cadet_id,))
                rowr = cur.fetchone()
                if rowr and rowr[0] is not None:
                    current_order = int(rowr[0])
                    cur.execute('SELECT rank_id, rank_name FROM `rank` WHERE rank_order > %s ORDER BY rank_order ASC LIMIT 1', (current_order,))
                    nr = cur.fetchone()
                    if nr:
                        next_rank_id = int(nr[0])
                        next_rank_name = nr[1]
                else:
                    # no current rank, offer the lowest rank as next target
                    cur.execute('SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC LIMIT 1')
                    nr = cur.fetchone()
                    if nr:
                        next_rank_id = int(nr[0])
                        next_rank_name = nr[1]
            except Exception:
                logging.exception('Error determining next rank')
            finally:
                conn.close()

        if not next_rank_id:
            ttk.Label(self.req_frame, text='No promotion target found for this cadet.').grid(row=0, column=0, sticky='w', pady=4)
            return

        # Fetch requirements linked to next rank
        tasks = []  # list of (requirement_id, requirement_name)
        conn2 = get_connection()
        if conn2:
            try:
                cur2 = conn2.cursor()
                cur2.execute('''
                    SELECT req.requirement_id, req.requirement_name
                    FROM rank_has_requirement rr
                    JOIN requirement req ON rr.rank_requirement_requirement_id = req.requirement_id
                    WHERE rr.rank_rank_id = %s
                    ORDER BY req.requirement_id
                ''', (next_rank_id,))
                rows = cur2.fetchall()
                for r in rows:
                    tasks.append((r[0], r[1]))
            except Exception:
                logging.exception('Could not read requirements for next rank')
            finally:
                conn2.close()

        if not tasks:
            label = f'No requirements defined for next promotion (rank id {next_rank_id}'
            if next_rank_name:
                label += f': {next_rank_name}'
            label += ').'
            ttk.Label(self.req_frame, text=label).grid(row=0, column=0, sticky='w', pady=4)
            return

        # load completed requirements for this cadet
        completed = set()
        conn3 = get_connection()
        if conn3:
            try:
                cur3 = conn3.cursor()
                cur3.execute('SELECT requirement_requirement_id, date_completed FROM cadet_has_rank_requirement WHERE cadet_cadet_id = %s', (cadet_id,))
                rows = cur3.fetchall()
                for req_id, date_completed in rows:
                    completed.add(req_id)
            except Exception:
                logging.exception('Could not read cadet_has_rank_requirement')
            finally:
                conn3.close()

        for idx, (req_id, text) in enumerate(tasks):
            var = tk.BooleanVar(value=(req_id in completed))
            cb = ttk.Checkbutton(self.req_frame, text=text, variable=var, command=lambda r=req_id, v=var: self.toggle_requirement(r, v.get()))
            cb.grid(row=idx, column=0, sticky='w', pady=2)
            self.requirements_state[req_id] = var

    def toggle_requirement(self, req_id, value: bool):
        """Mark a requirement complete/incomplete for the selected cadet using cadet_has_rank_requirement."""
        if not self.selected_cadet:
            return
        cadet_id = self.selected_cadet[0]
        conn = get_connection()
        if not conn:
            # update in-memory state if DB not available
            if req_id in self.requirements_state:
                self.requirements_state[req_id].set(value)
            return
        try:
            cur = conn.cursor()
            if value:
                # insert completion row with today's date
                cur.execute('INSERT INTO cadet_has_rank_requirement (cadet_cadet_id, requirement_requirement_id, date_completed) VALUES (%s, %s, CURDATE())', (cadet_id, req_id))
            else:
                cur.execute('DELETE FROM cadet_has_rank_requirement WHERE cadet_cadet_id = %s AND requirement_requirement_id = %s', (cadet_id, req_id))
            conn.commit()
        except Exception:
            conn.rollback()
            logging.exception('Error toggling requirement')
            messagebox.showerror('DB Error', 'Could not update requirement (see terminal).')
        finally:
            conn.close()


def main():
    root = tk.Tk()
    root.title('Cadet Dashboard')
    root.geometry('1000x700')
    root.iconbitmap('my_icon.ico') 
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except Exception:
        pass
    app = Dashboard(root)
    root.mainloop()


if __name__ == '__main__':
    main()
