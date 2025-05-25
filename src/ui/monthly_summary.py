import json
import os
from datetime import datetime
from collections import defaultdict

def load_attendance_data(filepath=None):
    if filepath is None:
        # Go up two directories from this file, then into 'data'
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        filepath = os.path.join(base_dir, "data", "001attendance_data.json")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def is_attended(value):
    """Check if an attendance value counts as a class held."""
    return value in ("P", "COD", "CIA")  # Add others if needed


def generate_monthly_summary(data, teacher_name="Paul R"):
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

    for class_id, class_data in data["classes"].items():
        meta = class_data["metadata"]
        if meta.get("Teacher") != teacher_name:
            continue

        class_time = float(meta.get("ClassTime", "2"))
        rate = float(meta.get("rate", "0"))
        travel_rate = float(meta.get("travel", "0"))
        bonus_amount = float(meta.get("bonus", "0"))
        dates = meta.get("Dates", [])
        students = class_data.get("students", {})
        class_name = meta.get("Company", class_id)

        # Count actual held sessions per date
        class_dates_by_month = defaultdict(int)
        for date_str in dates:
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                month_key = dt.strftime("%Y-%m")

                # Check if at least one student attended
                any_attended = False
                for student in students.values():
                    attendance = student.get("attendance", {})
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
            bonus = bonus_amount if meta.get("BonusClaimed", "") == month else 0
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


def get_summary_text(data, teacher_name="Paul R"):
    summary = generate_monthly_summary(data, teacher_name)
    lines = []
    lines.append(f"{'Month':<10} {'Hours':<6} {'Travel':<8} {'Bonus':<7} {'Total Pay':<10} {'Notes'}")
    lines.append("-" * 60)
    for month in sorted(summary):
        row = summary[month]
        lines.append(f"{month:<10} {row['total_hours']:<6} {row['total_travel']:<8} {row['total_bonus']:<7} {row['total_pay']:<10} {row['notes']}")
    return "\n".join(lines)


if __name__ == "__main__":
    data = load_attendance_data("001attendance.json")
    summary = generate_monthly_summary(data, teacher_name="Paul R")
    print(get_summary_text(data, teacher_name="Paul R"))
