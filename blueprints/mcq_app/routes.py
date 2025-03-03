import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, send_file

mcq_blueprint = Blueprint('mcq', __name__, url_prefix='/mcq')

# Paths for datasets
MCQ_FILE = "data/mcq/Python_40_MCQ_Questions.xlsx"
STUDENTS_FILE = "data/mcq/Kerala_Student_Records_Final.xlsx"
RESULT_FILE = "data/mcq/MCQ_Results.csv"

# Load datasets
try:
    mcqs = pd.read_excel(MCQ_FILE, engine="openpyxl")
    students = pd.read_excel(STUDENTS_FILE, engine="openpyxl")
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit()

students_dict = students.to_dict(orient="records")
mcqs_dict = mcqs.to_dict(orient="records")

if not os.path.exists(RESULT_FILE):
    pd.DataFrame(columns=["Reg No.", "Name", "Score"]).to_csv(RESULT_FILE, index=False)

@mcq_blueprint.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        reg_no = request.form.get("reg_no", "").strip()
        return redirect(url_for("mcq.quiz", reg_no=reg_no))
    return render_template("mcq/home.html")

@mcq_blueprint.route("/quiz/<reg_no>", methods=["GET", "POST"])
def quiz(reg_no):
    student = next((s for s in students_dict if str(s["Reg No."]) == reg_no), None)
    
    if not student:
        return render_template("mcq/result.html", error="Student not found.")  # ✅ FIX: Removed extra return
    
    selected_answers = {}
    
    if request.method == "POST":
        score = 0
        for i, mcq in enumerate(mcqs_dict):  # ✅ FIX: Ensure enumerate is used properly
            correct_idx = int(str(mcq["Correct Answer"]).strip()) - 1
            user_answer = request.form.get(f"q{i}")

            if user_answer and user_answer.isdigit() and int(user_answer) == correct_idx:
                score += 1

        results_df = pd.read_csv(RESULT_FILE)
        if str(reg_no) in results_df["Reg No."].astype(str).values:
            return render_template("mcq/result.html", error="⚠️ Score already recorded for this student.")

        new_result = pd.DataFrame([{"Reg No.": reg_no, "Name": student["Name"], "Score": score}])
        new_result.to_csv(RESULT_FILE, mode="a", header=False, index=False)

        return render_template("mcq/result.html", name=student["Name"], score=score, total=len(mcqs_dict))

    return render_template("mcq/quiz.html", reg_no=reg_no, mcqs=mcqs_dict, selected_answers=selected_answers, enumerate=enumerate)  # ✅ FIX: Pass enumerate explicitly

@mcq_blueprint.route("/download")
def download_results():
    if os.path.exists(RESULT_FILE):
        return send_file(RESULT_FILE, as_attachment=True)
    return "File not found!", 404
