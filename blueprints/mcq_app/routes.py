from flask import Blueprint, render_template, redirect, session, url_for, request, flash
import pandas as pd
import os
import random

mcq_blueprint = Blueprint('mcq', __name__)

# Define file paths and other constants
mcq_file = "E:\DSA july\Internship\Automated Grading System\data\mcq\Python_40_MCQ_Questions_Modified_Updated.xlsx"
student_file = "E:\DSA july\Internship\Automated Grading System\data\Kerala_Student_Records_Final.xlsx."
csv_file_path = "E:\DSA july\Internship\Automated Grading System\data\mcq\MCQ_Results_Updated_Cleaned_v3.csv"

# Define correct headers
expected_columns = [
    "Reg No.", "Name", "Score", "Low Level Score", "Medium Level Score", 
    "High Level Score", "Unknown Level Score", "Feedback", "Badge", "Streak", 
    "Previous Score", "Improvement"
]

# Ensure CSV file is correctly formatted
if os.path.exists(csv_file_path):
    try:
        results_df = pd.read_csv(csv_file_path, dtype=str)
        if not all(col in results_df.columns for col in expected_columns):
            results_df = results_df.reindex(columns=expected_columns, fill_value="")
            results_df.to_csv(csv_file_path, index=False)
        recorded_students = set(results_df["Reg No."].astype(str)) if not results_df.empty else set()
    except pd.errors.ParserError:
        results_df = pd.DataFrame(columns=expected_columns)
        results_df.to_csv(csv_file_path, index=False)
        recorded_students = set()
else:
    results_df = pd.DataFrame(columns=expected_columns)
    results_df.to_csv(csv_file_path, index=False)
    recorded_students = set()

# Load datasets
mcqs = pd.read_excel(mcq_file)
student = pd.read_excel(student_file)
mcqs_dict = mcqs.to_dict(orient="records")
students_dict = student.to_dict(orient="records")

# Define number of questions per level
QUESTIONS_PER_LEVEL = 5

# Function to select random questions
def select_questions(level):
    questions = [q for q in mcqs_dict if q.get("Level") == level]
    random.shuffle(questions)
    return questions[:QUESTIONS_PER_LEVEL]

# --- Home Route for MCQ ---
@mcq_blueprint.route("/", methods=["GET", "POST"])
def home():
    if "reg_no" not in session or "name" not in session:
        return redirect(url_for("login"))  # Redirect to global login route if not logged in

    reg_no = session["reg_no"]  # Use reg_no from session
    name = session["name"]

    # Fetch student details
    found_student = next((s for s in students_dict if str(s["Reg No."]) == reg_no), None)
    if not found_student:
        flash("❌ Student not found.", "error")
        return redirect(url_for("home"))

    # Select 5 random questions for each level
    low_questions = select_questions("Low")
    medium_questions = select_questions("Medium")
    high_questions = select_questions("High")

    # Combine all selected questions
    session["all_questions"] = low_questions + medium_questions + high_questions

    # Initialize session variables
    session["questions"] = low_questions  # Start with Low-level questions
    session["current_level"] = "Low"
    session["total_questions_attempted"] = 0
    session["answers"] = []

    return redirect(url_for("mcq.quiz"))  # Redirect to quiz page

# --- Quiz Route for MCQ ---
@mcq_blueprint.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "reg_no" not in session or "name" not in session:
        return redirect(url_for("login"))  # Redirect to global login route if not logged in

    reg_no = session["reg_no"]  # Use reg_no from session
    name = session["name"]

    if request.method == "POST":
        # Record the answer
        answer = request.form.get("answer")
        session["answers"].append(answer)
        session["total_questions_attempted"] += 1

        # Check if we need to move to the next level
        if session["total_questions_attempted"] % QUESTIONS_PER_LEVEL == 0:
            correct_count = 0
            start_index = len(session["answers"]) - QUESTIONS_PER_LEVEL
            for i in range(start_index, len(session["answers"])):
                question_index = i % QUESTIONS_PER_LEVEL
                correct_answer = session["questions"][question_index]["Correct Answer"]
                if session["answers"][i] == str(correct_answer):
                    correct_count += 1

            accuracy = (correct_count / QUESTIONS_PER_LEVEL) * 100
            if accuracy >= 50:
                if session["current_level"] == "Low":
                    session["current_level"] = "Medium"
                    session["questions"] = session["all_questions"][QUESTIONS_PER_LEVEL:2 * QUESTIONS_PER_LEVEL]  # Medium-level questions
                elif session["current_level"] == "Medium":
                    session["current_level"] = "High"
                    session["questions"] = session["all_questions"][2 * QUESTIONS_PER_LEVEL:3 * QUESTIONS_PER_LEVEL]  # High-level questions
                elif session["current_level"] == "High":
                    return redirect(url_for("mcq.result"))
            else:
                return redirect(url_for("mcq.result"))

    if session["total_questions_attempted"] >= 15:
        return redirect(url_for("mcq.result"))

    # Get the current question
    question_index = session["total_questions_attempted"] % QUESTIONS_PER_LEVEL
    question = session["questions"][question_index]
    options = [question[col] for col in question.keys() if "Option" in col]

    return render_template("mcq/quiz.html", question=question, options=options, question_number=session["total_questions_attempted"] + 1)

