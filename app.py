import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta

from data_store import get_general, get_semester_grades, get_study_time_weeks
from weekly_time_dialog import WeeklyTimeDialog
from analytics import (
    weighted_average_grade,
    ects_by_semester,
    ects_current_semester_month,
    ects_status,
    pass_rate,
    repeat_ratio,
    learning_hours_status,
    backlog_modules,
    backlog_status,
    study_end_forecast,
    grade_status,
    semester_average_grades,
)
from charts import bar_chart, line_chart

COLOR_BG = "#f8fafc"
COLOR_PANEL = "#ffffff"
COLOR_TEXT = "#0f172a"

STATUS_COLORS = {
    "light_green": "#86efac",
    "green": "#10b981",
    "orange": "#f59e0b",
    "red": "#ef4444",
}


class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Studien-Dashboard")
        self.geometry("1350x850")
        self.configure(bg=COLOR_BG)
        self._build()

    def _card(self, parent: tk.Widget):
        frame = ttk.Frame(parent)
        frame['padding'] = 10
        return frame

    def _get_progression_width(self, status: str, max_width: int) -> int:
        if status == "red":
            return max_width // 4  # 25%
        elif status == "orange":
            return max_width // 2  # 50%
        elif status == "green":
            return int(max_width * 0.75)  # 75%
        elif status == "light_green":
            return max_width  # 100%
        else:
            return max_width // 4  # Default to red length

    def _build(self):
        general = get_general()
        semesters = get_semester_grades()
        weeks = get_study_time_weeks()

        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        # Top KPIs grid
        kpi_frame = ttk.Frame(content)
        kpi_frame.pack(fill=tk.X)

        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1)

        # 1. Studienzeit forecast
        forecast_date, forecast_status = study_end_forecast(semesters)
        card1 = ttk.LabelFrame(kpi_frame, text="Studienzeit")
        card1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        ttk.Label(card1, text=f"Prognose Enddatum: {forecast_date.isoformat()}").pack(anchor="w")
        self._progress_bar(card1, forecast_status)


        # 2. Durchschnittsnote
        avg = weighted_average_grade(semesters)
        card2 = ttk.LabelFrame(kpi_frame, text="Durchschnittsnote")
        card2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        avg_txt = "-" if avg is None else f"{avg:.2f}"
        ttk.Label(card2, text=f"Aktuell: {avg_txt}").pack(anchor="w")
        grade_status_val = grade_status(avg)
        self._progress_bar(card2, grade_status_val)


        # 3. ECTS im Semester/Monat
        sem_ects, month_ects = ects_current_semester_month(semesters)
        sem_status, month_status = ects_status(sem_ects, month_ects)
        card3 = ttk.LabelFrame(kpi_frame, text="ECTS")
        card3.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
        ttk.Label(card3, text=f"Aktuelles Semester: {sem_ects} ECTS").pack(anchor="w")
        ttk.Label(card3, text=f"Diesen Monat: {month_ects} ECTS").pack(anchor="w")
        self._progress_bar(card3, month_status)

        # 4. Bestehensquote
        rate = pass_rate(semesters)
        card4 = ttk.LabelFrame(kpi_frame, text="Bestehensquote")
        card4.grid(row=0, column=3, sticky="nsew", padx=6, pady=6)
        rate_txt = "-" if rate is None else f"{int(rate*100)}%"
        ttk.Label(card4, text=f"Dieses Semester: {rate_txt}").pack(anchor="w")

        # Row 2
        kpi2 = ttk.Frame(content)
        kpi2.pack(fill=tk.X)
        for i in range(3):
            kpi2.columnconfigure(i, weight=1)

        # Wiederholungsquote
        rep = repeat_ratio(semesters)
        card5 = ttk.LabelFrame(kpi2, text="Wiederholungsquote")
        card5.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        rep_txt = "-" if rep is None or rep == float("inf") else f"{rep:.2f}"
        ttk.Label(card5, text=f"Ratio: {rep_txt}").pack(anchor="w")

        today = date.today()
        current_week_start = today - timedelta(days=today.weekday())

        # Find current week hours
        current_week_hours = None
        for week_date, hours in weeks:
            if week_date == current_week_start:
                current_week_hours = hours
                break

        card6 = ttk.LabelFrame(kpi2, text="Wöchentliche Lernzeit")
        card6.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        w_txt = "-" if current_week_hours is None else f"{current_week_hours} h"
        avg_hours = sum(week[1] for week in weeks) / len(weeks)

        header = ttk.Frame(card6)
        header.pack(fill=tk.X)

        ttk.Label(header, text=f"Durchschnitt: {avg_hours:.1f} h").pack(anchor="w")
        ttk.Button(header, text="+", width=3, command=self._open_weekly_time_dialog).pack(side=tk.RIGHT)
        ttk.Label(card6, text=f"Diese Woche: {w_txt}").pack(anchor="w")

        current_week_status = learning_hours_status(current_week_hours)
        self._progress_bar(card6, current_week_status)


