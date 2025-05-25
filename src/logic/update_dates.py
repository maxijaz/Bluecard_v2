from datetime import datetime


def update_dates(metadata, students):
    """
    Synchronize metadata["dates"] with students' attendance data.
    Preserve attendance values for dates with non-empty values.
    """
    # Get the current list of dates from metadata
    metadata_dates = metadata.get("dates", [])
    metadata_dates_set = set(metadata_dates)

    # Iterate through each student to update their attendance
    for student_id, student in students.items():
        attendance = student.get("attendance", {})

        # Preserve attendance for dates with non-empty values
        preserved_dates = {date: value for date, value in attendance.items() if value not in ["", "-"]}

        # Remove dates from attendance that are no longer in metadata
        for date in list(attendance.keys()):
            if date not in metadata_dates_set:
                del attendance[date]

        # Add new dates from metadata to attendance with default value "-"
        for date in metadata_dates:
            if date not in attendance:
                attendance[date] = "-"

        # Restore preserved dates
        attendance.update(preserved_dates)

        # Update the student's attendance
        student["attendance"] = attendance

    return metadata, students


def add_date(metadata, students, new_date):
    """
    Add a new date to metadata["dates"] and update students' attendance.
    """
    if new_date in metadata["dates"]:
        raise ValueError(f"The date {new_date} already exists in the schedule.")

    # Add the new date to metadata
    metadata["dates"].append(new_date)
    metadata["dates"].sort(key=lambda d: datetime.strptime(d, "%d/%m/%Y"))  # Keep dates sorted

    # Update students' attendance
    for student in students.values():
        student["attendance"][new_date] = "-"

    return update_dates(metadata, students)


def remove_date(metadata, students, date_to_remove):
    """
    Remove a date from metadata["dates"] and update students' attendance.
    """
    if date_to_remove not in metadata["dates"]:
        raise ValueError(f"The date {date_to_remove} does not exist in the schedule.")

    # Remove the date from metadata
    metadata["dates"].remove(date_to_remove)

    # Remove the date from students' attendance
    for student in students.values():
        if date_to_remove in student["attendance"]:
            del student["attendance"][date_to_remove]

    return update_dates(metadata, students)


def modify_date(metadata, students, old_date, new_date):
    """
    Modify a date in metadata["dates"] and update students' attendance.
    """
    if old_date not in metadata["dates"]:
        raise ValueError(f"The date {old_date} does not exist in the schedule.")

    if new_date in metadata["dates"]:
        raise ValueError(f"The date {new_date} already exists in the schedule.")

    # Check if the old date has preserved attendance values
    for student in students.values():
        attendance = student.get("attendance", {})
        if old_date in attendance and attendance[old_date] not in ["", "-"]:
            raise ValueError(f"The date {old_date} cannot be modified because it has preserved attendance values.")

    # Update metadata
    metadata["dates"].remove(old_date)
    metadata["dates"].append(new_date)
    metadata["dates"].sort(key=lambda d: datetime.strptime(d, "%d/%m/%Y"))  # Keep dates sorted

    # Update students' attendance
    for student in students.values():
        attendance = student.get("attendance", {})
        if old_date in attendance:
            attendance[new_date] = attendance.pop(old_date)

    return update_dates(metadata, students)