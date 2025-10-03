import tkinter as tk
from tkinter import ttk, messagebox
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# try to import the various app components; some may be standalone scripts so we embed or wrap them
from importlib import import_module

MODULES = {
    'dashboard': 'dashboard',
    'add_cadet': 'add_cadet',
    'inspection_form': 'inspection_form',
    'get_next_rank': 'get_next_rank',
    'reports': 'reports'
}


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('CAP Cadet Tracker - Unified')
        self.geometry('1100x750')
        # set application icon if available
        try:
            self.iconbitmap('my_icon.ico')
        except Exception:
            # ignore if not available or not supported on platform
            pass
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
        dash_frame = ttk.Frame(nb)
        nb.add(dash_frame, text='Dashboard')
        try:
            dash_mod = import_module(MODULES['dashboard'])
            Dashboard = getattr(dash_mod, 'Dashboard', None)
            if Dashboard:
                self.dashboard = Dashboard(dash_frame)
            else:
                ttk.Label(dash_frame, text='Dashboard module found but Dashboard class missing').pack()
        except Exception:
            logging.exception('Could not load dashboard module')
            ttk.Label(dash_frame, text='Dashboard module not available').pack()

        # Add Cadet tab
        cadet_frame = ttk.Frame(nb)
        nb.add(cadet_frame, text='Add/Edit Cadet')
        try:
            cad_mod = import_module(MODULES['add_cadet'])
            CadetForm = getattr(cad_mod, 'CadetForm', None)
            if CadetForm:
                self.cadet_form = CadetForm(cadet_frame)
            else:
                ttk.Label(cadet_frame, text='Cadet form missing in module').pack()
        except Exception:
            logging.exception('Could not load add_cadet')
            ttk.Label(cadet_frame, text='Add cadet module not available').pack()

        # Inspection tab
        insp_frame = ttk.Frame(nb)
        nb.add(insp_frame, text='Inspections')
        try:
            insp_mod = import_module(MODULES['inspection_form'])
            InspectionForm = getattr(insp_mod, 'InspectionForm', None)
            if InspectionForm:
                self.insp = InspectionForm(insp_frame)
            else:
                ttk.Label(insp_frame, text='InspectionForm class missing').pack()
        except Exception:
            logging.exception('Could not load inspection_form')
            ttk.Label(insp_frame, text='Inspection form module not available').pack()

        # Requirements editor tab (optional)
        req_frame = ttk.Frame(nb)
        nb.add(req_frame, text='Requirements')
        try:
            req_mod = import_module(MODULES['get_next_rank'])
            ReqEditor = getattr(req_mod, 'ReqEditor', None)
            if ReqEditor:
                # embed the editor as a child window; ReqEditor is a Tk root - instead provide a launch button
                ttk.Button(req_frame, text='Open Requirements Editor (separate window)', command=lambda: req_mod.ReqEditor()).pack(padx=12, pady=12)
            else:
                ttk.Label(req_frame, text='Requirements editor class not found').pack()
        except Exception:
            logging.exception('Could not load requirements editor')
            ttk.Label(req_frame, text='Requirements editor not available').pack()

        # Reports manager tab
        reports_frame = ttk.Frame(nb)
        nb.add(reports_frame, text='Reports')
        try:
            rep_mod = import_module(MODULES['reports'])
            # build a small manager in this tab
            self._build_reports_manager(reports_frame, rep_mod)
        except Exception:
            logging.exception('Could not load reports module')
            ttk.Label(reports_frame, text='Reports module not available').pack()

    def _build_reports_manager(self, parent, rep_mod):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill='both', expand=True)

        topf = ttk.Frame(frame)
        topf.pack(fill='x')
        ttk.Button(topf, text='Refresh', command=lambda: self._load_reports(rep_mod)).pack(side='left', padx=6)
        ttk.Button(topf, text='New Report', command=lambda: rep_mod.ReportForm(self, selected_cadet=None)).pack(side='left', padx=6)
        ttk.Button(topf, text='Edit Selected', command=lambda: self._edit_selected_report(rep_mod)).pack(side='left', padx=6)
        ttk.Button(topf, text='Delete Selected', command=lambda: self._delete_selected_report(rep_mod)).pack(side='left', padx=6)

        cols = ('id', 'cadet_id', 'type', 'title', 'date', 'resolved')
        self.reports_tv = ttk.Treeview(frame, columns=cols, show='headings', selectmode='browse')
        # store sort state
        self._reports_sort = {'by': 'date', 'order': 'DESC'}
        for c in cols:
            # make headings clickable
            self.reports_tv.heading(c, text=c.title(), command=lambda col=c: self._on_reports_heading_click(col, rep_mod))
        self.reports_tv.pack(fill='both', expand=True, pady=(8,0))
        self._load_reports(rep_mod)

    def _load_reports(self, rep_mod):
        for i in self.reports_tv.get_children():
            self.reports_tv.delete(i)
        try:
            rows = rep_mod.fetch_reports(sort_by=self._reports_sort['by'], order=self._reports_sort['order'])
            for r in rows:
                self.reports_tv.insert('', 'end', values=(r[0], r[1], r[2], (r[3] or '')[:60], str(r[4]), 'Yes' if r[5] else 'No'))
        except Exception:
            logging.exception('Error loading reports')
            messagebox.showerror('Error', 'Could not load reports (see terminal)')

    def _on_reports_heading_click(self, col, rep_mod):
        # map treeview column to fetch_reports sort_by key
        col_map = {
            'id': 'id',
            'cadet_id': 'cadet_id',
            'type': 'type',
            'title': 'title',
            'date': 'date',
            'resolved': 'resolved'
        }
        key = col_map.get(col, 'date')
        # toggle order if same column
        if self._reports_sort['by'] == key:
            self._reports_sort['order'] = 'ASC' if self._reports_sort['order'] == 'DESC' else 'DESC'
        else:
            self._reports_sort['by'] = key
            self._reports_sort['order'] = 'DESC'
        # reload
        self._load_reports(rep_mod)

    def _edit_selected_report(self, rep_mod):
        sel = self.reports_tv.selection()
        if not sel:
            messagebox.showinfo('Select', 'Select a report first')
            return
        item = sel[0]
        vals = self.reports_tv.item(item, 'values')
        report_id = vals[0]
        try:
            rep_mod.ReportForm(self, report_id=report_id)
        except Exception:
            logging.exception('Error opening report editor')
            messagebox.showerror('Error', 'Could not open report editor')

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


if __name__ == '__main__':
    app = MainApp()
    app.mainloop()
