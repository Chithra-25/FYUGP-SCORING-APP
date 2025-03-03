from flask import Flask, render_template
from blueprints.mcq_app.routes import mcq_blueprint
from blueprints.essay_app.routes import essay_blueprint

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a unique secret key

# Register Blueprints
app.register_blueprint(mcq_blueprint)
app.register_blueprint(essay_blueprint)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

