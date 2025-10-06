import tkinter as tk
from tkinter import ttk
from datetime import date

from data_store import get_general, get_semester_grades, get_study_time_weeks
from analytics import (
	weighted_average_grade,
	ects_by_semester,
	ects_current_semester_month,
	ects_status,
	pass_rate,
	repeat_ratio,
	weekly_learning_hours,
	learning_hours_status,
	backlog_modules,
	backlog_status,
	study_end_forecast,
	grade_status,
	semester_average_grades,
)
from charts import bar_chart

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
	def __init__(self) -> None:
		super().__init__()
		self.title("Studien-Dashboard")
		self.geometry("1100x750")
		self.configure(bg=COLOR_BG)
		self._build()

	def _card(self, parent: tk.Widget, title: str) -> ttk.Frame:
		frame = ttk.Frame(parent)
		frame['padding'] = 10
		return frame

	def _build(self) -> None:
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
		planned_months = general['planned_duration_months']
		start = date.fromisoformat(general['start_date'])
		planned_end = start.replace()  # placeholder to avoid linters about unused
		card1 = ttk.LabelFrame(kpi_frame, text="Studienzeit")
		card1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
		lbl = ttk.Label(card1, text=f"Prognose Enddatum: {forecast_date.isoformat()}")
		lbl.pack(anchor="w")
		status_color = STATUS_COLORS[forecast_status]
		canvas = tk.Canvas(card1, height=10, bg=COLOR_BG, highlightthickness=0)
		canvas.pack(fill=tk.X, pady=(6,0))
		canvas.create_rectangle(0, 0, 200, 10, fill=status_color, outline="")

		# 2. Durchschnittsnote
		avg = weighted_average_grade(semesters)
		card2 = ttk.LabelFrame(kpi_frame, text="Durchschnittsnote")
		card2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
		avg_txt = "-" if avg is None else f"{avg:.2f}"
		ttk.Label(card2, text=f"Aktuell: {avg_txt}").pack(anchor="w")
		canvas2 = tk.Canvas(card2, height=10, bg=COLOR_BG, highlightthickness=0)
		canvas2.pack(fill=tk.X, pady=(6,0))
		canvas2.create_rectangle(0, 0, 200, 10, fill=STATUS_COLORS[grade_status(avg)], outline="")

		# 3. ECTS im Semester/Monat
		sem_ects, month_ects = ects_current_semester_month(semesters)
		sem_status, month_status = ects_status(sem_ects, month_ects)
		card3 = ttk.LabelFrame(kpi_frame, text="ECTS")
		card3.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
		ttk.Label(card3, text=f"Aktuelles Semester: {sem_ects} ECTS").pack(anchor="w")
		ttk.Label(card3, text=f"Diesen Monat: {month_ects} ECTS").pack(anchor="w")
		c3 = tk.Canvas(card3, height=10, bg=COLOR_BG, highlightthickness=0)
		c3.pack(fill=tk.X, pady=(6,0))
		c3.create_rectangle(0, 0, 200, 10, fill=STATUS_COLORS[sem_status], outline="")

		# 4. Bestehensquote
		rate = pass_rate(semesters)
		card4 = ttk.LabelFrame(kpi_frame, text="Bestehensquote")
		card4.grid(row=0, column=3, sticky="nsew", padx=6, pady=6)
		rate_txt = "-" if rate is None else f"{int(rate*100)}%"
		ttk.Label(card4, text=f"Dieses Semester: {rate_txt}").pack(anchor="w")

		# Row 2 KPIs
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

		# Lernzeit
		w_hours = weekly_learning_hours(weeks)
		card6 = ttk.LabelFrame(kpi2, text="Wöchentliche Lernzeit")
		card6.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
		w_txt = "-" if w_hours is None else f"{w_hours} h"
		ttk.Label(card6, text=f"Letzte Woche: {w_txt}").pack(anchor="w")
		c6 = tk.Canvas(card6, height=10, bg=COLOR_BG, highlightthickness=0)
		c6.pack(fill=tk.X, pady=(6,0))
		c6.create_rectangle(0, 0, 200, 10, fill=STATUS_COLORS[learning_hours_status(w_hours)], outline="")

		# Backlog
		months_since_start = max(0, (date.today().year - date.fromisoformat(general['start_date']).year) * 12 + (date.today().month - date.fromisoformat(general['start_date']).month))
		backlog = backlog_modules(semesters, months_since_start)
		card7 = ttk.LabelFrame(kpi2, text="Nachhol-Backlog")
		card7.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
		ttk.Label(card7, text=f"Module zurück: {backlog}").pack(anchor="w")
		c7 = tk.Canvas(card7, height=10, bg=COLOR_BG, highlightthickness=0)
		c7.pack(fill=tk.X, pady=(6,0))
		c7.create_rectangle(0, 0, 200, 10, fill=STATUS_COLORS[backlog_status(backlog)], outline="")

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
		bar_chart(canvas1, (40, 250), (480, 200), values, labels)

		# Notenverlauf pro Semester (nur letzte Versuche)
		frame_chart2 = ttk.LabelFrame(charts_row, text="Notenverlauf pro Semester")
		frame_chart2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
		canvas2 = tk.Canvas(frame_chart2, height=280, bg=COLOR_BG, highlightthickness=0)
		canvas2.pack(fill=tk.BOTH, expand=True)
		avg_map = semester_average_grades(semesters)
		sem_keys2 = sorted(avg_map.keys())
		avg_values = [avg_map[s] for s in sem_keys2]
		bar_chart(canvas2, (40, 250), (480, 200), avg_values, [f"S{s}" for s in sem_keys2])


def run_app() -> None:
	Dashboard().mainloop()
