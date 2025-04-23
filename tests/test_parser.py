import unittest
import json  # Import the json module
from ..src.logic.parser import load_data, save_data, validate_class_format

class TestParser(unittest.TestCase):
    def test_validate_class_format_valid(self):
        valid_data = {
            "classes": {
                "OLO123": {
                    "metadata": {
                        "Company": "ACERs",
                        "Consultant": "Fraser",
                        "Teacher": "Paul R",
                        "Room": "Floor 23",
                        "CourseBook": "IEX",
                        "MaxClasses": 10,
                        "CourseHours": 40,
                        "ClassTime": 2,
                        "StartDate": "01/05/2025",
                        "FinishDate": "15/06/2025",
                        "Days": "Tuesday, Thursday",
                        "Time": "17:00 - 19:00",
                        "Notes": "Bring Projector and screen"
                    },
                    "students": {
                        "S001": {
                            "name": "Alice Kim",
                            "gender": "Female",
                            "nickname": "Ali",
                            "score": "82% - A",
                            "pre_test": "70%",
                            "post_test": "90%",
                            "active": "Yes",
                            "note": "Very punctual and loves discussions",
                            "attendance": {
                                "01/05/2025": "P",
                                "06/05/2025": "A"
                            }
                        }
                    }
                }
            }
        }
        self.assertTrue(validate_class_format(valid_data))

    def test_validate_class_format_invalid(self):
        invalid_data = {"classes": {}}
        self.assertFalse(validate_class_format(invalid_data))

    def test_load_data_file_not_found(self):
        data = load_data("nonexistent.json")
        self.assertEqual(data, {})

    def test_save_data(self):
        test_data = {"test": "data"}
        save_data(test_data, "test_output.json")
        with open("test_output.json", "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        self.assertEqual(test_data, loaded_data)

if __name__ == "__main__":
    unittest.main()

{
  "terminal.integrated.env.windows": {
    "PYTHONPATH": "c:\\Temp\\Bluecard_v2"
  }
}