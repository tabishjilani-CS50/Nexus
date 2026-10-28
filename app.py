from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)

TRANSACTION_FILE = "nexus_transactions.csv"
BUDGET_FILE = "nexus_budgets.csv"


# --------------------------------------------------
# FILE SETUP
# --------------------------------------------------

def ensure_files():
    if not os.path.exists(TRANSACTION_FILE):
        with open(TRANSACTION_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "id", "date", "type", "category",
                "amount", "description"
            ])

    if not os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "category", "amount"
            ])


ensure_files()


# --------------------------------------------------
# TRANSACTIONS
# --------------------------------------------------

def load_transactions():
    transactions = []

    with open(TRANSACTION_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                row["amount"] = float(row["amount"])
            except:
                row["amount"] = 0

            transactions.append(row)

    return transactions


def save_transaction(transaction):
    with open(TRANSACTION_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            transaction["id"],
            transaction["date"],
            transaction["type"],
            transaction["category"],
            transaction["amount"],
            transaction["description"]
        ])


def delete_transaction(transaction_id):
    transactions = load_transactions()

    transactions = [
        t for t in transactions
        if str(t["id"]) != str(transaction_id)
    ]

    with open(TRANSACTION_FILE, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "id", "date", "type",
            "category", "amount", "description"
        ])

        for t in transactions:
            writer.writerow([
                t["id"],
                t["date"],
                t["type"],
                t["category"],
                t["amount"],
                t["description"]
            ])


# --------------------------------------------------
# BUDGETS
# --------------------------------------------------

