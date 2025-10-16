"""
Windows 11-styled theming utilities for Tkinter using sv-ttk (Sun Valley ttk theme).
Falls back to the default 'clam' if sv_ttk is not installed.
"""
import tkinter as tk
from tkinter import ttk

ACCENT = '#2563EB'  # Windows 11-like blue


def setup(root: tk.Tk, dark: bool = False):
    try:
        import importlib
        sv_ttk = importlib.import_module('sv_ttk')  # pip install sv-ttk
        sv_ttk.set_theme('dark' if dark else 'light')
        style = ttk.Style()
        # Accent color for primary buttons
        style.configure('Accent.TButton', foreground='white')
        # sv_ttk uses Accent.TButton automatically if the widget class is ttk.Button with style='Accent.TButton'
    except Exception:
        # Fallback theme
        try:
            style = ttk.Style()
            style.theme_use('clam')
        except Exception:
            pass
    _apply_shared_styles()


def _apply_shared_styles():
    style = ttk.Style()
    # Global paddings
    style.configure('TFrame', padding=8)
    style.configure('TLabelframe', padding=12)
    style.configure('TLabelframe.Label', padding=(6, 0, 6, 6))
    style.configure('TButton', padding=(10, 6))
    style.configure('TEntry', padding=4)
    style.configure('TCombobox', padding=4)
    style.configure('Treeview', rowheight=26)


def apply_accent(button: ttk.Button):
    try:
        button.configure(style='Accent.TButton')
    except Exception:
        pass


def enable_alt_row_colors(tree: ttk.Treeview):
    tree.tag_configure('oddrow', background='#f6f6f6')
    tree.tag_configure('evenrow', background='#ffffff')
    for idx, iid in enumerate(tree.get_children()):
        tree.item(iid, tags=('oddrow' if idx % 2 else 'evenrow',))
