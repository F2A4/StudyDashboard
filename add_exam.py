import json
import argparse
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional

DATA_FILE = Path(__file__).with_name("data.json")


def load_json() -> Dict[str, Any]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fehler: Datei {DATA_FILE} nicht gefunden!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Fehler beim Lesen der JSON-Datei: {e}")
        sys.exit(1)


def save_json(data: Dict[str, Any]) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("[OK] Exam erfolgreich hinzugefügt!")
    except Exception as e:
        print(f"Fehler beim Speichern: {e}")
        sys.exit(1)


def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Ungültiges Datum: {date_str}. Erwartetes Format: YYYY-MM-DD")


def validate_grade(grade_str: Optional[str]) -> Optional[float]:
    if grade_str is None:
        return None
    try:
        grade = float(grade_str)
        if not (1.0 <= grade <= 5.0):
            raise ValueError("Note muss zwischen 1.0 und 5.0 liegen")
        return grade
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Ungültige Note: {e}")


def validate_ects(ects_str: str) -> int:
    try:
        ects = int(ects_str)
        if ects <= 0:
            raise ValueError("ECTS müssen positiv sein")
        return ects
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Ungültige ECTS: {e}")


def add_exam(
    semester: int,
    name: str,
    ects: int,
    date: str,
    grade: Optional[float] = None,
    versuch: int = 1
) -> None:
    
    # Lade aktuelle Daten
    data = load_json()
    
    # Stelle sicher, dass 'exams' Array existiert
    if "exams" not in data:
        data["exams"] = []
    
    # Erstelle neues Exam-Objekt
    new_exam = {
        "semester": semester,
        "prüfungsname": name,
        "ects": ects,
        "versuch": versuch,
        "datum": date
    }
    
    # Füge Note hinzu, falls vorhanden
    if grade is not None:
        new_exam["note"] = grade
    
    # Füge Exam hinzu
    data["exams"].append(new_exam)
    
    # Speichere Daten
    save_json(data)
    
    # Zeige Zusammenfassung
    print(f"\n[+] Neues Exam hinzugefügt:")
    print(f"   Semester: {semester}")
    print(f"   Name: {name}")
    print(f"   ECTS: {ects}")
    print(f"   Datum: {date}")
    print(f"   Versuch: {versuch}")
    if grade is not None:
        print(f"   Note: {grade}")
    else:
        print(f"   Note: (noch nicht geschrieben)")


def list_exams() -> None:
    data = load_json()
    exams = data.get("exams", [])
    
    if not exams:
        print("Keine Exams vorhanden.")
        return
    
    print(f"\n[LISTE] Vorhandene Exams ({len(exams)}):")
    print("-" * 80)
    
    for i, exam in enumerate(exams, 1):
        semester = exam.get("semester", "?")
        name = exam.get("prüfungsname", "Unbekannt")
        ects = exam.get("ects", "?")
        date = exam.get("datum", "?")
        versuch = exam.get("versuch", 1)
        note = exam.get("note")
        
        note_str = f"Note: {note}" if note is not None else "Noch nicht geschrieben"
        print(f"{i:2d}. S{semester} | {name} | {ects} ECTS | {date} | V{versuch} | {note_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Fügt neue Exams zur StudyDashboard JSON-Datei hinzu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Neues Exam ohne Note hinzufügen
  python add_exam.py -s 2 -n "Datenbanken" -e 5 -d "2025-11-15"
  
  # Neues Exam mit Note hinzufügen
  python add_exam.py -s 2 -n "Datenbanken" -e 5 -d "2025-11-15" -g 2.3
  
  # Wiederholungsprüfung hinzufügen
  python add_exam.py -s 1 -n "Mathematik" -e 5 -d "2025-12-01" -g 3.0 -v 2
  
  # Alle Exams anzeigen
  python add_exam.py --list
        """
    )
    
    parser.add_argument(
        "-s", "--semester",
        type=int,
        help="Semester (z.B. 1, 2, 3...)"
    )
    
    parser.add_argument(
        "-n", "--name",
        help="Name der Prüfung"
    )
    
    parser.add_argument(
        "-e", "--ects",
        type=validate_ects,
        help="ECTS-Punkte"
    )
    
    parser.add_argument(
        "-d", "--date",
        type=validate_date,
        help="Prüfungsdatum (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "-g", "--grade",
        type=validate_grade,
        help="Note (1.0-5.0, optional)"
    )
    
    parser.add_argument(
        "-v", "--versuch",
        type=int,
        default=1,
        help="Versuch (Standard: 1)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="Zeigt alle vorhandenen Exams an"
    )
    
    args = parser.parse_args()
    
    # Wenn --list angegeben, zeige Exams und beende
    if args.list:
        list_exams()
        return
    
    # Validiere, dass alle erforderlichen Argumente vorhanden sind
    required_args = ["semester", "name", "ects", "date"]
    missing_args = [arg for arg in required_args if getattr(args, arg) is None]
    
    if missing_args:
        print(f"Fehler: Folgende Argumente sind erforderlich: {', '.join(missing_args)}")
        print("Verwenden Sie --help für weitere Informationen.")
        sys.exit(1)
    
    # Validiere Semester
    if args.semester < 1:
        print("Fehler: Semester muss mindestens 1 sein.")
        sys.exit(1)
    
    # Validiere Versuch
    if args.versuch < 1:
        print("Fehler: Versuch muss mindestens 1 sein.")
        sys.exit(1)
    
    # Füge Exam hinzu
    add_exam(
        semester=args.semester,
        name=args.name,
        ects=args.ects,
        date=args.date,
        grade=args.grade,
        versuch=args.versuch
    )


if __name__ == "__main__":
    main()
