from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from data_store import SemesterGrades, Course, get_general


@dataclass
class KPIStatus:
	value: float
	status: str  # light_green, green, orange, red
	label: str


def _latest_course_map(semesters: Iterable[SemesterGrades]):
	latest: Dict[str, Tuple[Course, int]] = {}
	for s in semesters:
		for c in s.courses:
			key = c.name
			if key not in latest:
				latest[key] = (c, s.semester)
				continue
			cur, cur_sem = latest[key]
			if c.attempt > cur.attempt:
				latest[key] = (c, s.semester)
			elif c.attempt == cur.attempt:
				if (c.date or date.min) > (cur.date or date.min):
					latest[key] = (c, s.semester)
	return latest


def _latest_courses_list(semesters: Iterable[SemesterGrades]):
	return [c for c, _ in _latest_course_map(semesters).values()]


def semester_average_grades(semesters: Iterable[SemesterGrades]):
	latest = _latest_course_map(list(semesters))
	acc: Dict[int, Tuple[float, int]] = {}
	for c, sem in latest.values():
		if sem == 0:
			continue
		if c.grade is None:
			continue
		total, ects = acc.get(sem, (0.0, 0))
		acc[sem] = (total + c.grade * c.ects, ects + c.ects)
	return {sem: round(total / ects, 2) if ects else 0.0 for sem, (total, ects) in acc.items()}


def weighted_average_grade(semesters: Iterable[SemesterGrades]):
	courses = _latest_courses_list(list(semesters))
	sum_weighted = 0.0
	sum_ects = 0
	for c in courses:
		if c.grade is None:
			continue
		sum_weighted += c.grade * c.ects
		sum_ects += c.ects
	if sum_ects == 0:
		return None
	return round(sum_weighted / sum_ects, 2)


def ects_by_semester(semesters: Iterable[SemesterGrades]):
	latest = _latest_course_map(list(semesters))
	result: Dict[int, int] = {}
	for course, sem in latest.values():
		if sem == 0:
			continue
		if course.passed:
			result[sem] = result.get(sem, 0) + course.ects
	return result


def ects_current_semester_month(semesters: Iterable[SemesterGrades], today: Optional[date] = None):
	latest = _latest_course_map(list(semesters))
	if not latest:
		return 0, 0
	sems = [sem for _, sem in latest.values()]
	pos_sems = [s for s in sems if s > 0]
	current_sem = max(pos_sems) if pos_sems else max(sems)
	sem_ects = sum(c.ects for c, sem in latest.values() if sem == current_sem and c.passed)
	today = today or date.today()
	month_ects = 0
	for c, sem in latest.values():
		if sem == current_sem and c.passed and c.date and c.date.year == today.year and c.date.month == today.month:
			month_ects += c.ects
	return sem_ects, month_ects


def ects_status(sem_ects: int, month_ects: int):
	if month_ects >= 10:
		m = "light_green"
	elif month_ects >= 5:
		m = "green"
	elif month_ects == 0:
		m = "red"
	else:
		m = "orange"

	if sem_ects > 30:
		s = "light_green"
	elif sem_ects == 30:
		s = "green"
	elif sem_ects < 25:
		s = "red"
	else:
		s = "orange"
	return s, m


def pass_rate(semesters: Iterable[SemesterGrades]):
	courses = _latest_courses_list(list(semesters))
	attempted = 0
	passed = 0
	for c in courses:
		if c.grade is not None:
			attempted += 1
			if c.passed:
				passed += 1
	if attempted == 0:
		return None
	return round(passed / attempted, 2)


def repeat_ratio(semesters: Iterable[SemesterGrades]):
	courses = _latest_courses_list(list(semesters))
	failed = 0
	success_after_repeat = 0
	for c in courses:
		if c.grade is None:
			continue
		if not c.passed:
			failed += 1
		if c.passed and c.attempt > 1:
			success_after_repeat += 1
	if success_after_repeat == 0:
		return None if failed == 0 else float("inf")
	return round(failed / success_after_repeat, 2)


def weekly_learning_hours(weeks: Iterable[Tuple[date, float]]):
	weeks = list(weeks)
	if not weeks:
		return None
	return round(weeks[-1][1], 1)


def learning_hours_status(hours: float):
    if hours is None:
        return "red"
    if 25 <= hours <= 30:
        return "green"
    if hours > 30:
        return "light_green"
    return "orange"



def backlog_modules(semesters: Iterable[SemesterGrades], months_since_start: int):
	# expectation: 5 ECTS per month, only count ECTS from latest passed attempts
	general = get_general()
	required = int(general["ects_required"])
	completed = 0
	for c in _latest_courses_list(list(semesters)):
		if c.passed:
			completed += c.ects
	expected_ects = 5 * months_since_start
	behind = max(0, expected_ects - completed)
	# 1 module ~ 5 ECTS
	return behind // 5


def backlog_status(count: int):
	if count == 0:
		return "green"
	if count == 1:
		return "orange"
	return "red"


def study_end_forecast(semesters: Iterable[SemesterGrades]):
	general = get_general()
	start = date.fromisoformat(general["start_date"])
	planned_months = int(general["planned_duration_months"])
	planned_end = start + timedelta(days=planned_months * 30)

	required_total = int(general["ects_required"])
	# Split completed into credited (semester 0) and earned in real semesters (>0)
	credited_sem0 = 0
	completed_non0 = 0
	from_this = _latest_course_map(list(semesters))
	for c, sem in from_this.values():
		if c.passed:
			if sem == 0:
				credited_sem0 += c.ects
			else:
				completed_non0 += c.ects

	# Remaining ECTS needed exclude credits from semester 0
	remaining = max(0, (required_total - credited_sem0) - completed_non0)

	# average ECTS per semester from history (latest attempts, excluding semester 0)
	by_sem = ects_by_semester(list(semesters))  # already excludes 0
	sem_ects = list(by_sem.values())
	avg_semester_ects = max(1.0, (sum(sem_ects) / len(sem_ects))) if sem_ects else 30.0
	# convert to months: assume 6 months per semester
	avg_month_ects = avg_semester_ects / 6.0
	months_needed = int((remaining / avg_month_ects) if avg_month_ects > 0 else 0)
	forecast_end = date.today() + timedelta(days=months_needed * 30)

	# color logic
	if forecast_end < planned_end:
		status = "light_green"
	elif forecast_end == planned_end:
		status = "green"
	elif forecast_end <= planned_end + timedelta(days=30):
		status = "orange"
	else:
		status = "red"
	return forecast_end, status


def grade_status(avg: Optional[float]):
	if avg is None:
		return "orange"
	if avg < 1.8:
		return "light_green"
	if 1.8 <= avg < 2.0:
		return "green"
	if 2.0 <= avg < 2.5:
		return "orange"
	return "red"
