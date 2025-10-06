from typing import List, Tuple, Optional
import tkinter as tk

ColorBG = "#ffffff"
ColorAxis = "#94a3b8"
ColorBar = "#10b981"
ColorBarAlt = "#f59e0b"


def draw_axis(canvas: tk.Canvas, x: int, y: int, width: int, height: int) -> None:
	canvas.create_line(x, y, x, y - height, fill=ColorAxis)
	canvas.create_line(x, y, x + width, y, fill=ColorAxis)


def bar_chart(canvas: tk.Canvas, origin: Tuple[int, int], size: Tuple[int, int], values: List[float], labels: List[str], colors: Optional[List[str]] = None) -> None:
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
