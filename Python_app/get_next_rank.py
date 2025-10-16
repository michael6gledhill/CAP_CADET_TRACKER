# --- Requirements Editor GUI ---
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cadet_tracker',
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
        import tkinter as tk
        from tkinter import ttk, messagebox
        import mysql.connector
        from mysql.connector import Error

        DB_CONFIG = {
            'host': 'localhost',
            'user': 'Michael',
            'password': 'hogbog89',
            'database': 'cadet_tracker',
        }


        def get_connection():
            try:
                return mysql.connector.connect(**DB_CONFIG)
            except Error as e:
                messagebox.showerror('DB Error', f'Could not connect to DB:\n{e}')
                return None


        # Data helpers matching the provided DDL
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


        def fetch_requirements_for_rank(rank_id):
            """Return list of (requirement_id, requirement_name, description) linked to the rank."""
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


        def update_requirement(req_id, name, description):
            conn = get_connection()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                cur.execute('UPDATE requirement SET requirement_name=%s, description=%s WHERE requirement_id=%s', (name, description, req_id))
                conn.commit()
                return True
            except Error as e:
                messagebox.showerror('DB Error', f'Could not update requirement:\n{e}')
                return False
            finally:
                conn.close()


        def link_requirement_to_rank(rank_id, req_id):
            conn = get_connection()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                # avoid duplicate
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


        def unlink_requirement_from_rank(rank_id, req_id):
            conn = get_connection()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                cur.execute('DELETE FROM rank_has_requirement WHERE rank_rank_id=%s AND rank_requirement_requirement_id=%s', (rank_id, req_id))
                conn.commit()
                return True
            except Error as e:
                messagebox.showerror('DB Error', f'Could not unlink requirement from rank:\n{e}')
                return False
            finally:
                conn.close()


        try:
            from ui_theme import setup as theme_setup, apply_accent, enable_alt_row_colors
        except Exception:
            def theme_setup(_root, dark=False):
                return
            def apply_accent(_btn):
                return
            def enable_alt_row_colors(_tv):
                return

        class RankReqEditor(tk.Tk):
            def __init__(self):
                super().__init__()
                self.title('Rank Requirements')
                self.geometry('700x450')
                try:
                    theme_setup(self, dark=False)
                except Exception:
                    pass

                self.ranks = fetch_ranks()
                self.rank_map = {r[0]: r[1] for r in self.ranks}

                left = ttk.Frame(self)
                left.pack(side='left', fill='y', padx=12, pady=12)
                ttk.Label(left, text='Ranks').pack()
                self.rank_list = tk.Listbox(left, height=20, width=30)
                self.rank_list.pack(fill='y')
                for r in self.ranks:
                    self.rank_list.insert('end', f"{r[1]} (id {r[0]})")
                self.rank_list.bind('<<ListboxSelect>>', self.on_rank_select)

                right = ttk.Frame(self)
                right.pack(side='left', fill='both', expand=True, padx=12, pady=12)

                ttk.Label(right, text='Requirements linked to selected rank:').pack(anchor='w')
                self.req_tree = ttk.Treeview(right, columns=('id','name'), show='headings')
                self.req_tree.heading('id', text='ID')
                self.req_tree.heading('name', text='Name')
                self.req_tree.column('id', width=60, anchor='center')
                self.req_tree.pack(fill='both', expand=True)
                self.req_tree.bind('<<TreeviewSelect>>', self.on_req_select)

                form = ttk.Frame(right)
                form.pack(fill='x', pady=8)
                ttk.Label(form, text='Requirement Name:').grid(row=0, column=0, sticky='e')
                self.req_name = tk.StringVar()
                ttk.Entry(form, textvariable=self.req_name, width=60).grid(row=0, column=1, sticky='w')
                ttk.Label(form, text='Description:').grid(row=1, column=0, sticky='ne')
                self.req_desc = tk.Text(form, height=6, width=60)
                self.req_desc.grid(row=1, column=1, sticky='w')

                btnf = ttk.Frame(right)
                btnf.pack(pady=8)
                btn_create = ttk.Button(btnf, text='Create & Link', command=self.create_and_link)
                btn_create.pack(side='left', padx=6)
                try:
                    apply_accent(btn_create)
                except Exception:
                    pass
                btn_update = ttk.Button(btnf, text='Update Requirement', command=self.update_selected_req)
                btn_update.pack(side='left', padx=6)
                try:
                    apply_accent(btn_update)
                except Exception:
                    pass
                ttk.Button(btnf, text='Unlink', command=self.unlink_selected_req).pack(side='left', padx=6)
                ttk.Button(btnf, text='Refresh', command=self.refresh).pack(side='left', padx=6)

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
                self.clear_form()

            def on_req_select(self, *a):
                sel = self.req_tree.selection()
                if not sel:
                    return
                req_id = int(sel[0])
                # fetch full requirement row
                conn = get_connection()
                if not conn:
                    return
                try:
                    cur = conn.cursor()
                    cur.execute('SELECT requirement_id, requirement_name, description FROM requirement WHERE requirement_id=%s', (req_id,))
                    row = cur.fetchone()
                    if row:
                        self.req_name.set(row[1])
                        self.req_desc.delete('1.0', 'end')
                        if row[2]:
                            self.req_desc.insert('1.0', row[2])
                finally:
                    conn.close()

            def clear_form(self):
                self.req_name.set('')
                self.req_desc.delete('1.0', 'end')

            def create_and_link(self):
                sel = self.rank_list.curselection()
                if not sel:
                    messagebox.showerror('Error', 'Select a rank first')
                    return
                rank_id = self.ranks[sel[0]][0]
                name = self.req_name.get().strip()
                desc = self.req_desc.get('1.0', 'end').strip()
                if not name:
                    messagebox.showerror('Validation', 'Requirement name required')
                    return
                req_id = create_requirement(name, desc)
                if req_id:
                    if link_requirement_to_rank(rank_id, req_id):
                        messagebox.showinfo('Done', f'Created requirement {req_id} and linked to rank {rank_id}')
                        self.load_requirements(rank_id)

            def update_selected_req(self):
                sel = self.req_tree.selection()
                if not sel:
                    messagebox.showerror('Error', 'Select a requirement first')
                    return
                req_id = int(sel[0])
                name = self.req_name.get().strip()
                desc = self.req_desc.get('1.0', 'end').strip()
                if not name:
                    messagebox.showerror('Validation', 'Requirement name required')
                    return
                if update_requirement(req_id, name, desc):
                    messagebox.showinfo('Done', 'Requirement updated')
                    # refresh display
                    sel_rank = self.rank_list.curselection()
                    if sel_rank:
                        self.load_requirements(self.ranks[sel_rank[0]][0])

            def unlink_selected_req(self):
                sel = self.req_tree.selection()
                if not sel:
                    messagebox.showerror('Error', 'Select a requirement first')
                    return
                req_id = int(sel[0])
                sel_rank = self.rank_list.curselection()
                if not sel_rank:
                    return
                rank_id = self.ranks[sel_rank[0]][0]
                if messagebox.askyesno('Confirm', 'Unlink requirement from rank?'):
                    if unlink_requirement_from_rank(rank_id, req_id):
                        messagebox.showinfo('Done', 'Unlinked')
                        self.load_requirements(rank_id)

            def refresh(self):
                self.ranks = fetch_ranks()
                self.rank_map = {r[0]: r[1] for r in self.ranks}
                self.rank_list.delete(0, 'end')
                for r in self.ranks:
                    self.rank_list.insert('end', f"{r[1]} (id {r[0]})")
                if self.ranks:
                    self.rank_list.selection_set(0)
                    self.on_rank_select()


        def ReqEditor():
            try:
                RankReqEditor()
            except Exception:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror('Error', 'Requirements editor not available.')
                root.mainloop()


        if __name__ == '__main__':
            ReqEditor()
