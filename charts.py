from typing import List, Tuple, Optional
import tkinter as tk

ColorBG = "#ffffff"
ColorAxis = "#94a3b8"
ColorBar = "#10b981"
ColorBarAlt = "#f59e0b"


def draw_axis(canvas: tk.Canvas, x: int, y: int, width: int, height: int):
	canvas.create_line(x, y, x, y - height, fill=ColorAxis)
	canvas.create_line(x, y, x + width, y, fill=ColorAxis)


def bar_chart(canvas: tk.Canvas, origin: Tuple[int, int], size: Tuple[int, int], values: List[float], labels: List[str], colors: Optional[List[str]] = None):
	x0, y0 = origin
	width, height = size
	draw_axis(canvas, x0, y0, width, height)
	if not values:
		return
	max_val = max(values) or 1
	bar_w = max(10, int(width / (len(values) * 1.5)))
	gap = int(bar_w * 0.5)
	for i, v in enumerate(values):
		x = x0 + 10 + i * (bar_w + gap)
		bar_h = int((v / max_val) * (height - 10))
		color = colors[i] if colors and i < len(colors) else ColorBar
		canvas.create_rectangle(x, y0 - bar_h, x + bar_w, y0, fill=color, outline="")
		canvas.create_text(x + bar_w // 2, y0 + 12, text=labels[i], fill="#475569", font=("Segoe UI", 9))
		canvas.create_text(x + bar_w // 2, y0 - bar_h - 10, text=str(v), fill="#334155", font=("Segoe UI", 9))


def line_chart(canvas: tk.Canvas, origin: Tuple[int, int], size: Tuple[int, int], values: List[float], labels: List[str], color: str = "#10b981"):
	x0, y0 = origin
	width, height = size
	draw_axis(canvas, x0, y0, width, height)
	
	if not values or len(values) < 2:
		# Error Message
		canvas.create_text(x0 + width // 2, y0 - height // 2, text="Keine Daten", fill="#94a3b8", font=("Segoe UI", 12))
		return
	
	# fixed 50-hour scale
	max_val = max(values) or 1
	max_scale = max(50, max_val)
	
	# Calculate points for the line
	points = []
	for i, v in enumerate(values):
		x = x0 + 20 + (i * (width - 40) / (len(values) - 1))
		y = y0 - 20 - (v / max_scale) * (height - 40)
		points.append((x, y))
	
	# Draw the line
	for i in range(len(points) - 1):
		x1, y1 = points[i]
		x2, y2 = points[i + 1]
		canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
	
	# Draw points
	for i, (x, y) in enumerate(points):
		# Draw circle for each point
		canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")
		
		# Draw value labels above points
		canvas.create_text(x, y - 15, text=f"{values[i]:.1f}h", fill="#334155", font=("Segoe UI", 8))
		
		# Draw week labels below x-axis
		if i < len(labels):
			canvas.create_text(x, y0 + 15, text=labels[i], fill="#475569", font=("Segoe UI", 8))
	
	# Draw y-axis labels with 5-hour steps
	max_scale = max(50, max_val)
	y_steps = 10  # 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50
	for i in range(y_steps + 1):
		value = i * 5  # 5-hour increments
		y = y0 - 20 - (value / max_scale) * (height - 40)
		canvas.create_text(x0 - 10, y, text=f"{value:.0f}", fill="#475569", font=("Segoe UI", 8), anchor="e")
	
	# Draw target lines at 25h and 30h
	if max_scale >= 25:
		y25 = y0 - 20 - (25 / max_scale) * (height - 40)
		canvas.create_line(x0 + 20, y25, x0 + width - 20, y25, fill="#ef4444", width=1, dash=(5, 5))
		canvas.create_text(x0 + width - 15, y25, text="25h", fill="#ef4444", font=("Segoe UI", 8), anchor="w")
	
	if max_scale >= 30:
		y30 = y0 - 20 - (30 / max_scale) * (height - 40)
		canvas.create_line(x0 + 20, y30, x0 + width - 20, y30, fill="#ef4444", width=1, dash=(5, 5))
		canvas.create_text(x0 + width - 15, y30, text="30h", fill="#ef4444", font=("Segoe UI", 8), anchor="w")