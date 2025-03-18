from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import pandas as pd
import os
import glob

teacher_blueprint = Blueprint('teacher', __name__, url_prefix='/teacher')

# Path to the teacher credentials CSV file
TEACHER_CREDENTIALS_FILE = r"E:\DSA july\Internship\Automated Grading System\data\teachers_kerala.csv"


def load_teacher_credentials():
    """Load teacher credentials from the CSV file."""
    if os.path.exists(TEACHER_CREDENTIALS_FILE):
        df = pd.read_csv(TEACHER_CREDENTIALS_FILE)
        print(df.head())  # Debugging: Print first few rows
        return dict(zip(df['username'], df['password']))
    print("Teacher credentials file not found!")  # Debugging
    return {}


@teacher_blueprint.route("/login", methods=["GET", "POST"])
def teacher_login():
    """Handles teacher login authentication."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Load credentials from CSV
        credentials = load_teacher_credentials()

        if username in credentials:
            print(f"Found username: {username}")
            if credentials[username] == password:
                print("Password matched!")
                session["teacher_logged_in"] = True
                session["teacher_username"] = username
                return redirect(url_for("teacher.teacher_dashboard"))
            else:
                print("Incorrect password!")
                flash("Invalid password. Please try again.", "error")
        else:
            print("Username not found!")
            flash("Username not found. Please try again.", "error")

    return render_template("teacher/teacherlogin.html")


@teacher_blueprint.route("/dashboard")
def teacher_dashboard():
    """Teacher dashboard after successful login."""
    if not session.get("teacher_logged_in"):
        return redirect(url_for("teacher.teacher_login"))
    return render_template("teacher/teacherdashboard.html")


# Helper function to read CSV results
def read_results(file_path):
    """Reads CSV files and returns data as a dictionary list."""
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    return []


@teacher_blueprint.route("/mcq_results")
def mcq_results():
    """Render MCQ results for the teacher."""
    if not session.get("teacher_logged_in"):
        return redirect(url_for("teacher.teacher_login"))

    # Correct path to the MCQ results CSV file inside the 'mcq' subfolder
    results = read_results(r"E:\DSA july\Internship\Automated Grading System\data\mcq\MCQ_Results_Updated_Cleaned_v3.csv")

    return render_template("teacher/mcqresults.html", data=results)



@teacher_blueprint.route("/essay_results")
def essay_results():
    """Render all student essay results for the teacher."""
    if not session.get("teacher_logged_in"):
        return redirect(url_for("teacher.teacher_login"))

    folder_path = r"E:\DSA july\Internship\Automated Grading System\essay_results"

    # Get all Excel files inside the essay_results folder
    excel_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
    
    if not excel_files:
        print("No essay result files found in:", folder_path)  # Debugging
        return "No results available to display", 404  # Inform user

    all_results = []
    for file in excel_files:
        print("Reading file:", file)  # Debugging
        df = pd.read_excel(file)  # Use `read_excel()` for `.xlsx` files
        all_results.extend(df.to_dict(orient="records"))  # Append each student's results
    
    return render_template("teacher/essayresults.html", data=all_results)

@teacher_blueprint.route("/coding_results")
def coding_results():
    """Render all student essay results for the teacher."""
    if not session.get("teacher_logged_in"):
        return redirect(url_for("teacher.teacher_login"))

    folder_path = r"E:\DSA july\Internship\Automated Grading System\coding_results"

    # Get all Excel files inside the essay_results folder
    excel_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
    
    if not excel_files:
        print("No essay result files found in:", folder_path)  # Debugging
        return "No results available to display", 404  # Inform user

    all_results = []
    for file in excel_files:
        print("Reading file:", file)  # Debugging
        df = pd.read_excel(file)  # Use `read_excel()` for `.xlsx` files
        all_results.extend(df.to_dict(orient="records"))  # Append each student's results
    
    return render_template("teacher/coderesults.html", data=all_results)

@teacher_blueprint.route("/logout")
def logout():
    """Clears session and redirects to the landing page."""
    session.clear()
    return redirect(url_for("home"))  # Redirect to the landing page
