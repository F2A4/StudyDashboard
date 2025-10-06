import json
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, DefaultDict
from collections import defaultdict


DATA_FILE = Path(__file__).with_name("data.json")


def _parse_date(value: str) -> date:
	return datetime.strptime(value, "%Y-%m-%d").date()


@dataclass
class Course:
	name: str
	ects: int
	grade: Optional[float]
	passed: bool
	attempt: int
	date: Optional[date]


@dataclass
class SemesterGrades:
	semester: int
	courses: List[Course]


def load_json() -> Dict[str, Any]:
	with open(DATA_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def save_json(data: Dict[str, Any]) -> None:
	with open(DATA_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def _to_bool(val: Any) -> bool:
	if isinstance(val, bool):
		return val
	if val is None:
		return False
	text = str(val).strip().lower()
	return text in {"true", "1", "ja", "yes", "y"}


def get_general() -> Dict[str, Any]:
	"""Return a unified general dict with keys: ects_required, planned_duration_months, start_date.
	Supports old schema (general) and new schema (studieninfo).
	"""
	data = load_json()
	if "general" in data:
		g = data["general"]
		return {
			"ects_required": int(g.get("ects_required", g.get("total_ects", 180))),
			"planned_duration_months": int(g.get("planned_duration_months", g.get("ziel_monate", 36))),
			"start_date": g.get("start_date") or g.get("startdatum") or date.today().isoformat(),
		}
	elif "studieninfo" in data:
		s = data["studieninfo"]
		return {
			"ects_required": int(s.get("total_ects", 180)),
			"planned_duration_months": int(s.get("ziel_monate", 36)),
			"start_date": s.get("startdatum", date.today().isoformat()),
		}
	else:
		# sensible defaults
		return {
			"ects_required": 180,
			"planned_duration_months": 36,
			"start_date": date.today().isoformat(),
		}


def get_semester_grades() -> List[SemesterGrades]:
	data = load_json()
	semesters: List[SemesterGrades] = []
	if "grades" in data:
		for entry in data.get("grades", []):
			courses: List[Course] = []
			for c in entry.get("courses", []):
				courses.append(
					Course(
						name=c["name"],
						ects=int(c["ects"]),
						grade=float(c["grade"]) if c.get("grade") is not None else None,
						passed=_to_bool(c.get("passed", True)),
						attempt=int(c.get("attempt", 1)),
						date=_parse_date(c["date"]) if c.get("date") else None,
					)
				)
			semesters.append(SemesterGrades(semester=int(entry["semester"]), courses=courses))
		return semesters
	elif "exams" in data:
		bucket: DefaultDict[int, List[Course]] = defaultdict(list)
		for e in data.get("exams", []):
			grade_val: Optional[float] = float(e["note"]) if e.get("note") is not None else None
			# Pass rule: 5.0 => failed, else passed; None => passed but no grade
			passed = False if (grade_val is not None and grade_val >= 5.0) else True
			bucket[int(e["semester"])].append(
				Course(
					name=e.get("prüfungsname") or e.get("name", "Kurs"),
					ects=int(e["ects"]),
					grade=grade_val,
					passed=passed,
					attempt=int(e.get("versuch", 1)),
					date=_parse_date(e["datum"]) if e.get("datum") else None,
				)
			)
		for sem in sorted(bucket.keys()):
			semesters.append(SemesterGrades(semester=sem, courses=bucket[sem]))
		return semesters
	else:
		return []


def get_study_time_weeks() -> List[Tuple[date, float]]:
	data = load_json()
	weeks: List[Tuple[date, float]] = []
	for w in data.get("study_time", []):
		weeks.append((_parse_date(w["week_start"]), float(w["hours"])) )
	return weeks
