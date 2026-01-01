#!/usr/bin/env python3
"""Simple Tkinter GUI for browsing and managing quotes.

Features:
- Fuzzy search (uses `fuzzy_search` from `quotes_helper`)
- Tag filter (exact match)
- View quote details
- Add new quote

Run:
  python3 quotes_gui.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from quotes_helper import load_quotes, fuzzy_search, search_by_tag, add_quote, update_quote, delete_quote


class QuotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quotes Explorer")
        self.geometry("900x600")

        # apply Dracula-inspired dark theme
        self._apply_dracula_theme()

        self._build_widgets()
        self._refresh_tags()
        self._load_all()

    def _apply_dracula_theme(self):
        # Dracula color palette
        self._dracula = {
            'bg': '#282a36',
            'current_line': '#44475a',
            'selection': '#44475a',
            'foreground': '#f8f8f2',
            'comment': '#6272a4',
            'cyan': '#8be9fd',
            'green': '#50fa7b',
            'orange': '#ffb86c',
            'pink': '#ff79c6',
            'purple': '#bd93f9',
            'red': '#ff5555',
            'highlight': '#ffb86c',
        }
        bg = self._dracula['bg']
        fg = self._dracula['foreground']
        select = self._dracula['selection']

        # root background
        self.configure(bg=bg)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        # general ttk styling
        style.configure('.', background=bg, foreground=fg)
        style.configure('TLabel', background=bg, foreground=fg)
        style.configure('TFrame', background=bg)
        style.configure('TButton', background=self._dracula['current_line'], foreground=fg)
        style.configure('TEntry', fieldbackground=self._dracula['current_line'], foreground=fg)
        style.configure('TMenubutton', background=self._dracula['current_line'], foreground=fg)
        style.map('TButton', background=[('active', self._dracula['purple'])])

        # remember colors for later widget configs
        self._dracula_bg = bg
        self._dracula_fg = fg
        self._dracula_select = select

    def _build_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(top, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=6)
        self.search_entry.bind('<Return>', lambda e: self.on_search())

        self.min_score_var = tk.DoubleVar(value=0.35)
        ttk.Label(top, text="Min score:").pack(side=tk.LEFT, padx=(8,0))
        ttk.Entry(top, textvariable=self.min_score_var, width=6).pack(side=tk.LEFT)

        ttk.Button(top, text="Search", command=self.on_search).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Reload All", command=self._load_all).pack(side=tk.LEFT)

        ttk.Label(top, text="Tag:").pack(side=tk.LEFT, padx=(12,0))
        self.tag_var = tk.StringVar(value="")
        self.tag_menu = ttk.OptionMenu(top, self.tag_var, "")
        self.tag_menu.pack(side=tk.LEFT)
        ttk.Button(top, text="Filter by Tag", command=self.on_tag).pack(side=tk.LEFT, padx=6)

        # main panes
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # left: results list
        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.results_list = tk.Listbox(left, exportselection=False)
        self.results_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_list.bind('<<ListboxSelect>>', lambda e: self.on_select())
        scrollbar = ttk.Scrollbar(left, command=self.results_list.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.results_list.config(yscrollcommand=scrollbar.set)
        # apply listbox colors for dark theme if available
        try:
            self.results_list.config(bg=self._dracula_bg, fg=self._dracula_fg,
                                     selectbackground=self._dracula_select,
                                     selectforeground=self._dracula_fg,
                                     highlightbackground=self._dracula_bg)
        except Exception:
            pass

        # right: details + add form
        right = ttk.Frame(main, width=360)
        right.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(right, text="Details", font=(None, 12, 'bold')).pack(anchor=tk.W)
        self.details = tk.Text(right, height=10, wrap=tk.WORD)
        self.details.pack(fill=tk.X)
        # style details text for dark theme
        try:
            self.details.config(bg=self._dracula_bg, fg=self._dracula_fg, insertbackground=self._dracula_fg)
        except Exception:
            pass
        self.details.tag_configure('hl', background=self._dracula['highlight'])

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        ttk.Label(right, text="Add / Edit Quote", font=(None, 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(right, text="Text:").pack(anchor=tk.W)
        self.add_text = tk.Text(right, height=5, wrap=tk.WORD)
        self.add_text.pack(fill=tk.X)
        try:
            self.add_text.config(bg=self._dracula_bg, fg=self._dracula_fg, insertbackground=self._dracula_fg)
        except Exception:
            pass
        ttk.Label(right, text="Author:").pack(anchor=tk.W)
        self.add_author = ttk.Entry(right)
        self.add_author.pack(fill=tk.X)
        ttk.Label(right, text="Source:").pack(anchor=tk.W)
        self.add_source = ttk.Entry(right)
        self.add_source.pack(fill=tk.X)
        ttk.Label(right, text="Tags (comma separated):").pack(anchor=tk.W)
        self.add_tags = ttk.Entry(right)
        self.add_tags.pack(fill=tk.X)
        ttk.Label(right, text="Notes:").pack(anchor=tk.W)
        self.add_notes = ttk.Entry(right)
        self.add_notes.pack(fill=tk.X)
        # style simple tk/ttk widgets that don't pick up ttk style on some platforms
        try:
            for e in (self.add_author, self.add_source, self.add_tags, self.add_notes):
                e.configure(background=self._dracula['current_line'], foreground=self._dracula_fg)
        except Exception:
            pass
        btn_frame = ttk.Frame(right)
        btn_frame.pack(pady=6, fill=tk.X)
        ttk.Button(btn_frame, text="Add Quote", command=self.on_add).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Save Changes", command=self.on_save_changes).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Delete Quote", command=self.on_delete).pack(side=tk.LEFT, padx=4)

        # status bar
        self.status = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
        try:
            self.status.configure(background=self._dracula_bg, foreground=self._dracula_fg)
        except Exception:
            pass

    def _refresh_tags(self):
        data = load_quotes()
        tags = set()
        for q in data:
            for t in q.get('tags', []) or []:
                if t:
                    tags.add(t)
        choices = [""] + sorted(tags)
        menu = self.tag_menu['menu']
        menu.delete(0, 'end')
        for c in choices:
            menu.add_command(label=c, command=lambda v=c: self.tag_var.set(v))

    def _load_all(self):
        self.current = load_quotes()
        self._display_results(self.current)
        self.status.config(text=f"Loaded {len(self.current)} quotes")

    def _display_results(self, items: List[dict]):
        self.results_list.delete(0, tk.END)
        self._items = items
        for q in items:
            preview = q.get('text', '')
            # show id prefix and first 80 chars
            display = f"{q.get('id')[:8]} — {preview[:80].replace('\n',' ')}"
            self.results_list.insert(tk.END, display)

    def on_search(self):
        query = self.search_var.get().strip()
        if not query:
            self._load_all()
            return
        try:
            min_score = float(self.min_score_var.get())
        except Exception:
            min_score = 0.35
        results = fuzzy_search(query, min_score=min_score, limit=200)
        self._display_results(results)
        self.status.config(text=f"Found {len(results)} matches for '{query}'")

    def on_tag(self):
        tag = self.tag_var.get().strip()
        if not tag:
            self._load_all()
            return
        results = search_by_tag(tag)
        self._display_results(results)
        self.status.config(text=f"Found {len(results)} quotes with tag '{tag}'")

    def on_select(self):
        sel = self.results_list.curselection()
        if not sel:
            return
        q = self._items[sel[0]]
        # store currently selected id for edit/delete
        self._selected_id = q.get('id')
        self.details.delete('1.0', tk.END)
        txt = q.get('text', '') + '\n\n'
        txt += f"Author: {q.get('author')}\n"
        txt += f"Source: {q.get('source')}\n"
        txt += f"Tags: {', '.join(q.get('tags') or [])}\n"
        txt += f"Date: {q.get('date')}\n"
        txt += f"Notes: {q.get('notes')}\n"
        txt += f"ID: {q.get('id')}\n"
        # include score if present
        if q.get('_score') is not None:
            txt += f"\nScore: {q.get('_score')}\n"
        self.details.insert(tk.END, txt)
        # highlight matched snippet if present
        snippet = q.get('_match_snippet') or ''
        if snippet:
            try:
                # case-insensitive search
                start = '1.0'
                s_low = snippet.lower()
                while True:
                    idx = self.details.search(s_low, start, tk.END, nocase=1)
                    if not idx:
                        break
                    end_idx = f"{idx}+{len(snippet)}c"
                    self.details.tag_add('hl', idx, end_idx)
                    start = end_idx
            except Exception:
                pass
        # populate editor fields for convenient editing
        try:
            self.add_text.delete('1.0', tk.END)
            self.add_text.insert(tk.END, q.get('text') or '')
            self.add_author.delete(0, tk.END)
            if q.get('author'):
                self.add_author.insert(0, q.get('author'))
            self.add_source.delete(0, tk.END)
            if q.get('source'):
                self.add_source.insert(0, q.get('source'))
            self.add_tags.delete(0, tk.END)
            if q.get('tags'):
                self.add_tags.insert(0, ', '.join(q.get('tags')))
            self.add_notes.delete(0, tk.END)
            if q.get('notes'):
                self.add_notes.insert(0, q.get('notes'))
        except Exception:
            pass

    def on_add(self):
        text = self.add_text.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("No text", "Please enter quote text")
            return
        author = self.add_author.get().strip() or None
        source = self.add_source.get().strip() or None
        tags = [t.strip() for t in (self.add_tags.get() or '').split(',') if t.strip()]
        notes = self.add_notes.get().strip() or None
        obj = add_quote(text, author=author, source=source, tags=tags, notes=notes)
        self._refresh_tags()
        self._load_all()
        self.status.config(text=f"Added quote {obj['id']}")
        # clear add form
        self.add_text.delete('1.0', tk.END)
        self.add_author.delete(0, tk.END)
        self.add_source.delete(0, tk.END)
        self.add_tags.delete(0, tk.END)
        self.add_notes.delete(0, tk.END)

    def on_save_changes(self):
        """Save edits made in the editor back to the selected quote."""
        qid = getattr(self, '_selected_id', None)
        if not qid:
            messagebox.showwarning("No selection", "No quote selected to save changes to.")
            return
        text = self.add_text.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("No text", "Quote text cannot be empty")
            return
        author = self.add_author.get().strip() or None
        source = self.add_source.get().strip() or None
        tags = [t.strip() for t in (self.add_tags.get() or '').split(',') if t.strip()]
        notes = self.add_notes.get().strip() or None
        updated = update_quote(qid, text=text, author=author, source=source, tags=tags, notes=notes)
        if updated:
            self._refresh_tags()
            self._load_all()
            self.status.config(text=f"Saved changes to {qid}")
        else:
            messagebox.showerror("Not found", "Quote not found; it may have been deleted.")

    def on_delete(self):
        qid = getattr(self, '_selected_id', None)
        if not qid:
            messagebox.showwarning("No selection", "No quote selected to delete.")
            return
        if not messagebox.askyesno("Confirm delete", "Delete selected quote permanently?"):
            return
        ok = delete_quote(qid)
        if ok:
            self._refresh_tags()
            self._load_all()
            self.status.config(text=f"Deleted {qid}")
            # clear editor
            self.add_text.delete('1.0', tk.END)
            self.add_author.delete(0, tk.END)
            self.add_source.delete(0, tk.END)
            self.add_tags.delete(0, tk.END)
            self.add_notes.delete(0, tk.END)
            self._selected_id = None
        else:
            messagebox.showerror("Not found", "Quote not found; it may have been deleted already.")


def main():
    app = QuotesApp()
    app.mainloop()


if __name__ == '__main__':
    main()
