"""
DB Browser GUI - lightweight explorer for the configured MySQL database.

Features:
- List all tables in the configured database.
- Show selected table's columns and a paginated/limited set of rows.
- Refresh table list and rows.
- Export current table page to CSV.

Usage: python db_browser.py

Requires: mysql-connector-python
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
import csv
import logging

DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cadet_tracker',
}
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        logging.exception('DB connect failed')
        messagebox.showerror('DB Error', f'Could not connect to DB:\n{e}')
        return None


class DBBrowser(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=8)
        self.master = master
        self.pack(fill='both', expand=True)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        # Left: tables list
        left = ttk.Labelframe(self, text='Tables')
        left.grid(row=0, column=0, sticky='nsw', padx=(0,8), pady=6)
        left.rowconfigure(0, weight=1)

        self.tbl_list = tk.Listbox(left, width=30, height=30)
        self.tbl_list.grid(row=0, column=0, sticky='ns')
        self.tbl_list.bind('<<ListboxSelect>>', lambda e: self.on_table_select())

        tbl_btns = ttk.Frame(left)
        tbl_btns.grid(row=1, column=0, pady=(6,0))
        ttk.Button(tbl_btns, text='Refresh', command=self.load_tables).grid(row=0, column=0, padx=4)
        ttk.Button(tbl_btns, text='Export CSV', command=self.export_current_page).grid(row=0, column=1, padx=4)

        # Right: table viewer
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        top_row = ttk.Frame(right)
        top_row.grid(row=0, column=0, sticky='ew')
        ttk.Label(top_row, text='Table:').grid(row=0, column=0, sticky='w')
        self.table_name_var = tk.StringVar()
        ttk.Label(top_row, textvariable=self.table_name_var, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=1, sticky='w', padx=(6,12))

        ttk.Label(top_row, text='Row limit:').grid(row=0, column=2, sticky='e')
        self.row_limit_var = tk.IntVar(value=100)
        ttk.Entry(top_row, textvariable=self.row_limit_var, width=6).grid(row=0, column=3, sticky='w')
        ttk.Button(top_row, text='Load rows', command=self.load_rows).grid(row=0, column=4, sticky='w', padx=(6,0))

        # columns and rows treeview
        cols_frame = ttk.Frame(right)
        cols_frame.grid(row=1, column=0, sticky='nsew', pady=(8,0))
        cols_frame.columnconfigure(0, weight=1)
        cols_frame.rowconfigure(0, weight=1)

        self.cols_tv = ttk.Treeview(cols_frame, columns=('col', 'type'), show='headings', height=6)
        self.cols_tv.heading('col', text='Column')
        self.cols_tv.heading('type', text='Type')
        self.cols_tv.grid(row=0, column=0, sticky='nsew')

        self.rows_tv = ttk.Treeview(right, show='headings')
        self.rows_tv.grid(row=2, column=0, sticky='nsew', pady=(8,0))

        rows_btns = ttk.Frame(right)
        rows_btns.grid(row=3, column=0, sticky='ew', pady=(6,0))
        ttk.Button(rows_btns, text='Refresh Rows', command=self.load_rows).grid(row=0, column=0, padx=4)
        ttk.Button(rows_btns, text='Row Details', command=self.show_row_details).grid(row=0, column=1, padx=4)

        self.load_tables()

    def load_tables(self):
        self.tbl_list.delete(0, 'end')
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY table_name")
            rows = cur.fetchall()
            for r in rows:
                self.tbl_list.insert('end', r[0])
        except Exception:
            logging.exception('Error loading table list')
            messagebox.showerror('DB Error', 'Could not load table list (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def on_table_select(self):
        sel = self.tbl_list.curselection()
        if not sel:
            return
        tbl = self.tbl_list.get(sel[0])
        self.table_name_var.set(tbl)
        # load columns
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('SELECT column_name, column_type FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = %s ORDER BY ordinal_position', (tbl,))
            cols = cur.fetchall()
            # populate cols_tv
            for i in self.cols_tv.get_children():
                self.cols_tv.delete(i)
            for c in cols:
                self.cols_tv.insert('', 'end', values=(c[0], c[1]))
            # configure rows_tv columns
            col_names = [c[0] for c in cols]
            self.rows_tv['columns'] = col_names
            for col in col_names:
                self.rows_tv.heading(col, text=col)
                self.rows_tv.column(col, width=120)
            # clear any previous rows
            for i in self.rows_tv.get_children():
                self.rows_tv.delete(i)
        except Exception:
            logging.exception('Error loading columns for table %s', tbl)
            messagebox.showerror('DB Error', 'Could not load columns (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def load_rows(self):
        tbl = self.table_name_var.get()
        if not tbl:
            messagebox.showinfo('Select Table', 'Please select a table first')
            return
        limit = self.row_limit_var.get() or 100
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(f'SELECT * FROM `{tbl}` LIMIT %s', (limit,))
            rows = cur.fetchall()
            # clear tree
            for i in self.rows_tv.get_children():
                self.rows_tv.delete(i)
            for r in rows:
                # convert to strings for display
                vals = [str(x) if x is not None else '' for x in r]
                self.rows_tv.insert('', 'end', values=vals)
        except Exception:
            logging.exception('Error loading rows for table %s', tbl)
            messagebox.showerror('DB Error', 'Could not load rows (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def export_current_page(self):
        tbl = self.table_name_var.get()
        if not tbl:
            messagebox.showinfo('Select Table', 'Please select a table first')
            return
        if not self.rows_tv.get_children():
            messagebox.showinfo('No data', 'No rows to export')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')])
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # header
                cols = self.rows_tv['columns']
                writer.writerow(cols)
                for iid in self.rows_tv.get_children():
                    writer.writerow(self.rows_tv.item(iid, 'values'))
            messagebox.showinfo('Exported', f'Exported {len(self.rows_tv.get_children())} rows to {path}')
        except Exception:
            logging.exception('Error exporting CSV')
            messagebox.showerror('Error', 'Could not export CSV (see terminal).')

    def show_row_details(self):
        sel = self.rows_tv.selection()
        if not sel:
            messagebox.showinfo('Select row', 'Please select a row to show details')
            return
        vals = self.rows_tv.item(sel[0], 'values')
        cols = self.rows_tv['columns']
        top = tk.Toplevel(self.master)
        top.title('Row Details')
        for i, col in enumerate(cols):
            ttk.Label(top, text=col + ':', font=('TkDefaultFont', 9, 'bold')).grid(row=i, column=0, sticky='e', padx=(6,4), pady=2)
            txt = tk.Text(top, height=1, width=80)
            txt.grid(row=i, column=1, sticky='w', padx=(0,6), pady=2)
            txt.insert('1.0', str(vals[i] if i < len(vals) else ''))
            txt.config(state='disabled')


def main():
    root = tk.Tk()
    root.title('DB Browser')
    root.geometry('1100x700')
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except Exception:
        pass
    app = DBBrowser(root)
    root.mainloop()


if __name__ == '__main__':
    main()
