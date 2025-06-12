import os
import random
import pandas as pd
import numpy as np
from faker import Faker

# --- CONFIGURATION ---
OUTPUT_DIR = "C:/Temp/Bluecard_v2/data"
BASE_FILENAME = "randomized_student_data"
FILE_EXTENSION = ".xlsx"
STUDENT_COUNT = 50
GENDER_OPTIONS = ["male", "female"]

# --- INITIALIZE ---
fake = Faker()
# Optional: comment out the next 3 lines for different results every time
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# --- STUDENT DATA GENERATION FUNCTION ---
def generate_student():
    fullname = fake.name()
    nickname = fake.first_name()
    company_no = str(random.randint(100000, 9999999999))
    gender = random.choice(GENDER_OPTIONS)
    score = f"{random.randint(1, 99)}%"
    pre_test = f"{random.randint(1, 99)}%"
    post_test = f"{random.randint(1, 99)}%"
    note = " ".join(fake.words(nb=random.randint(1, 5)))
    return [fullname, nickname, company_no, gender, score, pre_test, post_test, note]

# --- GENERATE STUDENTS ---
students = [generate_student() for _ in range(STUDENT_COUNT)]

# --- CREATE DATAFRAME ---
df = pd.DataFrame(students, columns=[
    "Fullname", "Nickname", "Company No", "Gender", 
    "Score", "Pre-Test", "Post-Test", "Note"
])

# --- RANDOMIZE ORDER ---
df = df.sample(frac=1).reset_index(drop=True)

# --- CREATE OUTPUT DIRECTORY IF NEEDED ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- AUTO-NUMBERED FILENAME TO PREVENT OVERWRITE ---
counter = 1
while True:
    filename = f"{BASE_FILENAME} ({counter}){FILE_EXTENSION}"
    full_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(full_path):
        break
    counter += 1

# --- SAVE TO EXCEL ---
df.to_excel(full_path, index=False)
print(f"✅ File saved: {full_path}")
