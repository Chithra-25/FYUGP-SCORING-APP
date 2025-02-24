from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import os

app = Flask(__name__)

# Paths for datasets
mcq_file = r"E:\DSA july\Internship\Objective App\Python_40_MCQ_Questions.xlsx"
students_file = r"E:\DSA july\Internship\Objective App\Kerala_Student_Records_Final.xlsx"
result_file = r"E:\DSA july\Internship\Objective App\MCQ_Results.csv"

# Load MCQ and Student dataset
try:
    mcqs = pd.read_excel(mcq_file, engine="openpyxl")
    students = pd.read_excel(students_file, engine="openpyxl")
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit()

students_dict = students.to_dict(orient="records")
mcqs_dict = mcqs.to_dict(orient="records")

# Ensure results file exists
if not os.path.exists(result_file):
    pd.DataFrame(columns=["Reg No.", "Name", "Score"]).to_csv(result_file, index=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        reg_no = request.form.get("reg_no", "").strip()
        return redirect(url_for("quiz", reg_no=reg_no))
    return render_template("index.html")

@app.route("/quiz/<reg_no>", methods=["GET", "POST"])
def quiz(reg_no):
    student = next((s for s in students_dict if str(s["Reg No."]) == reg_no), None)

    if not student:
        return render_template("result.html", error="Student not found.")

    selected_answers = {}  # Dictionary to store selected answers

    if request.method == "POST":
        for i in range(len(mcqs_dict)):  
            selected_answers[f"q{i}"] = request.form.get(f"q{i}", "")

        
        # Score calculation
        score = 0
        for i, mcq in enumerate(mcqs_dict):
            correct_idx = int(str(mcq["Correct Answer"]).strip()) - 1
            user_answer = request.form.get(f"q{i}")

            if user_answer and user_answer.isdigit():
                if int(user_answer) == correct_idx:
                    score += 1

        # Save the score to CSV
        results_df = pd.read_csv(result_file)

        if str(reg_no) in results_df["Reg No."].astype(str).values:
            return render_template("result.html", error="⚠️ Score already recorded for this student.")

        new_result = pd.DataFrame([{"Reg No.": reg_no, "Name": student["Name"], "Score": score}])
        new_result.to_csv(result_file, mode="a", header=False, index=False)

        return render_template("result.html", name=student["Name"], score=score, total=len(mcqs_dict))

    return render_template("quiz.html", reg_no=reg_no, mcqs=mcqs_dict, selected_answers=selected_answers, enumerate=enumerate)


@app.route("/download")
def download_results():
    """Route to download the MCQ results file."""
    if os.path.exists(result_file):
        return send_file(result_file, as_attachment=True)
    else:
        return "File not found!", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
