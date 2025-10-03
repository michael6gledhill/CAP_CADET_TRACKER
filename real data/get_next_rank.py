
# --- Requirements Editor GUI ---
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cap_cadet_tracker_2.0',
}

def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        messagebox.showerror('DB Error', f'Could not connect to DB:\n{e}')
        return None

def fetch_ranks():
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('SELECT idrank, rank_name FROM `rank` ORDER BY idrank ASC')
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()

def fetch_req_id_for_rank(rank_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute('SELECT promtion_reqwierment_idpromtion_reqwierment FROM rank_has_promtion_reqwierment WHERE rank_idrank = %s', (rank_id,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def fetch_req(req_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute('''SELECT idpromtion_reqwierment, leadership_task_1, leadership_task_2, aerospace_req, fitness_req, character_req, special_req, honor_credit, goal_date, promotion_effective_date FROM promtion_reqwierment WHERE idpromtion_reqwierment = %s''', (req_id,))
        return cur.fetchone()
    finally:
        conn.close()

def save_req(req_id, fields):
    conn = get_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute('''UPDATE promtion_reqwierment SET leadership_task_1=%s, leadership_task_2=%s, aerospace_req=%s, fitness_req=%s, character_req=%s, special_req=%s, honor_credit=%s, goal_date=%s, promotion_effective_date=%s WHERE idpromtion_reqwierment=%s''', (*fields, req_id))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror('DB Error', f'Could not save requirements: {e}')
        return False
    finally:
        conn.close()

class ReqEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Rank Requirements Editor')
        self.geometry('600x400')
        self.ranks = fetch_ranks()
        self.rank_map = {str(r[0]): r[1] for r in self.ranks}
        self.rank_ids = [str(r[0]) for r in self.ranks]
        self.selected_rank_id = tk.StringVar()
        self.selected_rank_id.trace('w', self.on_rank_change)

        ttk.Label(self, text='Select Rank:').pack(pady=(12,4))
        self.rank_cb = ttk.Combobox(self, values=[f"{r[1]} (id {r[0]})" for r in self.ranks], state='readonly', width=40, textvariable=self.selected_rank_id)
        self.rank_cb.pack()

        # now 9 fields per your SQL schema
        self.fields = [tk.StringVar() for _ in range(9)]
        labels = ['Leadership Task 1', 'Leadership Task 2', 'Aerospace', 'Fitness', 'Character', 'Special Requirement', 'Honor Credit', 'Goal Date', 'Promotion Effective Date']
        self.entries = []
        for i, label in enumerate(labels):
            frame = ttk.Frame(self)
            frame.pack(fill='x', padx=24, pady=2)
            ttk.Label(frame, text=label+':', width=22).pack(side='left')
            entry = ttk.Entry(frame, textvariable=self.fields[i], width=40)
            entry.pack(side='left', fill='x', expand=True)
            self.entries.append(entry)

        btnf = ttk.Frame(self)
        btnf.pack(pady=16)
        ttk.Button(btnf, text='Save', command=self.save).pack(side='left', padx=8)
        ttk.Button(btnf, text='Create & Link', command=self.create_and_link).pack(side='left', padx=8)
        ttk.Button(btnf, text='Refresh', command=self.refresh).pack(side='left', padx=8)

        # set combobox values and default selection
        self.rank_cb['values'] = [f"{r[1]} (id {r[0]})" for r in self.ranks]
        if self.rank_ids:
            self.rank_cb.current(0)
            self.selected_rank_id.set(self.rank_ids[0])

    def on_rank_change(self, *a):
        # selected_rank_id stores the rank id string; some combobox interactions set by index
        rid = self.selected_rank_id.get()
        if not rid:
            # try to derive from combobox current selection
            idx = self.rank_cb.current()
            if idx >= 0 and idx < len(self.ranks):
                rid = str(self.ranks[idx][0])
                self.selected_rank_id.set(rid)
            else:
                return
        req_id = fetch_req_id_for_rank(rid)
        if not req_id:
            for f in self.fields:
                f.set('')
            return
        req = fetch_req(req_id)
        if req:
            # req tuple: id, leadership_task_1, leadership_task_2, aerospace_req, fitness_req, character_req, special_req, honor_credit, goal_date, promotion_effective_date
            for i in range(9):
                self.fields[i].set(req[i+1] or '')
        else:
            for f in self.fields:
                f.set('')

    def save(self):
        rid = self.selected_rank_id.get()
        if not rid:
            # fall back to combobox selection
            idx = self.rank_cb.current()
            if idx >= 0 and idx < len(self.ranks):
                rid = str(self.ranks[idx][0])
            else:
                return
        req_id = fetch_req_id_for_rank(rid)
        vals = [f.get() for f in self.fields]
        if not req_id:
            # create a new requirement row and link it
            req_id = self.create_req_row(vals)
            if not req_id:
                return
            self.link_req_to_rank(rid, req_id)
        if save_req(req_id, vals):
            messagebox.showinfo('Saved', 'Requirements updated.')

    def refresh(self):
        self.ranks = fetch_ranks()
        self.rank_map = {str(r[0]): r[1] for r in self.ranks}
        self.rank_ids = [str(r[0]) for r in self.ranks]
        self.rank_cb['values'] = [f"{r[1]} (id {r[0]})" for r in self.ranks]
        if self.rank_ids:
            self.rank_cb.current(0)
            self.selected_rank_id.set(self.rank_ids[0])

    def create_req_row(self, fields):
        """Insert a new promtion_reqwierment row and return its id."""
        conn = get_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor()
            cur.execute('''INSERT INTO promtion_reqwierment (leadership_task_1, leadership_task_2, aerospace_req, fitness_req, character_req, special_req, honor_credit, goal_date, promotion_effective_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (*fields,))
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            messagebox.showerror('DB Error', f'Could not create requirement row: {e}')
            return None
        finally:
            conn.close()

    def link_req_to_rank(self, rank_id, req_id):
        conn = get_connection()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            # ensure no duplicate
            cur.execute('SELECT 1 FROM rank_has_promtion_reqwierment WHERE rank_idrank = %s AND promtion_reqwierment_idpromtion_reqwierment = %s', (rank_id, req_id))
            if not cur.fetchone():
                cur.execute('INSERT INTO rank_has_promtion_reqwierment (rank_idrank, promtion_reqwierment_idpromtion_reqwierment) VALUES (%s,%s)', (rank_id, req_id))
                conn.commit()
            return True
        except Exception as e:
            messagebox.showerror('DB Error', f'Could not link requirement to rank: {e}')
            return False
        finally:
            conn.close()

    def create_and_link(self):
        idx = self.rank_cb.current()
        if idx < 0 or idx >= len(self.ranks):
            messagebox.showerror('Error', 'Select a rank first')
            return
        rank_id = self.ranks[idx][0]
        vals = [f.get() for f in self.fields]
        req_id = self.create_req_row(vals)
        if req_id:
            if self.link_req_to_rank(rank_id, req_id):
                messagebox.showinfo('Done', f'Created requirement id {req_id} and linked to rank {rank_id}')


if __name__ == '__main__':
    app = ReqEditor()
    app.mainloop()
