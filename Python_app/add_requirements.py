"""Add requirements and link them to ranks (GUI)

This provides a small Tk interface to create requirement rows and link/unlink them
to ranks. Also supports CSV import via file dialog (CSV columns: rank_identifier,requirement_name,description).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import mysql.connector
from mysql.connector import Error
try:
    from ui_theme import setup as theme_setup, apply_accent, enable_alt_row_colors
except Exception:
    def theme_setup(_root, dark=False):
        return
    def apply_accent(_btn):
        return
    def enable_alt_row_colors(_tv):
        return

DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cap_cadet_tracker_3.0',
}


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        messagebox.showerror('DB Error', f'Could not connect to DB:\n{e}')
        return None


def fetch_ranks():
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC')
        return cur.fetchall()
    finally:
        conn.close()


def create_requirement(name, description):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO requirement (requirement_name, description) VALUES (%s, %s)', (name, description))
        conn.commit()
        return cur.lastrowid
    except Error as e:
        messagebox.showerror('DB Error', f'Could not create requirement:\n{e}')
        return None
    finally:
        conn.close()


def link_requirement_to_rank(rank_id, req_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM rank_has_requirement WHERE rank_rank_id=%s AND rank_requirement_requirement_id=%s', (rank_id, req_id))
        if not cur.fetchone():
            cur.execute('INSERT INTO rank_has_requirement (rank_rank_id, rank_requirement_requirement_id) VALUES (%s, %s)', (rank_id, req_id))
            conn.commit()
        return True
    except Error as e:
        messagebox.showerror('DB Error', f'Could not link requirement to rank:\n{e}')
        return False
    finally:
        conn.close()


def find_rank_id_by_name(name):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute('SELECT rank_id FROM `rank` WHERE rank_name = %s', (name,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def fetch_requirements_for_rank(rank_id):
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT r.requirement_id, r.requirement_name, r.description
            FROM rank_has_requirement rr
            JOIN requirement r ON rr.rank_requirement_requirement_id = r.requirement_id
            WHERE rr.rank_rank_id = %s
            ORDER BY r.requirement_id
        ''', (rank_id,))
        return cur.fetchall()
    finally:
        conn.close()


def import_csv_file(path):
    try:
        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            items = []
            for row in reader:
                rank_idf = row.get('rank_identifier') or row.get('rank') or ''
                name = row.get('requirement_name') or row.get('name') or ''
                desc = row.get('description') or row.get('desc') or ''
                items.append((rank_idf.strip(), name.strip(), desc.strip()))
            return items
    except Exception as e:
        messagebox.showerror('CSV Error', f'Could not read CSV: {e}')
        return []


class AddReqGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Add Requirements to Rank')
        self.geometry('700x420')
        try:
            theme_setup(self, dark=False)
        except Exception:
            pass

        self.ranks = fetch_ranks()

        left = ttk.Frame(self)
        left.pack(side='left', fill='y', padx=10, pady=10)
        ttk.Label(left, text='Ranks').pack()
        self.rank_list = tk.Listbox(left, height=20, width=30)
        self.rank_list.pack(fill='y')
        for r in self.ranks:
            self.rank_list.insert('end', f"{r[1]} (id {r[0]})")
        self.rank_list.bind('<<ListboxSelect>>', self.on_rank_select)

        right = ttk.Frame(self)
        right.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        form = ttk.Frame(right)
        form.pack(fill='x')
        ttk.Label(form, text='Requirement name:').grid(row=0, column=0, sticky='e')
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=60).grid(row=0, column=1, sticky='w')
        ttk.Label(form, text='Description:').grid(row=1, column=0, sticky='ne')
        self.desc_text = tk.Text(form, height=6, width=60)
        self.desc_text.grid(row=1, column=1, sticky='w')

        btnf = ttk.Frame(right)
        btnf.pack(pady=8)
        btn_create = ttk.Button(btnf, text='Create & Link', command=self.create_and_link)
        btn_create.pack(side='left', padx=6)
        try:
            apply_accent(btn_create)
        except Exception:
            pass
        ttk.Button(btnf, text='Import CSV', command=self.import_csv).pack(side='left', padx=6)
        ttk.Button(btnf, text='Refresh Ranks', command=self.refresh).pack(side='left', padx=6)

        self.req_tree = ttk.Treeview(right, columns=('id','name'), show='headings')
        self.req_tree.heading('id', text='ID')
        self.req_tree.heading('name', text='Name')
        self.req_tree.column('id', width=60, anchor='center')
        self.req_tree.pack(fill='both', expand=True, pady=(8,0))
        try:
            enable_alt_row_colors(self.req_tree)
        except Exception:
            pass

        if self.ranks:
            self.rank_list.selection_set(0)
            self.on_rank_select()

    def on_rank_select(self, *a):
        sel = self.rank_list.curselection()
        if not sel:
            return
        idx = sel[0]
        rank_id = self.ranks[idx][0]
        self.load_requirements(rank_id)

    def load_requirements(self, rank_id):
        for i in self.req_tree.get_children():
            self.req_tree.delete(i)
        reqs = fetch_requirements_for_rank(rank_id)
        for r in reqs:
            self.req_tree.insert('', 'end', iid=str(r[0]), values=(r[0], r[1]))

    def create_and_link(self):
        sel = self.rank_list.curselection()
        if not sel:
            messagebox.showerror('Error', 'Select a rank first')
            return
        rank_id = self.ranks[sel[0]][0]
        name = self.name_var.get().strip()
        desc = self.desc_text.get('1.0', 'end').strip()
        if not name:
            messagebox.showerror('Validation', 'Requirement name required')
            return
        req_id = create_requirement(name, desc)
        if not req_id:
            return
        if link_requirement_to_rank(rank_id, req_id):
            messagebox.showinfo('Done', f'Created requirement {req_id} and linked to rank {rank_id}')
            self.load_requirements(rank_id)

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[('CSV files','*.csv'),('All files','*.*')])
        if not path:
            return
        items = import_csv_file(path)
        for rank_idf, name, desc in items:
            if not name:
                continue
            # resolve rank identifier
            try:
                rid = int(rank_idf)
            except Exception:
                rid = find_rank_id_by_name(rank_idf)
            if not rid:
                messagebox.showwarning('Warning', f'Could not resolve rank: {rank_idf}; skipping')
                continue
            req_id = create_requirement(name, desc)
            if req_id:
                link_requirement_to_rank(rid, req_id)
        messagebox.showinfo('Done', 'CSV import complete')
        # refresh current rank view
        sel = self.rank_list.curselection()
        if sel:
            self.load_requirements(self.ranks[sel[0]][0])

    def refresh(self):
        self.ranks = fetch_ranks()
        self.rank_list.delete(0, 'end')
        for r in self.ranks:
            self.rank_list.insert('end', f"{r[1]} (id {r[0]})")
        if self.ranks:
            self.rank_list.selection_set(0)
            self.on_rank_select()


def RequirementsApp():
    AddReqGUI()


if __name__ == '__main__':
    RequirementsApp()


class AddReqFrame(ttk.Frame):
    """Embeddable Requirements manager for use inside a Notebook tab."""
    def __init__(self, master=None):
        super().__init__(master)
        self.ranks = fetch_ranks()
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)

        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky='ns', padx=10, pady=10)
        ttk.Label(left, text='Ranks').pack()
        self.rank_list = tk.Listbox(left, height=20, width=30)
        self.rank_list.pack(fill='y')
        for r in self.ranks:
            self.rank_list.insert('end', f"{r[1]} (id {r[0]})")
        self.rank_list.bind('<<ListboxSelect>>', self.on_rank_select)

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        right.columnconfigure(1, weight=1)
        right.rowconfigure(2, weight=1)

        form = ttk.Frame(right)
        form.grid(row=0, column=0, sticky='ew')
        ttk.Label(form, text='Requirement name:').grid(row=0, column=0, sticky='e')
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=60).grid(row=0, column=1, sticky='w')
        ttk.Label(form, text='Description:').grid(row=1, column=0, sticky='ne')
        self.desc_text = tk.Text(form, height=6, width=60)
        self.desc_text.grid(row=1, column=1, sticky='w')

        btnf = ttk.Frame(right)
        btnf.grid(row=1, column=0, pady=8, sticky='w')
        btn_create = ttk.Button(btnf, text='Create & Link', command=self.create_and_link)
        btn_create.pack(side='left', padx=6)
        try:
            apply_accent(btn_create)
        except Exception:
            pass
        ttk.Button(btnf, text='Import CSV', command=self.import_csv).pack(side='left', padx=6)
        ttk.Button(btnf, text='Refresh Ranks', command=self.refresh).pack(side='left', padx=6)

        self.req_tree = ttk.Treeview(right, columns=('id','name'), show='headings')
        self.req_tree.heading('id', text='ID')
        self.req_tree.heading('name', text='Name')
        self.req_tree.column('id', width=60, anchor='center')
        self.req_tree.grid(row=2, column=0, sticky='nsew', pady=(8,0))
        try:
            enable_alt_row_colors(self.req_tree)
        except Exception:
            pass

        if self.ranks:
            self.rank_list.selection_set(0)
            self.on_rank_select()

    def on_rank_select(self, *a):
        sel = self.rank_list.curselection()
        if not sel:
            return
        idx = sel[0]
        rank_id = self.ranks[idx][0]
        self.load_requirements(rank_id)

    def load_requirements(self, rank_id):
        for i in self.req_tree.get_children():
            self.req_tree.delete(i)
        reqs = fetch_requirements_for_rank(rank_id)
        for r in reqs:
            self.req_tree.insert('', 'end', iid=str(r[0]), values=(r[0], r[1]))

    def create_and_link(self):
        sel = self.rank_list.curselection()
        if not sel:
            messagebox.showerror('Error', 'Select a rank first')
            return
        rank_id = self.ranks[sel[0]][0]
        name = self.name_var.get().strip()
        desc = self.desc_text.get('1.0', 'end').strip()
        if not name:
            messagebox.showerror('Validation', 'Requirement name required')
            return
        req_id = create_requirement(name, desc)
        if not req_id:
            return
        if link_requirement_to_rank(rank_id, req_id):
            messagebox.showinfo('Done', f'Created requirement {req_id} and linked to rank {rank_id}')
            self.load_requirements(rank_id)

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[('CSV files','*.csv'),('All files','*.*')])
        if not path:
            return
        items = import_csv_file(path)
        for rank_idf, name, desc in items:
            if not name:
                continue
            try:
                rid = int(rank_idf)
            except Exception:
                rid = find_rank_id_by_name(rank_idf)
            if not rid:
                messagebox.showwarning('Warning', f'Could not resolve rank: {rank_idf}; skipping')
                continue
            req_id = create_requirement(name, desc)
            if req_id:
                link_requirement_to_rank(rid, req_id)
        messagebox.showinfo('Done', 'CSV import complete')
        sel = self.rank_list.curselection()
        if sel:
            self.load_requirements(self.ranks[sel[0]][0])

    def refresh(self):
        self.ranks = fetch_ranks()
        self.rank_list.delete(0, 'end')
        for r in self.ranks:
            self.rank_list.insert('end', f"{r[1]} (id {r[0]})")
        if self.ranks:
            self.rank_list.selection_set(0)
            self.on_rank_select()
