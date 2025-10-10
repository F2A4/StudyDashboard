import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from data_store import get_study_time_weeks, load_json, save_json


COLOR_BG = "#f8fafc"


class WeeklyTimeDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Wöchentliche Lernzeit hinzufügen/bearbeiten")
        self.geometry("500x450")
        self.configure(bg=COLOR_BG)
        self.transient(parent)
        self.grab_set()

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        # Initialize selected_date first
        self.selected_date = date.today() - timedelta(days=date.today().weekday())

        self._build()

    def _build(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Week selection section
        week_section = ttk.LabelFrame(main_frame, text="Woche auswählen")
        week_section.pack(fill=tk.X, pady=(0, 15))

        # Selected week display (create first)
        self.selected_week_label = ttk.Label(week_section, text="", font=("Arial", 10, "bold"))
        self.selected_week_label.pack(pady=(10, 5))

        # Calendar widget inside week section
        self.calendar_frame = ttk.Frame(week_section)
        self.calendar_frame.pack(fill=tk.X, padx=10, pady=10)

        self._create_week_selection_widget()

        # Hours input section
        hours_section = ttk.LabelFrame(main_frame, text="Lernzeit eingeben")
        hours_section.pack(fill=tk.X, pady=(0, 15))

        # Hours input frame
        hours_frame = ttk.Frame(hours_section)
        hours_frame.pack(padx=10, pady=10)

        ttk.Label(hours_frame, text="Stunden pro Woche:").pack(side=tk.LEFT)

        self.hours_var = tk.StringVar()
        self.hours_entry = ttk.Entry(hours_frame, textvariable=self.hours_var, width=8)
        self.hours_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Validate that only numbers are entered
        vcmd = (self.register(self._validate_number), '%P')
        self.hours_entry.config(validate='key', validatecommand=vcmd)

        # Initialize the selected week display
        week_end = self.selected_date + timedelta(days=6)
        self.selected_week_label.config(text=f"Ausgewählte Woche: {self.selected_date.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}")

        # Check if week already exists and preload value
        self._check_existing_week()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Speichern", command=self._save_weekly_time).pack(side=tk.RIGHT)

    def _create_week_selection_widget(self):
        today = date.today()

        # Month and year selection
        nav_frame = ttk.Frame(self.calendar_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))

        self.month_var = tk.IntVar(value=today.month)
        self.year_var = tk.IntVar(value=today.year)

        ttk.Button(nav_frame, text="<", width=3, command=self._prev_month).pack(side=tk.LEFT)

        month_label = ttk.Label(nav_frame, text="")
        month_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(nav_frame, text=">", width=3, command=self._next_month).pack(side=tk.LEFT)

        # Update month label when variables change
        def update_month_label(*args):
            months = ["", "Januar", "Februar", "März", "April", "Mai", "Juni",
                     "Juli", "August", "September", "Oktober", "November", "Dezember"]
            month_label.config(text=f"{months[self.month_var.get()]} {self.year_var.get()}")

        self.month_var.trace('w', update_month_label)
        self.year_var.trace('w', update_month_label)
        update_month_label()

        # Calendar grid
        self.calendar_grid = ttk.Frame(self.calendar_frame)
        self.calendar_grid.pack(fill=tk.X)

        # Day headers
        headers = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        for i, header in enumerate(headers):
            ttk.Label(self.calendar_grid, text=header, width=5).grid(row=0, column=i, padx=1, pady=1)

        # Update calendar with current selection
        self._update_week_selection()

    def _prev_month(self):
        if self.month_var.get() > 1:
            self.month_var.set(self.month_var.get() - 1)
        else:
            self.month_var.set(12)
            self.year_var.set(self.year_var.get() - 1)
        self._update_week_selection()

    def _next_month(self):
        if self.month_var.get() < 12:
            self.month_var.set(self.month_var.get() + 1)
        else:
            self.month_var.set(1)
            self.year_var.set(self.year_var.get() + 1)
        self._update_week_selection()

    def _update_week_selection(self):
        # Clear existing calendar
        for widget in self.calendar_grid.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.destroy()

        # Get first day of month and number of days
        year = self.year_var.get()
        month = self.month_var.get()
        first_day = date(year, month, 1)
        last_day = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year + 1, 1, 1) - timedelta(days=1)

        # Calculate starting position (Monday = 0)
        start_pos = (first_day.weekday()) % 7

        # Create week buttons instead of day buttons
        day_num = 1
        for week in range(6):  # Maximum 6 weeks
            week_start_day = None
            week_end_day = None

            # Find the Monday of this week
            for day in range(7):
                if week == 0 and day < start_pos:
                    continue
                elif day_num > last_day.day:
                    break

                if day == 0:  # Monday
                    week_start_day = day_num
                elif day == 6:  # Sunday
                    week_end_day = day_num

                day_num += 1

            # Only create week button if we have a complete week
            if week_start_day is not None:
                week_monday = date(year, month, week_start_day) - timedelta(days=date(year, month, week_start_day).weekday())
                week_end = week_monday + timedelta(days=6)

                # Create week button spanning the full week
                btn = ttk.Button(self.calendar_grid, text=f"{week_start_day}-{week_end_day if week_end_day else last_day.day}",
                               width=15, command=lambda w=week_monday: self._select_week(w))
                btn.grid(row=week + 1, column=0, columnspan=7, padx=1, pady=1, sticky="ew")

                # Highlight current week
                today = date.today()
                current_week_start = today - timedelta(days=today.weekday())
                if week_monday == current_week_start:
                    btn.config(style="Accent.TButton")

    def _select_week(self, week_start: date):
        self.selected_date = week_start

        # Update the selected week display
        week_end = week_start + timedelta(days=6)
        self.selected_week_label.config(text=f"Ausgewählte Woche: {week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}")

        # Update hours field if this week already has data
        self._check_existing_week()

    def _validate_number(self, value: str):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _check_existing_week(self):
        try:
            # The selected_date is already the Monday of the week
            week_start = self.selected_date

            # Load existing data
            weeks = get_study_time_weeks()
            for week_date, hours in weeks:
                if week_date == week_start:
                    self.hours_var.set(str(hours))
                    return

            # Clear hours if no existing data found
            self.hours_var.set("")
        except (ValueError, AttributeError):
            # Invalid date or no selected date, ignore
            pass

    def _save_weekly_time(self):
        try:
            hours_text = self.hours_var.get().strip()
            hours = float(hours_text) if hours_text != "" else 0.0
            if hours < 0:
                messagebox.showerror("Fehler", "Die Lernzeit muss eine positive Zahl sein.")
                return

            week_start = self.selected_date  # already a Monday

            # Load JSON
            data = load_json()
            if "study_time" not in data or not isinstance(data["study_time"], list):
                data["study_time"] = []

            # Find existing entry index (if any)
            week_iso = week_start.isoformat()
            existingIndex = next((i for i, w in enumerate(data["study_time"])
                        if w.get("week_start") == week_iso), None)

            if hours == 0:
                # DELETE entry for this week, if it exists
                if existingIndex is not None:
                    del data["study_time"][existingIndex]
                    save_json(data)
                    messagebox.showinfo("Gelöscht", f"Eintrag für Woche {week_iso} wurde entfernt.")
                else:
                    messagebox.showerror("Fehler", "Bitte verwenden sie eine gültige Zahl")
                    return
            else:
                #update or insert
                if existingIndex is not None:
                    data["study_time"][existingIndex]["hours"] = hours
                else:
                    data["study_time"].append({"week_start": week_iso, "hours": hours})
                    # keep list ordered
                    data["study_time"].sort(key=lambda x: x["week_start"])

                save_json(data)
                messagebox.showinfo("Erfolg", f"Lernzeit für Woche {week_iso} gespeichert.")

            # Close dialog and refresh Dashboard
            self.destroy()
            self.parent.destroy()
            from app import Dashboard
            Dashboard().mainloop()

        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {str(e)}")
