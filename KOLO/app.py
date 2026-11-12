from flask import Flask, render_template, request, redirect, session
from cs50 import SQL
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
import math

app = Flask(__name__)
app.config["SECRET_KEY"] = "ilovebutterfly" 


category_weights = {
    "food and groceries": 33,
    "transport": 15,
    "education": 8,
    "utilities": 6,
    "internet and data": 6,
    "healthcare": 4,
    "personal_care": 3,
    "entertainment": 4,
    "other": 1
}


db = SQL("sqlite:///kolo.db")
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:

        full_name = request.form.get("full_name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")

        #check if all fields are filled
        if not full_name or not email or not password or not confirm_password:
            return("All fields are required")
        #check if password and confirm password match
        if password != confirm_password:
            return("password and confirmation must match")
        #check if email already exists
        user = db.execute("SELECT id FROM users WHERE email = ?", email)
        if user:
            return("Email already exists")
        hash_password = generate_password_hash(password)
        #register user in the database
        result = db.execute("INSERT INTO users(full_name, email, password_hash) VALUES (?, ?, ?)", full_name, email, hash_password)
        session["user_id"] = result
        return redirect("/setup")

@app.route("/login", methods=["GET", "POST"]) 
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        #check if all fields are filled
        if not email or not password:
            return ("All fields must be filled")

        #check if user exists in the database
        user = db.execute("SELECT * FROM users WHERE email = ?", email)
        
        if not user:
            return ("Email or password is not correct")
        #check if password is correct
        if not check_password_hash(user[0]["password_hash"], password):
            return("Password is not correct")
        session.clear()
        session["user_id"] = user[0]["id"]
       
        #check if user has completed onboarding
        if user[0]["onboarding_complete"] == 0:
            return redirect("/setup")
        
        return redirect("/dashboard")
    
@app.route("/setup", methods=["GET", "POST"])
def setup():
    #check if user is logged in
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")
    
    #check if user has completed onboarding
    user = db.execute(
        "SELECT onboarding_complete FROM users WHERE id = ?",
        user_id
    )

    if not user:
        session.clear()
        return redirect("/login")

    if user[0]["onboarding_complete"] == 1:
        return redirect("/dashboard")

    if request.method == "GET":
        return render_template("setup.html")

    # Get form data
    monthly_income = request.form.get("monthly_income")
    categories = request.form.getlist("categories")
    savings_choice = request.form.get("savings_choice")
    budget_month = date.today().strftime("%Y-%m")

    
    # Validate form data
    if not monthly_income or not categories or savings_choice not in ["yes", "no"]:
        return "Please complete all required fields"

    try:
        monthly_income = int(monthly_income)
    except ValueError:
        return "Enter a valid monthly income"

    if monthly_income <= 0:
        return "Monthly income must be greater than zero"

    if savings_choice == "yes":
        savings_amount = request.form.get("savings_amount")

        if not savings_amount:
            return "Savings amount is required"

        try:
            savings_amount = int(savings_amount)
        except ValueError:
            return "Enter a valid savings amount"
    else:
        savings_amount = 0

    if savings_amount < 0 or savings_amount > monthly_income:
        return "Invalid savings amount"

    # Validate selected categories
    if not all(category in category_weights for category in categories):
        return "Invalid category selected"

    # Calculate allocations
    #chatgpt was used to assist in generating the allocation logic based on category weights and user input
    total_weight = sum(category_weights[category] for category in categories)

    available_budget = monthly_income - savings_amount

    percentages = {}

    for category in categories:
        percentage = (category_weights[category] / total_weight) * 100
        percentages[category] = round(percentage)

    # Make sure percentages add up to 100
    difference = 100 - sum(percentages.values())

    last_category = categories[-1]
    percentages[last_category] += difference

    allocations = {}
    remaining_budget = available_budget

    for i, category in enumerate(categories):
        category_percentage = percentages[category]
        if i == len(categories) - 1:
            allocated_amount = remaining_budget
        else:
            allocated_amount = round(
                available_budget * category_percentage / 100
            )

        remaining_budget -= allocated_amount

        allocations[category] = {
            "percentage": category_percentage,
            "amount": allocated_amount
        }

    # Save budget
    budget_id = db.execute("""INSERT INTO budgets (user_id, monthly_income, savings_amount, budget_month) VALUES (?, ?, ?, ?)""", user_id, monthly_income, savings_amount, budget_month)

    # Save category allocations
    for category, details in allocations.items():
        db.execute("""INSERT INTO budget_categories (budget_id, category, percentage, allocated_amount) VALUES (?, ?, ?, ?)""", budget_id, category, details["percentage"], details["amount"])

    # Mark onboarding as complete
    db.execute("UPDATE users SET onboarding_complete = 1 WHERE id = ?", user_id)

    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    #check if user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    user = db.execute("SELECT full_name FROM users WHERE id = ?", user_id)
    if not user:
        session.clear()
        return redirect("/login")
    #check if user has a budget
    budget = db.execute("SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", user_id)
    if not budget:
        return redirect("/setup")

    #chatpt was used to write the SQL query to calculate the total spent amount for the current budget
    budget_id = budget[0]["id"]
    total_spent = db.execute("""SELECT COALESCE(SUM(expenses.amount), 0) AS total FROM expenses JOIN budget_categories ON expenses.budget_category_id = budget_categories.id WHERE budget_categories.budget_id = ?""", budget_id)

    total_spent = total_spent[0]["total"]

    remaining_money = budget[0]["monthly_income"] - budget[0]["savings_amount"] - total_spent

    
    categories = db.execute("SELECT * FROM budget_categories WHERE budget_id = ?", budget_id)
    expenses = db.execute("SELECT expenses.* FROM expenses JOIN budget_categories ON expenses.budget_category_id = budget_categories.id WHERE budget_categories.budget_id = ?", budget_id)
    spent = db.execute("SELECT budget_categories.id, SUM(expenses.amount) AS total_spent FROM budget_categories LEFT JOIN expenses ON budget_categories.id = expenses.budget_category_id WHERE budget_categories.budget_id = ? GROUP BY budget_categories.id ", budget_id)
    spent_by_category = {
        item["id"]: item["total_spent"] or 0
        for item in spent
    }
    for category in categories:
        category["spent"] = spent_by_category.get(category["id"], 0)
        category["remaining"] = category["allocated_amount"] - category["spent"]

    return render_template("dashboard.html", categories=categories, expenses=expenses, budget=budget[0], user=user[0], remaining_money=remaining_money)

