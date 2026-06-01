from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash
)

import numpy as np
import pandas as pd
import os

from datetime import datetime

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

# -----------------------------
# FLASK APP
# -----------------------------

app = Flask(__name__)

app.secret_key = "mysecretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# LOGIN MANAGER
# -----------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -----------------------------
# USER TABLE
# -----------------------------

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True
    )

    password = db.Column(db.String(100))


# -----------------------------
# EXPENSE TABLE
# -----------------------------

class Expense(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.String(100))

    food = db.Column(db.Integer)

    travel = db.Column(db.Integer)

    shopping = db.Column(db.Integer)

    bills = db.Column(db.Integer)

    entertainment = db.Column(db.Integer)

    health = db.Column(db.Integer)

    education = db.Column(db.Integer)

    total = db.Column(db.Integer)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


# -----------------------------
# USER LOADER
# -----------------------------

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
    User,
    int(user_id)
    )


# -----------------------------
# LANDING PAGE
# -----------------------------

@app.route("/")
def landing():

    return render_template("landing.html")


# -----------------------------
# REGISTER
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("Username already exists")
            return redirect("/register")

        new_user = User(
            username=username,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful! Please Login.")

        return redirect("/login")

    return render_template("register.html")


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:

            login_user(user)

            flash("Login Successful!")

            return redirect("/dashboard")

        else:

            return "Invalid Credentials"

    return render_template("login.html")


# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    food = ""
    travel = ""
    shopping = ""
    bills = ""
    entertainment = ""
    health = ""
    education = ""

    total = 0
    average = 0

    chart_exists = False

    if request.method == "POST":

        food = int(request.form["food"])
        travel = int(request.form["travel"])
        shopping = int(request.form["shopping"])
        bills = int(request.form["bills"])
        entertainment = int(request.form["entertainment"])
        health = int(request.form["health"])
        education = int(request.form["education"])

        expenses = np.array([
            food,
            travel,
            shopping,
            bills,
            entertainment,
            health,
            education
        ])

        total = int(np.sum(expenses))

        average = round(float(np.mean(expenses)), 2)

        categories = [
            "Food",
            "Travel",
            "Shopping",
            "Bills",
            "Entertainment",
            "Health",
            "Education"
        ]

        plt.figure(figsize=(8,8))

        def make_autopct(values):

            def my_autopct(pct):
                return f"\n{pct:.1f}%"

            return my_autopct


        wedges, texts, autotexts = plt.pie(
            expenses,
            labels=categories,
            autopct=make_autopct(expenses),
            startangle=90,
            pctdistance=1.15,
            labeldistance=1.30,
            textprops={"fontsize":14}
        )

        centre_circle = plt.Circle(
            (0,0),
            0.72,
            fc="white"
        )

        fig = plt.gcf()

        fig.gca().add_artist(
            centre_circle
        )

        plt.axis("equal")

        plt.savefig(
            "static/chart.png",
            bbox_inches="tight"
        )
        plt.close()

        chart_exists = True

        current_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        data = {
            "Date": [current_date],
            "Food": [food],
            "Travel": [travel],
            "Shopping": [shopping],
            "Bills": [bills],
            "Entertainment": [entertainment],
            "Health": [health],
            "Education": [education],
            "Total": [total]
        }

        df = pd.DataFrame(data)

        file_exists = os.path.isfile(
            "expenses.csv"
        )

        df.to_csv(
            "expenses.csv",
            mode="a",
            header=not file_exists,
            index=False
        )

        new_expense = Expense(
            date=current_date,
            food=food,
            travel=travel,
            shopping=shopping,
            bills=bills,
            entertainment=entertainment,
            health=health,
            education=education,
            total=total,
            user_id=current_user.id
        )

        db.session.add(new_expense)

        db.session.commit()

        flash("Expense Saved Successfully!")

    return render_template(
        "index.html",
        food=food,
        travel=travel,
        shopping=shopping,
        bills=bills,
        entertainment=entertainment,
        health=health,
        education=education,
        total=total,
        average=average,
        chart_exists=(total > 0)
    )


# -----------------------------
# HISTORY
# -----------------------------

@app.route("/history")
@login_required
def history():

    expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "history.html",
        expenses=expenses
    )

# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/")


# -----------------------------
# RUN APP
# -----------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)