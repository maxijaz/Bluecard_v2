import json
import os
from datetime import datetime
from collections import defaultdict
from logic.db_interface import get_all_classes, get_students_by_class, get_attendance_by_student

def is_attended(value):
    """Check if an attendance value counts as a class held."""
    return value in ("P", "COD", "CIA")  # Add others if needed

def generate_monthly_summary(teacher_name="Paul R"):
    """
    Build a monthly summary across all classes taught by a given teacher.

    Returns:
        Dict of the form:
        {
            "2025-05": {
                "total_hours": 20,
                "total_travel": 4000,
                "total_bonus": 1000,
                "total_pay": 15400,
                "notes": "1 class"
            },
            ...
        }
    """
    summary = defaultdict(lambda: {
        "total_hours": 0,
        "total_travel": 0,
        "total_bonus": 0,
        "total_pay": 0,
        "notes": set()
    })

    for class_row in get_all_classes():
        if class_row.get("teacher") != teacher_name:
            continue

        class_time = float(class_row.get("class_time", "2"))
        rate = float(class_row.get("rate", "0"))
        travel_rate = float(class_row.get("travel", "0"))
        bonus_amount = float(class_row.get("bonus", "0"))
        dates = class_row.get("dates", [])
        class_name = class_row.get("company", class_row.get("class_no", ""))

        # Get all students for this class
        students = get_students_by_class(class_row["class_no"])

        # Count actual held sessions per date
        class_dates_by_month = defaultdict(int)
        for date_str in dates:
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                month_key = dt.strftime("%Y-%m")

                # Check if at least one student attended
                any_attended = False
                for student in students:
                    attendance_records = get_attendance_by_student(student["student_id"])
                    attendance = {rec["date"]: rec["status"] for rec in attendance_records}
                    if is_attended(attendance.get(date_str, "")):
                        any_attended = True
                        break

                if any_attended:
                    class_dates_by_month[month_key] += 1
            except ValueError:
                continue

        # Now summarize for each month where this class had sessions
        for month, count in class_dates_by_month.items():
            hours = count * class_time
            travel = count * travel_rate
            # If you have a lowercase "bonus_claimed" field, use that; otherwise, remove this logic or adapt as needed
            bonus = bonus_amount if class_row.get("bonus_claimed", "") == month else 0
            pay = hours * rate + travel + bonus

            summary[month]["total_hours"] += hours
            summary[month]["total_travel"] += travel
            summary[month]["total_bonus"] += bonus
            summary[month]["total_pay"] += pay
            summary[month]["notes"].add(class_name)

    # Final formatting
    for month in summary:
        summary[month]["notes"] = f"{len(summary[month]['notes'])} class(es)"

    return summary

def get_summary_text(teacher_name="Paul R"):
    summary = generate_monthly_summary(teacher_name)
    lines = []
    lines.append(f"{'Month':<10} {'Hours':<6} {'Travel':<8} {'Bonus':<7} {'Total Pay':<10} {'Notes'}")
    lines.append("-" * 60)
    for month in sorted(summary):
        row = summary[month]
        lines.append(f"{month:<10} {row['total_hours']:<6} {row['total_travel']:<8} {row['total_bonus']:<7} {row['total_pay']:<10} {row['notes']}")
    return "\n".join(lines)

if __name__ == "__main__":
    print(get_summary_text("Paul R"))