@app.route("/expenses")
def expenses():
    #check if user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    #check if user has a budget
    budget = db.execute("SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", user_id)
    if not budget:
       return redirect("/setup")

    budget_id = budget[0]["id"]
    categories = db.execute("SELECT * FROM budget_categories WHERE budget_id = ?", budget_id)
    expenses = db.execute("""SELECT expenses.*, budget_categories.category FROM expenses JOIN budget_categories ON expenses.budget_category_id = budget_categories.id WHERE budget_categories.budget_id = ?""", budget_id)

    return render_template("expenses.html", categories=categories, expenses=expenses)
    
@app.route("/budget")
def budget():
    #check if user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    #check if user has a budget
    budget = db.execute("SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", user_id)
    if not budget:
        return redirect("/setup")

    budget_id = budget[0]["id"]
    categories = db.execute("SELECT * FROM budget_categories WHERE budget_id = ?", budget_id)

    return render_template("budget.html", categories=categories, budget=budget[0])      

@app.route("/update_budget", methods=["POST"])
def update_budget():
    #check if user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    #check if user has a budget
    budget = db.execute("SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", user_id)
    if not budget:
        return redirect("/setup")
    #get the budget id
    budget_id = budget[0]["id"]
    #get the new monthly income and savings amount from the form
    monthly_income = request.form.get("monthly_income")
    savings_amount = request.form.get("savings_amount")

    #validate the inputs
    if not monthly_income or not savings_amount:
        return "Monthly income and savings amount are required"

    try:
        monthly_income = int(monthly_income)
        savings_amount = int(savings_amount)
    except ValueError:
        return "Enter valid numbers for monthly income and savings amount"

    if monthly_income <= 0 or savings_amount < 0 or savings_amount > monthly_income:
        return "Invalid values for monthly income or savings amount"
    available_budget = monthly_income - savings_amount

    # Get existing categories
    categories = db.execute("""SELECT * FROM budget_categories WHERE budget_id = ?""", budget_id)

    if not categories:
        return "No budget categories found", 400

    # Recalculate category allocations
    #chatgpt was used to assist in generating the allocation logic based on category weights and user input
    remaining_budget = available_budget

    for i, category in enumerate(categories):
        percentage = category["percentage"]

        if i == len(categories) - 1:
            allocated_amount = remaining_budget
        else:
            allocated_amount = round(
                available_budget * percentage / 100
            )

        remaining_budget -= allocated_amount
        #update the allocated amount for each category in the database
        db.execute("""UPDATE budget_categories SET allocated_amount = ? WHERE id = ? AND budget_id = ?""", allocated_amount, category["id"], budget_id)
    #update the budget with the new monthly income and savings amount
    db.execute("UPDATE budgets SET monthly_income = ?, savings_amount = ? WHERE id = ? AND user_id = ?", monthly_income, savings_amount, budget_id, user_id)

    return redirect("/budget")

@app.route("/add_expense", methods=["GET","POST"])
def add_expense():
    #check if user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    if request.method == "GET":
        #check if user has a budget
        budget = db.execute("SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", user_id)
        if not budget:
            return redirect("/setup")
        #get the budget id
        budget_id = budget[0]["id"]
        #get the categories for the budget
        categories = db.execute("SELECT * FROM budget_categories WHERE budget_id = ?", budget_id)
        return render_template("add-expense.html", categories=categories)
    else:
        #check if user has a budget
        budget = db.execute("SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", user_id)

        if not budget:
            return redirect("/setup")

        #get the budget id
        budget_id = budget[0]["id"]

        #get the form data
        category_id = request.form.get("category")
        amount = request.form.get("amount")
        description = request.form.get("description", "")

        #validate the inputs
        if not category_id or not amount:
            return "Category and amount are required"

        category = db.execute("SELECT id FROM budget_categories WHERE id = ? AND budget_id = ?", category_id, budget_id)

        if not category:
            return "Invalid category"

        try:
            amount = int(amount)
        except ValueError:
            return "Enter a valid amount"

        if amount <= 0:
            return "Amount must be greater than zero"

        #insert the expense into the database
        db.execute("""INSERT INTO expenses (budget_category_id, amount, description) VALUES (?, ?, ?)""", category_id, amount, description)
        return redirect("/expenses")

