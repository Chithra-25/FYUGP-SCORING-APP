from flask import Flask, render_template, redirect, url_for, session, request, flash
from blueprints.mcq_app.routes import mcq_blueprint
from blueprints.essay_app.routes import essay_blueprint
from blueprints.code_app.routes import code_blueprint
from blueprints.teacher_app.routes import teacher_blueprint

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Register Blueprints
app.register_blueprint(mcq_blueprint, url_prefix='/mcq')
app.register_blueprint(essay_blueprint, url_prefix='/essay')
app.register_blueprint(code_blueprint, url_prefix='/code')
app.register_blueprint(teacher_blueprint, url_prefix="/teacher")


@app.route('/')
def home():
    return render_template('landing_page.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        reg_no = request.form.get("reg_no", "").strip()

        if not name or not reg_no:
            flash("Both fields are required.", "error")
            return redirect(url_for("login"))

        session["name"] = name
        session["reg_no"] = reg_no

        print("Session Data:", session)  # Debugging line

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/teacherlogin", methods=["GET", "POST"])
def teacherlogin():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        # Add logic for validating student login (ensure reg_no exists)
        session["username"] = username
        session["password"] = password
        session["completed_sessions"] = []
        return redirect(url_for("teacherdashboard"))
    return render_template("teacherlogin.html")  # Display the login page


# Dashboard route
@app.route("/dashboard")
def dashboard():
    if "reg_no" not in session or "name" not in session:
        return redirect(url_for("login"))

    name = session.get("name", "Guest")  # Use .get() to avoid errors
    return render_template("dashboard.html", name=name)

# Dashboard route
@app.route("/teacherdashboard")
def teacherdashboard():
    if "username" not in session or "password" not in session:
        return redirect(url_for("teacherlogin"))

    return render_template("teacherdashboard.html")


@app.route("/logout")
def logout():
    """Clears session and redirects to the landing page."""
    session.clear()
    return redirect(url_for("home"))  # Redirect to the landing page


if __name__ == "__main__":
    app.run(debug=True)
