import tkinter as tk
from tkinter import ttk, messagebox
try:
    from ui_theme import setup as ui_setup, apply_accent, enable_alt_row_colors
except Exception:
    ui_setup = None
    def apply_accent(btn):
        return
    def enable_alt_row_colors(_tv):
        return
import logging
from importlib import import_module

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

DB_CONFIG = {
    'host': 'localhost',
    'user': 'Michael',
    'password': 'hogbog89',
    'database': 'cadet_tracker',
}

# Map module names to filenames (assumes all scripts are in the same folder)
MODULES = {
    'dashboard': 'dashboard',
    'add_cadet': 'add_cadet',
    'inspection_form': 'inspection_form',
    'get_next_rank': 'get_next_rank',
    'reports': 'reports',
    'manage_positions': 'manage_positions',
    'add_requirements': 'add_requirements',
}

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('CAP Cadet Tracker - Unified')
        self.geometry('1100x750')
        try:
            self.iconbitmap('my_icon.ico')
        except Exception:
            pass
        # Apply Windows 11-like theming (sv-ttk) if available
        if ui_setup:
            try:
                ui_setup(self, dark=False)
            except Exception:
                pass
        else:
            try:
                style = ttk.Style()
                style.theme_use('clam')
            except Exception:
                pass
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True)

        # Dashboard tab
        self._add_tab(nb, 'Dashboard', 'dashboard', 'Dashboard')
        # Add/Edit Cadet tab
        self._add_tab(nb, 'Add/Edit Cadet', 'add_cadet', 'CadetForm')
        # Inspection tab
        self._add_tab(nb, 'Inspections', 'inspection_form', 'InspectionForm')
        # Requirements tab (embedded)
        self._add_requirements_tab(nb)
        # Reports manager tab (embedded)
        self._add_reports_tab(nb)
        # Manage Positions tab (embedded)
        self._add_positions_tab(nb)

    def _add_tab(self, nb, tab_name, module_key, class_name, launch_button=False):
        frame = ttk.Frame(nb)
        nb.add(frame, text=tab_name)
        try:
            mod = import_module(MODULES[module_key])
            if launch_button and module_key == 'add_requirements':
                # Always call RequirementsApp() directly for requirements
                ttk.Button(frame, text=f'Open {tab_name} (separate window)', command=mod.RequirementsApp).pack(padx=12, pady=12)
            elif launch_button:
                Cls = getattr(mod, class_name, None)
                ttk.Button(frame, text=f'Open {tab_name} (separate window)', command=Cls).pack(padx=12, pady=12)
            else:
                Cls = getattr(mod, class_name, None)
                if Cls:
                    Cls(frame)
                else:
                    ttk.Label(frame, text=f'{class_name} missing in {module_key}.py').pack()
        except Exception:
            logging.exception(f'Could not load {module_key}')
            ttk.Label(frame, text=f'{tab_name} module not available').pack()

    def _add_reports_tab(self, nb):
        reports_frame = ttk.Frame(nb)
        nb.add(reports_frame, text='Reports')
        try:
            rep_mod = import_module(MODULES['reports'])
            self._build_reports_manager(reports_frame, rep_mod)
        except Exception:
            logging.exception('Could not load reports module')
            ttk.Label(reports_frame, text='Reports module not available').pack()

    def _add_positions_tab(self, nb):
        pos_frame = ttk.Frame(nb)
        nb.add(pos_frame, text='Manage Positions')
        try:
            pos_mod = import_module(MODULES['manage_positions'])
            FrameCls = getattr(pos_mod, 'PositionManagerFrame', None)
            if FrameCls:
                FrameCls(pos_frame).pack(fill='both', expand=True)
            else:
                # Fallback: show launcher button
                Cls = getattr(pos_mod, 'PositionManager', None)
                if Cls:
                    ttk.Button(pos_frame, text='Open Positions (separate window)', command=Cls).pack(padx=12, pady=12)
                else:
                    ttk.Label(pos_frame, text='Position manager not available').pack()
        except Exception:
            logging.exception('Could not load positions module')
            ttk.Label(pos_frame, text='Positions module not available').pack()

    def _add_requirements_tab(self, nb):
        req_frame = ttk.Frame(nb)
        nb.add(req_frame, text='Requirements')
        try:
            req_mod = import_module(MODULES['add_requirements'])
            FrameCls = getattr(req_mod, 'AddReqFrame', None)
            if FrameCls:
                FrameCls(req_frame).pack(fill='both', expand=True)
            else:
                # Fallback: launcher button
                AppFn = getattr(req_mod, 'RequirementsApp', None)
                if AppFn:
                    ttk.Button(req_frame, text='Open Requirements (separate window)', command=AppFn).pack(padx=12, pady=12)
                else:
                    ttk.Label(req_frame, text='Requirements module not available').pack()
        except Exception:
            logging.exception('Could not load requirements module')
            ttk.Label(req_frame, text='Requirements module not available').pack()

    def _build_reports_manager(self, parent, rep_mod):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill='both', expand=True)
        topf = ttk.Frame(frame)
        topf.pack(fill='x')
        btn_refresh = ttk.Button(topf, text='Refresh', command=lambda: self._load_reports(rep_mod))
        # Open an embedded editor below the table
        btn_new = ttk.Button(topf, text='New Report', command=lambda: self._open_report_editor(rep_mod, None))
        apply_accent(btn_new)
        btn_refresh.pack(side='left', padx=6)
        btn_new.pack(side='left', padx=6)
        btn_edit = ttk.Button(topf, text='Edit Selected', command=lambda: self._edit_selected_report(rep_mod))
        btn_edit.pack(side='left', padx=6)
        try:
            apply_accent(btn_edit)
        except Exception:
            pass
        btn_del = ttk.Button(topf, text='Delete Selected', command=lambda: self._delete_selected_report(rep_mod))
        apply_accent(btn_del)
        btn_del.pack(side='left', padx=6)
        cols = ('id', 'cadet_id', 'type', 'title', 'date', 'resolved')
        self.reports_tv = ttk.Treeview(frame, columns=cols, show='headings', selectmode='browse')
        self._reports_sort = {'by': 'date', 'order': 'DESC'}
        for c in cols:
            self.reports_tv.heading(c, text=c.title(), command=lambda col=c: self._on_reports_heading_click(col, rep_mod))
        self.reports_tv.pack(fill='both', expand=True, pady=(8,0))
        self._load_reports(rep_mod)
        try:
            enable_alt_row_colors(self.reports_tv)
        except Exception:
            pass
        # editor area
        self.reports_editor_container = ttk.Labelframe(frame, text='Report Editor', padding=8)
        self.reports_editor_container.pack(fill='x', pady=8)

    def _load_reports(self, rep_mod):
        for i in self.reports_tv.get_children():
            self.reports_tv.delete(i)
        try:
            rows = rep_mod.fetch_reports(sort_by=self._reports_sort['by'], order=self._reports_sort['order'])
            for r in rows:
                self.reports_tv.insert('', 'end', values=(r[0], r[1], r[2], (r[3] or '')[:60], str(r[4]), 'Yes' if r[5] else 'No'))
            try:
                enable_alt_row_colors(self.reports_tv)
            except Exception:
                pass
        except Exception:
            logging.exception('Error loading reports')
            messagebox.showerror('Error', 'Could not load reports (see terminal)')

    def _on_reports_heading_click(self, col, rep_mod):
        col_map = {
            'id': 'id',
            'cadet_id': 'cadet_id',
            'type': 'type',
            'title': 'title',
            'date': 'date',
            'resolved': 'resolved'
        }
        key = col_map.get(col, 'date')
        if self._reports_sort['by'] == key:
            self._reports_sort['order'] = 'ASC' if self._reports_sort['order'] == 'DESC' else 'DESC'
        else:
            self._reports_sort['by'] = key
            self._reports_sort['order'] = 'DESC'
        self._load_reports(rep_mod)

    def _edit_selected_report(self, rep_mod):
        sel = self.reports_tv.selection()
        if not sel:
            messagebox.showinfo('Select', 'Select a report first')
            return
        item = sel[0]
        vals = self.reports_tv.item(item, 'values')
        report_id = vals[0]
        self._open_report_editor(rep_mod, report_id)

    def _delete_selected_report(self, rep_mod):
        sel = self.reports_tv.selection()
        if not sel:
            messagebox.showinfo('Select', 'Select a report first')
            return
        item = sel[0]
        vals = self.reports_tv.item(item, 'values')
        report_id = vals[0]
        if not messagebox.askyesno('Confirm', f'Delete report {report_id}?'):
            return
        try:
            if rep_mod.delete_report(report_id):
                messagebox.showinfo('Deleted', 'Report deleted')
                self._load_reports(rep_mod)
            else:
                messagebox.showerror('Error', 'Could not delete report')
        except Exception:
            logging.exception('Error deleting report')
            messagebox.showerror('Error', 'Could not delete report (see terminal)')

    def _open_report_editor(self, rep_mod, report_id):
        # Clear previous editor
        for w in self.reports_editor_container.winfo_children():
            w.destroy()
        try:
            FrameCls = getattr(rep_mod, 'ReportFormFrame', None)
            if FrameCls:
                FrameCls(self.reports_editor_container, report_id=report_id, on_close=lambda: self._load_reports(rep_mod)).pack(fill='x', expand=False)
            else:
                # fallback to toplevel
                rep_mod.ReportForm(self, report_id=report_id)
        except Exception:
            logging.exception('Error opening embedded report editor')
            messagebox.showerror('Error', 'Could not open report editor')

if __name__ == '__main__':
    app = MainApp()
    app.mainloop()