@app.route("/edit_expense/<int:id>", methods=["GET", "POST"])
def edit_expense(id):
    #check if user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    
    #check if user has a budget
    budget = db.execute("SELECT id FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1",user_id)

    if not budget:
        return redirect("/setup")

    budget_id = budget[0]["id"]

    if request.method == "GET":
        expense = db.execute("""SELECT expenses.* FROM expenses JOIN budget_categories ON expenses.budget_category_id = budget_categories.id WHERE expenses.id = ? AND budget_categories.budget_id = ?""", id, budget_id)

        if not expense:
            return "Expense not found", 404

        categories = db.execute("SELECT * FROM budget_categories WHERE budget_id =?", budget_id)
        return render_template("edit-expense.html", expense=expense[0], categories=categories)

    else:
        #get the form data
        category_id = request.form.get("category")
        amount = request.form.get("amount")
        description = request.form.get("description", "")

        #validate the inputs
        if not category_id or not amount:
            return "Category and amount are required"

        try:
            amount = int(amount)
        except ValueError:
            return "Enter a valid amount"

        if amount <= 0:
            return "Amount must be greater than zero"

        expense = db.execute("""SELECT expenses.id FROM expenses JOIN budget_categories ON expenses.budget_category_id = budget_categories.id WHERE expenses.id = ? AND budget_categories.budget_id = ?""", id, budget_id)
        if not expense:
            return "Expense not found", 404

        category = db.execute("SELECT id FROM budget_categories WHERE id = ? AND budget_id = ?", category_id, budget_id)
        if not category:
            return "Invalid category"
        
        #update the expense in the database
        db.execute("""UPDATE expenses SET budget_category_id = ?, amount = ?, description = ? WHERE id = ?""", category_id, amount, description, id)
        return redirect("/expenses")

@app.route("/delete_expense/<int:id>", methods=["POST"])
def delete_expense(id):
    #check if user is logged in
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    #check if user has a budget
    budget = db.execute("SELECT id FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1", user_id)

    if not budget:
        return redirect("/setup")
    #get the budget id
    budget_id = budget[0]["id"]

    #check if the expense exists and belongs to the user's budget
    #chatgpt was used to write the SQL query to check if the expense exists and belongs to the user's budget
    expense = db.execute("SELECT * FROM expenses JOIN budget_categories ON expenses.budget_category_id = budget_categories.id JOIN budgets ON budget_categories.budget_id = budgets.id WHERE expenses.id = ? AND budgets.user_id = ?", id, user_id)
    if not expense:
        return "Expense not found", 404

    db.execute("DELETE FROM expenses WHERE id = ?", id)
    return redirect("/expenses")

@app.route("/update-allocations", methods=["POST"])
def update_allocations():
    #check if user is logged in
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/login")

    #check if user has a budget
    budget = db.execute("""SELECT * FROM budgets WHERE user_id = ? ORDER BY id DESC LIMIT 1""", user_id)

    if not budget:
        return redirect("/setup")

    budget = budget[0]

    # Get the categories belonging to the budget
    categories = db.execute("""SELECT * FROM budget_categories WHERE budget_id = ?""", budget["id"])

    if not categories:
        return redirect("/budget")

    # Retrieve and validate the submitted percentages
    #chatgpt was used to assist in generating the allocation logic based on category weights and user input
    percentages = {}

    try:
        for category in categories:
            value = float(request.form.get(
                f"percentage_{category['id']}", ""
            ))

            if not math.isfinite(value) or value < 0 or value > 100:
                return "Invalid percentage", 400

            percentages[category["id"]] = value

    except ValueError:
        return "Please enter valid percentages", 400

    # Check that all percentages add up to 100
    if not math.isclose(sum(percentages.values()), 100, abs_tol=0.01):
        return "Your allocations must add up to 100%", 400

    # Calculate the available budget
    available_budget = budget["monthly_income"] - budget["savings_amount"]

    remaining_budget = available_budget

    # Update each category
    for i, category in enumerate(categories):
        percentage = percentages[category["id"]]

        if i == len(categories) - 1:
            allocated_amount = remaining_budget
        else:
            allocated_amount = round(
                available_budget * percentage / 100
            )

        remaining_budget -= allocated_amount

        db.execute("""UPDATE budget_categories SET percentage = ?, allocated_amount = ? WHERE id = ? AND budget_id = ? """, percentage, allocated_amount, category["id"], budget["id"])

    return redirect("/budget")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
