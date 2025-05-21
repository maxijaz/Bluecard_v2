def warn_if_start_date_not_in_days(parent, start_date_str, days_str):
    from datetime import datetime
    from PyQt5.QtWidgets import QMessageBox

    if not start_date_str:
        return True
    try:
        start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    except ValueError:
        return True

    selected_days = [d.strip() for d in days_str.split(",") if d.strip()]
    day_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    selected_indices = [day_map[day] for day in selected_days if day in day_map]
    if not selected_indices:
        return True

    if start_date.weekday() not in selected_indices:
        day_name = start_date.strftime("%A")
        days_str_disp = ", ".join(selected_days)
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Start Date Warning")
        msg.setText(
            f"Warning: The selected start date ({start_date_str}) is a {day_name}, "
            f"but you have only selected {days_str_disp}.\n\n"
            "The first class will be on this date, but subsequent classes will be on your selected days.\n"
            "Do you want to continue with this start date?"
        )
        yes_button = msg.addButton("Yes", QMessageBox.AcceptRole)
        cancel_button = msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.setDefaultButton(cancel_button)
        reply = msg.exec_()
        if msg.clickedButton() == cancel_button:
            return False
    return True