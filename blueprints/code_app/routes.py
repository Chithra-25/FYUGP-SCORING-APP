from flask import Flask, request, render_template, send_file, Blueprint, session
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import os

code_blueprint = Blueprint('code', __name__, url_prefix='/code')

# Ensure the evaluated_responses folder exists
evaluated_folder = "coding_results"
os.makedirs(evaluated_folder, exist_ok=True)

def evaluate_response(Instruction, student_code):
    try:
        # Create a safe execution environment
        local_env = {}
        exec(student_code, {}, local_env)

        # Extract the result if defined
        result = local_env.get('result', None)

        # Define expected output dynamically based on instruction (adjust as needed)
        expected_output = Instruction.strip().lower()  # Assuming instruction holds expected output

        if result is not None and str(result).strip().lower() == expected_output:
            score = 10
            feedback = "Excellent! The code is correct."
        elif result is not None:
            score = 6
            feedback = "The code runs but the output is incorrect."
        else:
            score = 3
            feedback = "The code has an error or no output."
    except Exception as e:
        score = 0
        feedback = f"The code has an error: {str(e)}"

    return score, feedback

@code_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Read the uploaded file
        file = request.files['response_file']
        responses_df = pd.read_excel(file)

        # Ensure required columns exist
        if 'Instruction' not in responses_df.columns or 'Response' not in responses_df.columns:
            return "Uploaded file must contain 'Instruction' and 'Response' columns", 400

        # Retrieve the student's registration number from session
        name = session.get('name', 'Unknown_Student')
        register_number = session.get('reg_no', 'Unknown_Student')

        # Process responses
        results = []
        for i, row in responses_df.iterrows():
            instruction = row['Instruction']
            student_response = row['Response']
            score, feedback = evaluate_response(instruction, student_response)

            results.append({
                "Name": name,
                "Register Number": register_number,
                "Instruction": instruction,
                "Response": student_response,
                "Score": score,
                "Feedback": feedback
            })

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)

        # Save evaluated responses per student
        student_file_path = os.path.join(evaluated_folder, f"{register_number}_evaluated.xlsx")
        results_df.to_excel(student_file_path, index=False)

        # Generate a bar chart for summary
        correct = results_df['Score'].tolist().count(10)
        incorrect = results_df['Score'].tolist().count(0)
        partial = len(results_df) - correct - incorrect

        plt.figure(figsize=(5, 3))
        plt.bar(['Correct', 'Partial', 'Incorrect'], [correct, partial, incorrect], color=['green', 'orange', 'red'])
        plt.xlabel('Response Type')
        plt.ylabel('Count')
        plt.title('Evaluation Summary')

        # Convert chart to Base64
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        chart_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        # Pass results to the template
        return render_template('code/index.html',
                               chart=chart_url,
                               results=results_df.to_dict(orient='records'))

    return render_template('code/index.html')

@code_blueprint.route('/download')
def download():
    # Retrieve student's registration number from session
    name = session.get('name', 'Unknown_Student')
    register_number = session.get('reg_no', 'Unknown_Student')
    student_file_path = os.path.join(evaluated_folder, f"{register_number}_evaluated.xlsx")

    if os.path.exists(student_file_path):
        return send_file(student_file_path, as_attachment=True)
    else:
        return "File not found", 404
