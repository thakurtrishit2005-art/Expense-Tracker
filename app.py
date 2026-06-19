from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import calendar

# -----------------------------#
# FLASK APP SETUP
# -----------------------------#

app = Flask(__name__)
app.secret_key = "pocketrunway_v2_secure_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pocketrunway.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------#
# LOGIN MANAGER
# -----------------------------#

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------#
# DATABASE MODELS (V2 SCHEMA)
# -----------------------------#

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    monthly_allowance = db.Column(db.Integer, default=2000) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    amount = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(10), default="expense") # 'expense' or 'income'
    category = db.Column(db.String(50), nullable=False) 
    payment_method = db.Column(db.String(10), default="UPI") 
    is_split = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(200), nullable=True) # Universal notes field
    
    date = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------#
# AUTHENTICATION ROUTES
# -----------------------------#

@app.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return redirect(url_for("register"))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials.", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("landing"))

# -----------------------------#
# CORE PRODUCT ROUTES (V2)
# -----------------------------#

@app.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_passed = today.day
    days_left = days_in_month - today.day
    
    # Fetch all records for current month
    transactions = Expense.query.filter(
        Expense.user_id == current_user.id,
        db.extract('month', Expense.date) == today.month,
        db.extract('year', Expense.date) == today.year
    ).order_by(Expense.date.desc()).all()

    # V2 Math: Separate Incomes and Expenses
    total_spent = sum(t.amount for t in transactions if t.transaction_type == 'expense')
    total_added = sum(t.amount for t in transactions if t.transaction_type == 'income')
    
    effective_allowance = current_user.monthly_allowance + total_added
    current_balance = effective_allowance - total_spent
    
    # --- FIXED "SAFE TODAY" MATH ---
    # 1. Calculate what was spent specifically today
    spent_today = sum(t.amount for t in transactions if t.date.date() == today and t.transaction_type == 'expense')
    
    # 2. What was the balance when the user woke up today?
    start_of_day_balance = current_balance + spent_today
    
    # 3. What was today's target allowance before they spent anything?
    target_daily_allowance = start_of_day_balance / max(days_left, 1)
    
    # 4. Subtract today's spending from today's target
    raw_safe_today = round(target_daily_allowance - spent_today)
    
    # 5. Floor at 0 for UI purposes (no negative safe spends)
    safe_daily_spend = max(0, raw_safe_today)

    # Storytelling Insights Engine
    insight_message = ""
    status_state = "On track" 
    
    if days_passed > 0:
        avg_daily_spend = total_spent / days_passed
        projected_balance = effective_allowance - (avg_daily_spend * days_in_month)
        
        if current_balance <= 0:
            insight_message = f"You've overspent your budget by ₹{abs(current_balance)}. Time to survive! 💀"
            status_state = "Risk"
        elif projected_balance > 0:
            insight_message = f"Nice ✨ At this pace you'll finish the month with ₹{int(projected_balance)} left."
            status_state = "On track"
        else:
            insight_message = f"Careful ⚠️ You're trending to run out before the month ends."
            status_state = "Careful"

    # 5-Day Streak Calculator
    base_daily_target = round(effective_allowance / days_in_month)
    streak_icons = []
    
    for i in range(4, -1, -1): 
        check_date = today - timedelta(days=i)
        if check_date.month != today.month:
            continue 
            
        daily_spent = sum(t.amount for t in transactions if t.date.date() == check_date and t.transaction_type == 'expense')
        if daily_spent <= base_daily_target:
            streak_icons.append("🟢")
        else:
            streak_icons.append("🔴")

    return render_template(
        "index.html", 
        balance=current_balance,
        safe_daily_spend=safe_daily_spend,
        days_left=days_left,
        total_spent=total_spent,
        expenses=transactions[:5],
        insight_message=insight_message,
        status_state=status_state,
        streak_icons=streak_icons
    )

@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    amount = request.form.get("amount", type=int)
    transaction_type = request.form.get("transaction_type", default="expense")
    category = request.form.get("category", default="Other")
    payment_method = request.form.get("payment_method", default="UPI")
    is_split = request.form.get("is_split") == 'on'
    notes = request.form.get("split_notes", default="")

    if amount and amount > 0:
        new_exp = Expense(
            user_id=current_user.id,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            payment_method=payment_method,
            is_split=is_split,
            notes=notes
        )
        db.session.add(new_exp)
        db.session.commit()
        
        if transaction_type == "income":
            flash(f"Successfully added +₹{amount} to your runway! 💸", "success")
        else:
            flash("Expense logged safely! ✨", "success")
    else:
        flash("Please enter a valid amount.", "error")

    return redirect(url_for("dashboard"))

@app.route("/history")
@login_required
def history():
    transactions = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template("history.html", expenses=transactions)

@app.route("/delete_expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    # Ensure users can only delete their own transactions
    if expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
        flash("Transaction deleted.", "success")
        
    # Redirect back to the page they were just on (Dashboard or History)
    return redirect(request.referrer or url_for('dashboard'))

# -----------------------------#
# RUN APP
# -----------------------------#
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)