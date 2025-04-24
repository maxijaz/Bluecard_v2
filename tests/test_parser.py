import os
import unittest
import json
from datetime import datetime, timedelta
from src.logic.parser import (
    load_data,
    save_data,
    validate_class_format,
    backup_data,
    cleanup_old_backups,
    DATA_FILE,
    BACKUP_DIR,
)

class TestParser(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create test directories and files
        os.makedirs("data", exist_ok=True)
        self.test_data = {
            "classes": {
                "class1": {
                    "metadata": {
                        "Company": "TestCompany",
                        "Consultant": "TestConsultant",
                        "Teacher": "TestTeacher",
                        "Room": "101",
                        "CourseBook": "TestBook",
                        "MaxClasses": 10,
                        "CourseHours": 20,
                        "ClassTime": "10:00 AM",
                        "StartDate": "2025-01-01",
                        "FinishDate": "2025-06-01",
                        "Days": "Monday",
                        "Time": "10:00 AM",
                        "Notes": "Test notes",
                    },
                    "students": {
                        "student1": {
                            "name": "John Doe",
                            "gender": "Male",
                            "nickname": "Johnny",
                            "score": 85,
                            "pre_test": 80,
                            "post_test": 90,
                            "active": True,
                            "note": "Good student",
                            "attendance": [],
                        }
                    },
                }
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.test_data, f, indent=4)

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        if os.path.exists(BACKUP_DIR):
            for file in os.listdir(BACKUP_DIR):
                os.remove(os.path.join(BACKUP_DIR, file))
            os.rmdir(BACKUP_DIR)

    def test_load_data(self):
        """Test loading data from a JSON file."""
        data = load_data()
        self.assertEqual(data, self.test_data)

    def test_save_data(self):
        """Test saving data to a JSON file."""
        new_data = {"test": "data"}
        save_data(new_data)
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, new_data)

    def test_validate_class_format(self):
        """Test validation of class and student data."""
        self.assertTrue(validate_class_format(self.test_data))
        invalid_data = {"classes": {}}
        self.assertFalse(validate_class_format(invalid_data))

    def test_backup_data(self):
        """Test creating a backup of the JSON data file."""
        backup_data()
        backups = os.listdir(BACKUP_DIR)
        self.assertEqual(len(backups), 1)
        self.assertTrue(backups[0].startswith("001attendance_data_"))

    def test_cleanup_old_backups(self):
        """Test cleanup of old backups."""
        # Create multiple backups with different timestamps
        os.makedirs(BACKUP_DIR, exist_ok=True)
        for i in range(5):
            timestamp = (datetime.now() - timedelta(days=i + 100)).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"001attendance_data_{timestamp}.json"
            with open(os.path.join(BACKUP_DIR, backup_filename), "w") as f:
                f.write("{}")
        cleanup_old_backups(days=90)
        backups = os.listdir(BACKUP_DIR)
        self.assertEqual(len(backups), 0)

if __name__ == "__main__":
    unittest.main()