# --- Result Route for MCQ ---
@mcq_blueprint.route("/result")
def result():
    if "reg_no" not in session or "name" not in session:
        return redirect(url_for("login"))  # Redirect to global login route if not logged in

    reg_no = session["reg_no"]  # Use reg_no from session
    name = session["name"]
    result = evaluate_student(session["reg_no"], session["answers"])
    if not result:
        return redirect(url_for("home"))

   
    return render_template("mcq/result.html", result=result)

# --- Function to evaluate the student ---
def evaluate_student(Reg_No, answers):
    global results_df, recorded_students
    Reg_No = str(Reg_No).strip()
    
    name = session.get("name", "Unknown")  # Get name from session or use default
    name = str(name).strip()

    # Fix: Filter previous records correctly using both Reg_No and Name
    prev_record = results_df[(results_df["Reg No."] == Reg_No) & (results_df["Name"] == name)]

    # Fix: Ensure is_first_attempt checks both Reg_No and Name
    is_first_attempt = (Reg_No not in recorded_students) and (name not in recorded_students)

    # Handle previous_score correctly
    previous_score = 0
    if not prev_record.empty:
        previous_score_str = prev_record["Score"].values[0]
        if isinstance(previous_score_str, str) and previous_score_str.isdigit():
            previous_score = int(previous_score_str)
        elif isinstance(previous_score_str, (int, float)):
            previous_score = int(previous_score_str)

    # Fetch student details
    found_student = next((s for s in students_dict if str(s["Reg No."]) == Reg_No), None)
    if not found_student:
        flash("❌ Student not found.", "error")
        return None

    level_scores = {"Low": 0, "Medium": 0, "High": 0, "Unknown": 0}
    level_totals = {"Low": 0, "Medium": 0, "High": 0, "Unknown": 0}
    streak = 0

    # Iterate through all questions and answers
    for i in range(len(answers)):
        question = session["all_questions"][i]
        level = question.get("Level", "Unknown")
        level_totals[level] += 1

        correct_answer = str(question["Correct Answer"]).strip()
        if answers[i] == correct_answer:
            level_scores[level] += 1
            streak += 1
        else:
            streak = 0

    total_score = sum(level_scores.values())
    badge = "🏆 Python Pro" if total_score == 15 else "🌟 Python Enthusiast" if total_score >= 5 else "🚀 Keep Practicing"

    feedback = []
    for level in ["Low", "Medium", "High", "Unknown"]:
        if level_totals[level] > 0:
            accuracy = (level_scores[level] / level_totals[level]) * 100
            if accuracy >= 80:
                feedback.append(f"✅ Excellent at {level}-level questions.")
            elif accuracy >= 50:
                feedback.append(f"📘 Good at {level}-level questions but needs improvement.")
            else:
                feedback.append(f"❗ Weak at {level}-level questions. Needs practice.")

    feedback_text = " | ".join(feedback)

    # Determine improvement status
    if is_first_attempt:
        improvement = "First Attempt"
    else:
        if total_score > previous_score:
            improvement = "📈 Improved"
        elif total_score == previous_score:
            improvement = "No Change"
        else:
            improvement = "📉 Declined"

    new_result = pd.DataFrame([{
        "Reg No.": Reg_No,
        "Name": found_student["Name"],  # ✅ Ensure correct column name
        "Score": total_score,
        "Low Level Score": level_scores["Low"],
        "Medium Level Score": level_scores["Medium"],
        "High Level Score": level_scores["High"],
        "Unknown Level Score": level_scores["Unknown"],
        "Feedback": feedback_text,
        "Badge": badge,
        "Streak": streak,
        "Previous Score": previous_score,
        "Improvement": improvement
    }])

    # Fix: Update results_df while ensuring the column name is correct
    results_df = pd.concat([
        results_df[(results_df["Reg No."] != Reg_No) | (results_df["Name"] != name)],  # ✅ Fixed column name
        new_result
    ], ignore_index=True)

    results_df.to_csv(csv_file_path, index=False)
    print("✅ Results written to file:", csv_file_path)

    # Add the student to the set of recorded students to prevent duplicates
    recorded_students.add(name)
    recorded_students.add(Reg_No)

    return {
        "Name": found_student["Name"],
        "Score": total_score,
        "Badge": badge,
        "Feedback": feedback_text,
        "Improvement": improvement
    }