# Backlog
        months_since_start = max(0, (date.today().year - date.fromisoformat(general['start_date']).year) * 12 + (date.today().month - date.fromisoformat(general['start_date']).month))
        backlog = backlog_modules(semesters, months_since_start)
        card7 = ttk.LabelFrame(kpi2, text="Nachhol-Backlog")
        card7.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
        ttk.Label(card7, text=f"Module zurück: {backlog}").pack(anchor="w")
        backlog_status_val = backlog_status(backlog)
        self._progress_bar(card7, backlog_status_val)


# Charts row
        charts_row = ttk.Frame(content)
        charts_row.pack(fill=tk.BOTH, expand=True)
        charts_row.columnconfigure(0, weight=1)
        charts_row.columnconfigure(1, weight=1)

        # ECTS Fortschritt per Semester
        frame_chart1 = ttk.LabelFrame(charts_row, text="ECTS-Fortschritt")
        frame_chart1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        canvas1 = tk.Canvas(frame_chart1, height=280, bg=COLOR_BG, highlightthickness=0)
        canvas1.pack(fill=tk.BOTH, expand=True)
        ects_map = ects_by_semester(semesters)
        sem_keys = sorted(ects_map.keys())
        values = [ects_map[s] for s in sem_keys]
        labels = [f"S{s}" for s in sem_keys]

        # Create colors based on ECTS status for each semester
        colors = []
        for ects in values:
            if ects > 30:
                colors.append(STATUS_COLORS["light_green"])
            elif ects == 30:
                colors.append(STATUS_COLORS["green"])
            elif ects < 25:
                colors.append(STATUS_COLORS["red"])
            else:
                colors.append(STATUS_COLORS["orange"])

        bar_chart(canvas1, (40, 250), (480, 200), values, labels, colors)

        # Notenverlauf pro Semester (nur letzte Versuche)
        frame_chart2 = ttk.LabelFrame(charts_row, text="Notenverlauf pro Semester")
        frame_chart2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        canvas2 = tk.Canvas(frame_chart2, height=280, bg=COLOR_BG, highlightthickness=0)
        canvas2.pack(fill=tk.BOTH, expand=True)
        avg_map = semester_average_grades(semesters)
        sem_keys2 = sorted(avg_map.keys())
        avg_values = [avg_map[s] for s in sem_keys2]

        grade_colors = []
        for avg in avg_values:
            grade_colors.append(STATUS_COLORS[grade_status(avg)])

        bar_chart(canvas2, (40, 250), (480, 200), avg_values, [f"S{s}" for s in sem_keys2], grade_colors)

        # Weekly Study Time Line Chart
        line_chart_frame = ttk.LabelFrame(content, text="Wöchentliche Lernzeit Verlauf")
        line_chart_frame.pack(fill=tk.X, padx=6, pady=6)

        # Create scrollable frame for the chart
        chart_container = tk.Frame(line_chart_frame)
        chart_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create canvas with scrollbar
        line_canvas = tk.Canvas(chart_container, height=250, bg=COLOR_BG, highlightthickness=0)  # Made taller
        scrollbar = ttk.Scrollbar(chart_container, orient="horizontal", command=line_canvas.xview)
        line_canvas.configure(xscrollcommand=scrollbar.set)

        line_canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")

        # Prepare data for line chart
        study_weeks = get_study_time_weeks()
        if study_weeks:
            # Sort by date
            study_weeks.sort(key=lambda x: x[0])

            # Extract values and labels
            hours_values = [week[1] for week in study_weeks]
            week_labels = []

            for week_date, _ in study_weeks:
                # Format as week number (e.g., "KW 37")
                week_num = week_date.isocalendar()[1]
                week_labels.append(f"KW {week_num}")

            weeks_to_show = min(6, len(hours_values))
            base_width = 800  # Base width for 6 weeks
            total_width = max(base_width, len(hours_values) * (base_width // weeks_to_show))

            # Set scroll region
            line_canvas.configure(scrollregion=(0, 0, total_width, 250))
            line_chart(line_canvas, (60, 200), (total_width - 120, 150), hours_values, week_labels)

            # Auto-scroll to the right to show latest weeks
            line_canvas.after(100, lambda: line_canvas.xview_moveto(1.0))
        else:
            line_canvas.create_text(400, 125, text="Keine Lernzeit-Daten vorhanden", fill="#94a3b8", font=("Segoe UI", 14))

    def _open_weekly_time_dialog(self):
        dialog = WeeklyTimeDialog(self)
        self.wait_window(dialog)

    def _progress_bar(self, parent: tk.Widget, status_key: str, height: int = 10) -> tk.Canvas:
        c = tk.Canvas(parent, height=height, bg=COLOR_BG, highlightthickness=0)
        c.pack(fill=tk.X, pady=(6, 0))

        def redraw():
            w = c.winfo_width()
            if w <= 1:
                return
            c.delete("all")
            c.create_rectangle(
                0, 0,
                self._get_progression_width(status_key, w), height,
                fill=STATUS_COLORS[status_key],
                outline=""
            )

        c.bind("<Configure>", redraw)
        return c



def run_app():
    Dashboard().mainloop()