def load_budgets():
    budgets = {}

    with open(BUDGET_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                budgets[row["category"]] = float(row["amount"])
            except:
                budgets[row["category"]] = 0

    return budgets


def save_budgets(budgets):
    with open(BUDGET_FILE, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(["category", "amount"])

        for category, amount in budgets.items():
            writer.writerow([category, amount])


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def calculate_finances():
    transactions = load_transactions()

    income = sum(
        t["amount"]
        for t in transactions
        if t["type"].lower() == "income"
    )

    expenses = sum(
        t["amount"]
        for t in transactions
        if t["type"].lower() == "expense"
    )

    balance = income - expenses

    return income, expenses, balance


def category_expenses():
    transactions = load_transactions()

    categories = {}

    for t in transactions:
        if t["type"] == "expense":
            category = t["category"]

            categories[category] = (
                categories.get(category, 0)
                + t["amount"]
            )

    return categories


def calculate_health():
    income, expenses, balance = calculate_finances()

    if income <= 0:
        return 0, "Add some income to start your financial analysis."

    score = 50

    if balance > 0:
        score += 15

    if expenses < income * 0.8:
        score += 15

    if balance > income * 0.2:
        score += 10

    if balance > income * 0.4:
        score += 10

    score = min(score, 100)

    if score >= 80:
        message = "Great! You have a healthy financial position."

    elif score >= 60:
        message = "Good start. There is room to improve your savings."

    else:
        message = "Try reviewing your expenses and building a small buffer."

    return score, message


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def dashboard():

    income, expenses, balance = calculate_finances()

    transactions = load_transactions()

    budgets = load_budgets()

    categories = category_expenses()

    alerts = []

    for category, budget in budgets.items():

        spent = categories.get(category, 0)

        if budget > 0:

            percentage = (spent / budget) * 100

            if percentage >= 100:
                alerts.append(
                    f"You have exceeded your {category} budget."
                )

            elif percentage >= 80:
                alerts.append(
                    f"You are close to your {category} budget."
                )

    health_score, health_message = calculate_health()

    return render_template(
        "dashboard.html",
        income=income,
        expenses=expenses,
        balance=balance,
        transactions=transactions,
        budgets=budgets,
        categories=categories,
        alerts=alerts,
        health_score=health_score,
        health_message=health_message
    )


# --------------------------------------------------
# ADD TRANSACTION
# --------------------------------------------------

@app.route("/add", methods=["GET", "POST"])
def add_transaction():

    if request.method == "POST":

        transaction = {
            "id": int(datetime.now().timestamp() * 1000),
            "date": request.form.get(
                "date"
            ) or datetime.now().strftime("%Y-%m-%d"),

            "type": request.form.get("type"),

            "category": request.form.get(
                "category"
            ) or "Other",

            "amount": float(
                request.form.get("amount", 0)
            ),

            "description": request.form.get(
                "description"
            ) or ""
        }

        save_transaction(transaction)

        return redirect(url_for("dashboard"))

    return render_template("add.html")


# --------------------------------------------------
# TRANSACTIONS
# --------------------------------------------------

@app.route("/transactions")
def transactions():

    all_transactions = load_transactions()

    search = request.args.get("search", "").lower()

    if search:

        all_transactions = [
            t for t in all_transactions
            if search in t["category"].lower()
            or search in t["description"].lower()
            or search in t["type"].lower()
        ]

    return render_template(
        "transactions.html",
        transactions=all_transactions
    )


@app.route("/delete/<transaction_id>")
def delete(transaction_id):

    delete_transaction(transaction_id)

    return redirect(url_for("transactions"))


# --------------------------------------------------
# BUDGET
# --------------------------------------------------

@app.route("/budget", methods=["GET", "POST"])
def budget():

    budgets = load_budgets()

    if request.method == "POST":

        category = request.form.get("category")

        amount = float(
            request.form.get("amount", 0)
        )

        if category and amount > 0:
            budgets[category] = amount

            save_budgets(budgets)

        return redirect(url_for("budget"))

    categories = category_expenses()

    budget_data = []

    for category, limit in budgets.items():

        spent = categories.get(category, 0)

        percentage = 0

        if limit > 0:
            percentage = (spent / limit) * 100

        budget_data.append({
            "category": category,
            "limit": limit,
            "spent": spent,
            "percentage": round(percentage, 1)
        })

    return render_template(
        "budget.html",
        budgets=budget_data
    )


# --------------------------------------------------
# WHAT-IF SIMULATOR
# --------------------------------------------------

@app.route("/what-if", methods=["GET", "POST"])
def what_if():

    income, expenses, balance = calculate_finances()

    result = None

    if request.method == "POST":

        income_change = float(
            request.form.get("income_change", 0)
        )

        expense_change = float(
            request.form.get("expense_change", 0)
        )

        emergency = float(
            request.form.get("emergency", 0)
        )

        new_income = income + income_change

        new_expenses = (
            expenses
            + expense_change
            + emergency
        )

        new_balance = new_income - new_expenses

        if new_balance < 0:

            advice = (
                "This situation could create a deficit. "
                "Try reducing non-essential expenses "
                "or increasing available income."
            )

        elif new_balance < income * 0.1:

            advice = (
                "Your balance is still positive, "
                "but your safety margin is quite small."
            )

        else:

            advice = (
                "Your finances remain positive "
                "under this scenario."
            )

        result = {
            "new_income": new_income,
            "new_expenses": new_expenses,
            "new_balance": new_balance,
            "advice": advice
        }

    return render_template(
        "what_if.html",
        income=income,
        expenses=expenses,
        balance=balance,
        result=result
    )


# --------------------------------------------------
# STUDENT MODE
# --------------------------------------------------

@app.route("/student-mode", methods=["GET", "POST"])
def student_mode():

    result = None

    if request.method == "POST":

        allowance = float(
            request.form.get("allowance", 0)
        )

        food = float(
            request.form.get("food", 0)
        )

        transport = float(
            request.form.get("transport", 0)
        )

        education = float(
            request.form.get("education", 0)
        )

        phone = float(
            request.form.get("phone", 0)
        )

        other = float(
            request.form.get("other", 0)
        )

        savings_goal = float(
            request.form.get("savings_goal", 0)
        )

        total_expenses = (
            food
            + transport
            + education
            + phone
            + other
        )

        remaining = allowance - total_expenses

        if allowance > 0:
            savings_percentage = (
                remaining / allowance
            ) * 100
        else:
            savings_percentage = 0

        if remaining < 0:

            message = (
                "Your planned spending is higher than "
                "your available allowance. Try reviewing "
                "non-essential spending."
            )

        elif savings_goal > 0 and remaining >= savings_goal:

            message = (
                "Nice! Your current plan can cover "
                "your savings goal."
            )

        elif remaining > 0:

            message = (
                "You have money left after your planned "
                "expenses. Consider keeping some as an "
                "emergency buffer."
            )

        else:

            message = (
                "Your planned spending uses all of "
                "your available money."
            )

        result = {
            "allowance": allowance,
            "food": food,
            "transport": transport,
            "education": education,
            "phone": phone,
            "other": other,
            "total_expenses": total_expenses,
            "remaining": remaining,
            "savings_percentage": round(
                savings_percentage, 1
            ),
            "savings_goal": savings_goal,
            "message": message
        }

    return render_template(
        "student_mode.html",
        result=result
    )


# --------------------------------------------------
# CAN I AFFORD THIS?
# --------------------------------------------------

@app.route("/afford", methods=["GET", "POST"])
def afford():

    income, expenses, balance = calculate_finances()

    result = None

    if request.method == "POST":

        price = float(
            request.form.get("price", 0)
        )

        savings_goal = float(
            request.form.get("savings_goal", 0)
        )

        remaining = balance - price

        if remaining < 0:

            message = (
                "This purchase would put your balance "
                "below zero."
            )

            status = "Not recommended"

        elif savings_goal > 0 and remaining < savings_goal:

            message = (
                "You can technically afford it, but "
                "it would reduce the amount available "
                "for your savings goal."
            )

            status = "Think about it"

        else:

            message = (
                "This purchase fits within your current "
                "available balance."
            )

            status = "Looks manageable"

        result = {
            "price": price,
            "remaining": remaining,
            "message": message,
            "status": status
        }

    return render_template(
        "afford.html",
        balance=balance,
        result=result
    )


# --------------------------------------------------
# SAVINGS GOAL
# --------------------------------------------------

@app.route("/savings-goal", methods=["GET", "POST"])
def savings_goal():

    result = None

    if request.method == "POST":

        target = float(
            request.form.get("target", 0)
        )

        current = float(
            request.form.get("current", 0)
        )

        months = int(
            request.form.get("months", 1)
        )

        remaining = max(target - current, 0)

        if months > 0:
            monthly = remaining / months
        else:
            monthly = remaining

        result = {
            "target": target,
            "current": current,
            "remaining": remaining,
            "months": months,
            "monthly": monthly
        }

    return render_template(
        "savings_goal.html",
        result=result
    )


# --------------------------------------------------
# EMERGENCY BUFFER
# --------------------------------------------------

@app.route("/emergency-buffer", methods=["GET", "POST"])
def emergency_buffer():

    result = None

    if request.method == "POST":

        available = float(
            request.form.get("available", 0)
        )

        essential = float(
            request.form.get("essential", 0)
        )

        if essential > 0:

            months = available / essential

        else:

            months = 0

        if months >= 3:

            message = (
                "You have a relatively strong emergency buffer."
            )

        elif months >= 1:

            message = (
                "You have some emergency coverage, "
                "but building a larger buffer could help."
            )

        else:

            message = (
                "Your current emergency buffer is small."
            )

        result = {
            "available": available,
            "essential": essential,
            "months": round(months, 2),
            "message": message
        }

    return render_template(
        "emergency_buffer.html",
        result=result
    )


# --------------------------------------------------
# FINANCIAL HEALTH
# --------------------------------------------------

@app.route("/health")
def health():

    score, message = calculate_health()

    income, expenses, balance = calculate_finances()

    return render_template(
        "health.html",
        score=score,
        message=message,
        income=income,
        expenses=expenses,
        balance=balance
    )


# --------------------------------------------------
# EDUCATION
# --------------------------------------------------

@app.route("/education")
def education():

    lessons = [

        {
            "title": "Needs vs Wants",
            "text": (
                "Needs are things you generally need for "
                "daily life. Wants are things you may enjoy "
                "but can usually delay."
            )
        },

        {
            "title": "Emergency Buffer",
            "text": (
                "An emergency buffer is money kept aside "
                "for unexpected expenses."
            )
        },

        {
            "title": "Budgeting",
            "text": (
                "A budget gives every part of your available "
                "money a purpose."
            )
        },

        {
            "title": "Saving",
            "text": (
                "Saving a small amount consistently can help "
                "you work toward future goals."
            )
        },

        {
            "title": "Compound Interest",
            "text": (
                "Compound interest means returns can themselves "
                "generate additional returns over time."
            )
        }
    ]

    return render_template(
        "education.html",
        lessons=lessons
    )


# --------------------------------------------------
# COMMUNITY / ACCESS
# --------------------------------------------------

@app.route("/community")
def community():

    return render_template(
        "community.html"
    )


# --------------------------------------------------
# DEMO DATA
# --------------------------------------------------

@app.route("/demo")
def demo():

    demo_transactions = [

        [
            int(datetime.now().timestamp() * 1000),
            datetime.now().strftime("%Y-%m-%d"),
            "income",
            "Allowance",
            5000,
            "Monthly student allowance"
        ],

        [
            int(datetime.now().timestamp() * 1000) + 1,
            datetime.now().strftime("%Y-%m-%d"),
            "expense",
            "Food",
            900,
            "Food and snacks"
        ],

        [
            int(datetime.now().timestamp() * 1000) + 2,
            datetime.now().strftime("%Y-%m-%d"),
            "expense",
            "Transport",
            600,
            "Bus and travel"
        ],

        [
            int(datetime.now().timestamp() * 1000) + 3,
            datetime.now().strftime("%Y-%m-%d"),
            "expense",
            "Education",
            500,
            "Books and study material"
        ],

        [
            int(datetime.now().timestamp() * 1000) + 4,
            datetime.now().strftime("%Y-%m-%d"),
            "expense",
            "Phone",
            300,
            "Mobile recharge"
        ]
    ]

    with open(
        TRANSACTION_FILE,
        "a",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerows(demo_transactions)

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# RESET
# --------------------------------------------------

@app.route("/reset")
def reset():

    with open(
        TRANSACTION_FILE,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "id",
            "date",
            "type",
            "category",
            "amount",
            "description"
        ])

    with open(
        BUDGET_FILE,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "category",
            "amount"
        ])

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# REPORT
# --------------------------------------------------

@app.route("/report")
def report():

    income, expenses, balance = calculate_finances()

    score, message = calculate_health()

    transactions = load_transactions()

    report_text = f"""
NEXUS FINANCIAL REPORT
======================

Generated:
{datetime.now().strftime("%Y-%m-%d %H:%M")}

Income: ₹{income:.2f}
Expenses: ₹{expenses:.2f}
Balance: ₹{balance:.2f}

Financial Health Score:
{score}/100

Assessment:
{message}

Transactions:
"""

    for t in transactions:

        report_text += (
            f"\n{t['date']} | "
            f"{t['type']} | "
            f"{t['category']} | "
            f"₹{float(t['amount']):.2f} | "
            f"{t['description']}"
        )

    file = BytesIO(
        report_text.encode("utf-8")
    )

    file.seek(0)

    return send_file(
        file,
        as_attachment=True,
        download_name="nexus_financial_report.txt",
        mimetype="text/plain"
    )


# --------------------------------------------------
# MONEY FILTER
# --------------------------------------------------

@app.template_filter("money")
def money(value):

    try:
        return f"₹{float(value):,.2f}"
    except:
        return "₹0.00"


# --------------------------------------------------
# START APP
# --------------------------------------------------

if __name__ == "__main__":

    print()
    print("=" * 45)
    print("        NEXUS PERSONAL FINANCE")
    print("=" * 45)
    print()
    print("Running at: http://127.0.0.1:5000")
    print()
    print("Student Mode: /student-mode")
    print("Can I Afford It?: /afford")
    print("Savings Goal: /savings-goal")
    print("Emergency Buffer: /emergency-buffer")
    print()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )