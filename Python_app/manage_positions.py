import tkinter as tk
from tkinter import ttk, messagebox
import logging
try:
    from ui_theme import setup as theme_setup, apply_accent, enable_alt_row_colors
except Exception:
    def theme_setup(_root, dark=False):
        return
    def apply_accent(_btn):
        return
    def enable_alt_row_colors(_tv):
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


class PositionManager(tk.Tk):
    """GUI to add, edit, and delete positions from the position table.
    
    Positions have:
    - position_id (auto-increment primary key)
    - position_name (varchar)
    - line (tinyint: 1 = Line/Staff position, 0 = Support position)
    """

    def __init__(self):
        super().__init__()
        self.title('Manage Positions')
        self.geometry('800x500')
        self.selected_position_id = None
        try:
            theme_setup(self, dark=False)
        except Exception:
            pass
        self._build_ui()
        self.load_positions()

    def _build_ui(self):
        # Main container
        main = ttk.Frame(self, padding=12)
        main.pack(fill='both', expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # Top frame: form for add/edit
        form_frame = ttk.Labelframe(main, text='Position Details', padding=12)
        form_frame.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text='Position Name:').grid(row=0, column=0, sticky='e', padx=(0, 8), pady=6)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky='w', pady=6)

        ttk.Label(form_frame, text='Level:').grid(row=1, column=0, sticky='e', padx=(0, 8), pady=6)
        self.level_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.level_var, width=20).grid(row=1, column=1, sticky='w', pady=6)

        ttk.Label(form_frame, text='Type:').grid(row=2, column=0, sticky='e', padx=(0, 8), pady=6)
        self.type_var = tk.StringVar(value='Support')
        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=2, column=1, sticky='w', pady=6)
        ttk.Radiobutton(type_frame, text='Line/Staff Position', variable=self.type_var, value='Line').grid(row=0, column=0, padx=(0, 12))
        ttk.Radiobutton(type_frame, text='Support Position', variable=self.type_var, value='Support').grid(row=0, column=1)

        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        btn_add = ttk.Button(btn_frame, text='Add New', command=self.add_position)
        btn_add.grid(row=0, column=0, padx=6)
        try:
            apply_accent(btn_add)
        except Exception:
            pass
        btn_update = ttk.Button(btn_frame, text='Update Selected', command=self.update_position)
        btn_update.grid(row=0, column=1, padx=6)
        try:
            apply_accent(btn_update)
        except Exception:
            pass
        ttk.Button(btn_frame, text='Delete Selected', command=self.delete_position).grid(row=0, column=2, padx=6)
        ttk.Button(btn_frame, text='Clear Form', command=self.clear_form).grid(row=0, column=3, padx=6)

        # Bottom frame: list of positions
        list_frame = ttk.Labelframe(main, text='Positions', padding=12)
        list_frame.grid(row=1, column=0, sticky='nsew')
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Treeview
        columns = ('ID', 'Name', 'Type', 'Level')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Position Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Level', text='Level')
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Name', width=300)
        self.tree.column('Type', width=120, anchor='center')
        self.tree.column('Level', width=80, anchor='center')
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Refresh button at bottom
        btn_refresh = ttk.Button(list_frame, text='Refresh List', command=self.load_positions)
        btn_refresh.grid(row=1, column=0, columnspan=2, pady=(8, 0))

    def load_positions(self):
        """Load all positions from the database and populate the treeview."""
        self.tree.delete(*self.tree.get_children())
        
        conn = get_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            cur.execute('SELECT position_id, position_name, line, level FROM `position` ORDER BY position_id')
            rows = cur.fetchall()
            
            for row in rows:
                pos_id = row[0]
                name = row[1] or ''
                line_flag = row[2]
                level = row[3]
                pos_type = 'Line/Staff' if line_flag == 1 else 'Support'
                self.tree.insert('', 'end', values=(pos_id, name, pos_type, level))
            try:
                enable_alt_row_colors(self.tree)
            except Exception:
                pass
        except Exception:
            logging.exception('Error loading positions')
            messagebox.showerror('DB Error', 'Could not load positions (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def on_select(self, event):
        """Populate the form when a position is selected in the treeview."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        if values:
            self.selected_position_id = values[0]
            self.name_var.set(values[1])
            self.type_var.set('Line' if values[2] == 'Line/Staff' else 'Support')
            self.level_var.set(str(values[3]))

    def clear_form(self):
        """Clear the form and deselect."""
        self.selected_position_id = None
        self.name_var.set('')
        self.type_var.set('Support')
        self.level_var.set('')
        self.tree.selection_remove(*self.tree.selection())

    def add_position(self):
        """Add a new position to the database."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror('Validation', 'Position name is required.')
            return
        level = self.level_var.get().strip()
        if not level:
            messagebox.showerror('Validation', 'Level is required.')
            return
        line_flag = 1 if self.type_var.get() == 'Line' else 0
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('INSERT INTO `position` (position_name, line, level) VALUES (%s, %s, %s)', (name, line_flag, level))
            conn.commit()
            messagebox.showinfo('Success', f'Position "{name}" added successfully.')
            self.clear_form()
            self.load_positions()
        except Exception:
            conn.rollback()
            logging.exception('Error adding position')
            messagebox.showerror('DB Error', 'Could not add position (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def update_position(self):
        """Update the selected position in the database."""
        if not self.selected_position_id:
            messagebox.showerror('Validation', 'Please select a position to update.')
            return
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror('Validation', 'Position name is required.')
            return
        level = self.level_var.get().strip()
        if not level:
            messagebox.showerror('Validation', 'Level is required.')
            return
        line_flag = 1 if self.type_var.get() == 'Line' else 0
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('UPDATE `position` SET position_name=%s, line=%s, level=%s WHERE position_id=%s', 
                       (name, line_flag, level, self.selected_position_id))
            conn.commit()
            messagebox.showinfo('Success', f'Position updated successfully.')
            self.clear_form()
            self.load_positions()
        except Exception:
            conn.rollback()
            logging.exception('Error updating position')
            messagebox.showerror('DB Error', 'Could not update position (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def delete_position(self):
        """Delete the selected position from the database."""
        if not self.selected_position_id:
            messagebox.showerror('Validation', 'Please select a position to delete.')
            return
        
        name = self.name_var.get().strip()
        confirm = messagebox.askyesno('Confirm Delete', 
                                     f'Are you sure you want to delete position "{name}"?\n\n'
                                     f'This will also remove all cadet assignments to this position.')
        if not confirm:
            return
        
        conn = get_connection()
        if not conn:
            return
        
        try:
            cur = conn.cursor()
            # Delete mappings first (foreign key constraint)
            cur.execute('DELETE FROM position_has_cadet WHERE position_position_id=%s', (self.selected_position_id,))
            # Delete the position
            cur.execute('DELETE FROM `position` WHERE position_id=%s', (self.selected_position_id,))
            conn.commit()
            messagebox.showinfo('Success', f'Position deleted successfully.')
            self.clear_form()
            self.load_positions()
        except Exception:
            conn.rollback()
            logging.exception('Error deleting position')
            messagebox.showerror('DB Error', 'Could not delete position (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass


def main():
    app = PositionManager()
    app.mainloop()


if __name__ == '__main__':
    main()


class PositionManagerFrame(ttk.Frame):
    """Embeddable Positions manager for use inside a Notebook tab (no separate window)."""
    def __init__(self, master=None):
        super().__init__(master)
        self.selected_position_id = None
        try:
            # Parent may already have theme applied; do nothing here
            pass
        except Exception:
            pass
        self._build_ui()
        self.load_positions()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        form_frame = ttk.Labelframe(self, text='Position Details', padding=12)
        form_frame.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text='Position Name:').grid(row=0, column=0, sticky='e', padx=(0, 8), pady=6)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky='w', pady=6)

        ttk.Label(form_frame, text='Level:').grid(row=1, column=0, sticky='e', padx=(0, 8), pady=6)
        self.level_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.level_var, width=20).grid(row=1, column=1, sticky='w', pady=6)

        ttk.Label(form_frame, text='Type:').grid(row=2, column=0, sticky='e', padx=(0, 8), pady=6)
        self.type_var = tk.StringVar(value='Support')
        type_frame = ttk.Frame(form_frame)
        type_frame.grid(row=2, column=1, sticky='w', pady=6)
        ttk.Radiobutton(type_frame, text='Line/Staff Position', variable=self.type_var, value='Line').grid(row=0, column=0, padx=(0, 12))
        ttk.Radiobutton(type_frame, text='Support Position', variable=self.type_var, value='Support').grid(row=0, column=1)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        btn_add = ttk.Button(btn_frame, text='Add New', command=self.add_position)
        btn_add.grid(row=0, column=0, padx=6)
        try:
            apply_accent(btn_add)
        except Exception:
            pass
        btn_update = ttk.Button(btn_frame, text='Update Selected', command=self.update_position)
        btn_update.grid(row=0, column=1, padx=6)
        try:
            apply_accent(btn_update)
        except Exception:
            pass
        ttk.Button(btn_frame, text='Delete Selected', command=self.delete_position).grid(row=0, column=2, padx=6)
        ttk.Button(btn_frame, text='Clear Form', command=self.clear_form).grid(row=0, column=3, padx=6)

        list_frame = ttk.Labelframe(self, text='Positions', padding=12)
        list_frame.grid(row=1, column=0, sticky='nsew')
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ('ID', 'Name', 'Type', 'Level')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Position Name')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Level', text='Level')
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Name', width=300)
        self.tree.column('Type', width=120, anchor='center')
        self.tree.column('Level', width=80, anchor='center')
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        try:
            enable_alt_row_colors(self.tree)
        except Exception:
            pass
        ttk.Button(list_frame, text='Refresh List', command=self.load_positions).grid(row=1, column=0, columnspan=2, pady=(8, 0))

    # The methods below mirror the tk.Tk-based manager, adapted for Frame
    def load_positions(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('SELECT position_id, position_name, line, level FROM `position` ORDER BY position_id')
            rows = cur.fetchall()
            for row in rows:
                pos_id = row[0]
                name = row[1] or ''
                line_flag = row[2]
                level = row[3]
                pos_type = 'Line/Staff' if line_flag == 1 else 'Support'
                self.tree.insert('', 'end', values=(pos_id, name, pos_type, level))
        except Exception:
            logging.exception('Error loading positions')
            messagebox.showerror('DB Error', 'Could not load positions (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item['values']
        if values:
            self.selected_position_id = values[0]
            self.name_var.set(values[1])
            self.type_var.set('Line' if values[2] == 'Line/Staff' else 'Support')
            self.level_var.set(str(values[3]))

    def clear_form(self):
        self.selected_position_id = None
        self.name_var.set('')
        self.type_var.set('Support')
        self.level_var.set('')
        try:
            self.tree.selection_remove(*self.tree.selection())
        except Exception:
            pass

    def add_position(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror('Validation', 'Position name is required.')
            return
        level = self.level_var.get().strip()
        if not level:
            messagebox.showerror('Validation', 'Level is required.')
            return
        line_flag = 1 if self.type_var.get() == 'Line' else 0
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('INSERT INTO `position` (position_name, line, level) VALUES (%s, %s, %s)', (name, line_flag, level))
            conn.commit()
            messagebox.showinfo('Success', f'Position "{name}" added successfully.')
            self.clear_form()
            self.load_positions()
        except Exception:
            conn.rollback()
            logging.exception('Error adding position')
            messagebox.showerror('DB Error', 'Could not add position (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def update_position(self):
        if not self.selected_position_id:
            messagebox.showerror('Validation', 'Please select a position to update.')
            return
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror('Validation', 'Position name is required.')
            return
        level = self.level_var.get().strip()
        if not level:
            messagebox.showerror('Validation', 'Level is required.')
            return
        line_flag = 1 if self.type_var.get() == 'Line' else 0
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('UPDATE `position` SET position_name=%s, line=%s, level=%s WHERE position_id=%s', (name, line_flag, level, self.selected_position_id))
            conn.commit()
            messagebox.showinfo('Success', f'Position updated successfully.')
            self.clear_form()
            self.load_positions()
        except Exception:
            conn.rollback()
            logging.exception('Error updating position')
            messagebox.showerror('DB Error', 'Could not update position (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def delete_position(self):
        if not self.selected_position_id:
            messagebox.showerror('Validation', 'Please select a position to delete.')
            return
        name = self.name_var.get().strip()
        confirm = messagebox.askyesno('Confirm Delete', f'Are you sure you want to delete position "{name}"?\n\nThis will also remove all cadet assignments to this position.')
        if not confirm:
            return
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM position_has_cadet WHERE position_position_id=%s', (self.selected_position_id,))
            cur.execute('DELETE FROM `position` WHERE position_id=%s', (self.selected_position_id,))
            conn.commit()
            messagebox.showinfo('Success', f'Position deleted successfully.')
            self.clear_form()
            self.load_positions()
        except Exception:
            conn.rollback()
            logging.exception('Error deleting position')
            messagebox.showerror('DB Error', 'Could not delete position (see terminal).')
        finally:
            try:
                conn.close()
            except Exception:
                pass
