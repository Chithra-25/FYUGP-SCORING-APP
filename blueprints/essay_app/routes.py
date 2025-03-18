from flask import Flask, render_template, request, send_file, Blueprint, session
import pandas as pd
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
import os

essay_blueprint = Blueprint('essay', __name__, url_prefix='/essay')

# Ensure the evaluated_responses folder exists
evaluated_folder = "essay_results"
os.makedirs(evaluated_folder, exist_ok=True)

# Load BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# Function to generate BERT embeddings
def get_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze()

# Function to evaluate response similarity
def evaluate_response(question, response):
    try:
        # Generate embeddings
        question_embedding = get_embedding(question)
        response_embedding = get_embedding(response)

        # Calculate cosine similarity
        similarity = cosine_similarity(
            response_embedding.unsqueeze(0), 
            question_embedding.unsqueeze(0)
        )[0][0]

        # Convert similarity to a 10-point score
        score = round(similarity * 10, 2)

        # Generate feedback
        if similarity > 0.8:
            feedback = "Excellent response with strong coverage of key points."
        elif similarity > 0.5:
            feedback = "Good response but can improve by adding more key details."
        else:
            feedback = "Needs Improvement."

    except Exception as e:
        score = 0
        feedback = f"Error processing response: {str(e)}"

    return score, feedback

@essay_blueprint.route('/')
def index():
    return render_template('essay/upload.html')

@essay_blueprint.route('/evaluate', methods=['POST'])
def evaluate():
    if 'response_file' not in request.files:
        return "No file uploaded", 400

    response_file = request.files['response_file']
    if response_file.filename == '':
        return "No selected file", 400

    # Read uploaded file
    students_df = pd.read_excel(response_file)

    # Identify question and response columns dynamically
    question_col = next((col for col in students_df.columns if 'question' in col.lower()), None)
    response_col = next((col for col in students_df.columns if 'response' in col.lower()), None)

    if not question_col or not response_col:
        return "Uploaded file must contain 'Question' and 'Response' columns", 400

    # Get logged-in student's registration number
    name = session.get('name', 'Unknown_Student')
    register_number = session.get('reg_no', 'Unknown_Student')

    results = []
    for _, row in students_df.iterrows():
        question = row[question_col]
        response = row[response_col]

        # Skip empty rows
        if pd.isna(question) or pd.isna(response):
            continue

        # Evaluate using BERT/NLP-based scoring
        score, feedback = evaluate_response(question, response)

        # Store results
        results.append({
            "Name": name,
            "Register Number": register_number,
            "Question": question,
            "Response": response,
            "Score": score,
            "Feedback": feedback
        })

    # Save the results into an Excel file
    file_path = os.path.join(evaluated_folder, f"{register_number}_evaluation.xlsx")
    results_df = pd.DataFrame(results)
    results_df.to_excel(file_path, index=False)

    return render_template('essay/upload.html', results=results)

@essay_blueprint.route('/download')
def download():
    name = session.get('name', 'Unknown_Student')
    reg_no = session.get('reg_no', 'Unknown_Student')
    result_file = os.path.join(evaluated_folder, f"{reg_no}_evaluation.xlsx")

    if os.path.exists(result_file):
        return send_file(result_file, as_attachment=True)
    else:
        return "No results available to download", 404
