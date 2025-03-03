import os
import pandas as pd
import nltk
from flask import Blueprint, request, render_template, send_file, redirect, url_for, session
from nltk.stem import WordNetLemmatizer

essay_blueprint = Blueprint('essay', __name__, url_prefix='/essay')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

nltk.download("wordnet")
lemmatizer = WordNetLemmatizer()

# Teacher Login Route
@essay_blueprint.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Store credentials in session (no validation)
        session['teacher_username'] = username
        session['teacher_password'] = password

        # Redirect to upload form
        return redirect(url_for('essay.upload_form'))

    return render_template('essay/login.html')

# Display Upload Form After Login
@essay_blueprint.route('/upload-form')
def upload_form():
    if 'teacher_username' not in session:
        return redirect(url_for('essay.login_page'))  # Ensure login first

    return render_template('essay/upload.html')

# **Function to Evaluate Responses Based on Keywords**
def evaluate_response(response, keywords):
    if pd.isna(response) or not isinstance(response, str) or response.strip() == "":
        return 0, "No response provided."

    if pd.isna(keywords) or not isinstance(keywords, str) or keywords.strip() == "":
        return 0, "No keywords provided for evaluation."

    # Process keywords and response words with lemmatization
    keyword_list = {lemmatizer.lemmatize(kw.strip().lower()) for kw in keywords.split(",")}
    response_words = {lemmatizer.lemmatize(word) for word in response.lower().split()}

    # Find matched and missing keywords
    matched_keywords = keyword_list & response_words
    missing_keywords = keyword_list - response_words

    # Calculate score (out of 10)
    score = round((len(matched_keywords) / len(keyword_list)) * 10, 2) if keyword_list else 0

    # Generate feedback
    feedback = f"Strengths: Used keywords - {', '.join(matched_keywords)}. " if matched_keywords else "No relevant keywords found. "
    if missing_keywords:
        feedback += f"Areas for improvement: Include - {', '.join(missing_keywords)}."

    return score, feedback

# File Upload Route (Processes Uploaded Files)
@essay_blueprint.route('/upload', methods=['POST'])
def upload_file():
    if 'teacher_username' not in session:
        return redirect(url_for('essay.login_page'))  # Ensure login first

    if 'questions' not in request.files or 'responses' not in request.files:
        return "Please upload both files"

    questions_file = request.files['questions']
    responses_file = request.files['responses']
    
    questions_path = os.path.join(UPLOAD_FOLDER, questions_file.filename)
    responses_path = os.path.join(UPLOAD_FOLDER, responses_file.filename)

    questions_file.save(questions_path)
    responses_file.save(responses_path)

    questions_df = pd.read_excel(questions_path, engine='openpyxl')
    responses_df = pd.read_excel(responses_path, engine='openpyxl')

    questions_df.columns = questions_df.columns.str.strip()
    responses_df.columns = responses_df.columns.str.strip()

    merged_df = responses_df.merge(questions_df[['Question', 'Keywords']], on="Question", how="left")

    # Identify student response columns (columns containing "Response")
    student_columns = [col for col in merged_df.columns if "Response" in col]

    # Evaluate responses for each student
    for student_col in student_columns:
        score_col = student_col.replace("Response", "Score")
        feedback_col = student_col.replace("Response", "Feedback")

        merged_df[score_col], merged_df[feedback_col] = zip(*merged_df.apply(
            lambda row: evaluate_response(row[student_col], row["Keywords"]), axis=1))

    # Save evaluated responses
    evaluated_file_path = os.path.join(UPLOAD_FOLDER, "Evaluated_Student_Responses.xlsx")
    merged_df.to_excel(evaluated_file_path, index=False, engine='openpyxl')

    return render_template('essay/download.html', file_path="Evaluated_Student_Responses.xlsx")

# Download Evaluated File
@essay_blueprint.route('/download/<filename>')
def download_file(filename):
    if 'teacher_username' not in session:
        return redirect(url_for('essay.login_page'))  # Ensure login first

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True)
