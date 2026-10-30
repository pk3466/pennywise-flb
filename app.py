from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path
from datetime import date, datetime
from collections import defaultdict
import csv
import io

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("budget.db")

# Small, transparent training set for the classroom demonstration.
# The model learns from transaction descriptions and predicts an expense category.
TRAINING_EXAMPLES = {
    "Food": [
        "pizza burger restaurant lunch dinner cafe coffee tea snacks grocery vegetables fruits milk",
        "swiggy zomato takeaway food order meal breakfast sandwich",
        "canteen mess food dosa biryani groceries supermarket",
    ],
    "Transport": [
        "uber ola taxi cab auto rickshaw bus metro train petrol fuel diesel parking",
        "flight ticket railway ticket commute travel pass",
        "rapido bike ride toll recharge fastag",
    ],
    "Shopping": [
        "clothes shoes shirt jeans shopping mall amazon flipkart online order",
        "electronics headphones phone accessories cosmetics",
        "gift watch bag fashion purchase",
    ],
    "Bills": [
        "electricity bill water bill gas bill internet wifi broadband mobile recharge",
        "phone postpaid subscription rent maintenance",
        "insurance premium society bill utility payment",
    ],
    "Entertainment": [
        "movie cinema netflix spotify youtube premium game concert",
        "ott subscription amusement park outing bowling",
        "music show event streaming",
    ],
    "Health": [
        "doctor hospital medicine pharmacy medical test dentist clinic",
        "health checkup prescription tablets consultation",
        "gym fitness physiotherapy",
    ],
    "Education": [
        "college fees tuition books notebook stationery course exam",
        "online learning udemy coursera class workshop",
        "project printing assignment laboratory",
    ],
    "Personal Care": [
        "haircut salon skincare shampoo soap grooming",
        "beauty parlour spa personal hygiene",
        "toothpaste deodorant",
    ],
}

def train_classifier():
    texts, labels = [], []
    for category, samples in TRAINING_EXAMPLES.items():
        for sample in samples:
            # Split phrase groups into several training rows to make the tiny model useful.
            texts.append(sample)
            labels.append(category)
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
        ("classifier", MultinomialNB(alpha=0.35)),
    ])
    model.fit(texts, labels)
    return model

classifier = train_classifier()
CATEGORIES = list(TRAINING_EXAMPLES.keys())

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('income', 'expense')),
                tx_date TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL CHECK(monthly_limit >= 0)
            )
        """)
        conn.commit()

def current_month():
    return date.today().strftime("%Y-%m")

def month_transactions(month=None):
    month = month or current_month()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE substr(tx_date, 1, 7) = ? ORDER BY tx_date DESC, id DESC",
            (month,)
        ).fetchall()
    return [dict(row) for row in rows]

def month_summary(month=None):
    rows = month_transactions(month)
    income = sum(r["amount"] for r in rows if r["kind"] == "income")
    expenses = sum(r["amount"] for r in rows if r["kind"] == "expense")
    by_category = defaultdict(float)
    for r in rows:
        if r["kind"] == "expense":
            by_category[r["category"]] += r["amount"]
    with get_db() as conn:
        budgets = {r["category"]: r["monthly_limit"] for r in
                   conn.execute("SELECT * FROM budgets").fetchall()}
    return {
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "balance": round(income - expenses, 2),
        "savings_rate": round(((income - expenses) / income) * 100, 1) if income else 0,
        "by_category": dict(by_category),
        "budgets": budgets,
        "transactions": rows,
    }

def make_recommendations(summary):
    recs = []
    income, expenses = summary["income"], summary["expenses"]
    by_category, budgets = summary["by_category"], summary["budgets"]

    if income == 0 and expenses == 0:
        return ["Add a few income and expense transactions to unlock your budget insights."]
    if income > 0 and expenses > income:
        recs.append("Your expenses are higher than your income this month. Review non-essential spending first.")
    elif income > 0:
        rate = (income - expenses) / income * 100
        if rate < 10:
            recs.append("Your savings rate is below 10%. Try setting aside a small amount as soon as income arrives.")
        elif rate >= 20:
            recs.append("Good work: you are saving at least 20% of your recorded income this month.")

    for category, spent in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        limit = budgets.get(category)
        if limit is not None and limit > 0:
            if spent > limit:
                recs.append(f"{category} is over budget by ₹{spent - limit:,.0f}. Consider reducing spending in this category.")
            elif spent >= limit * 0.8:
                recs.append(f"{category} has used {spent / limit * 100:.0f}% of its budget. Keep an eye on the remaining limit.")

    if by_category:
        top = max(by_category, key=by_category.get)
        if len(recs) < 4:
            recs.append(f"{top} is your highest spending category so far. Check whether any purchases can be planned or reduced.")
    if not recs:
        recs.append("Your spending looks balanced based on the transactions entered. Keep recording purchases for more useful insights.")
    return recs[:5]

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES, today=date.today().isoformat())

@app.get("/api/dashboard")
def dashboard():
    month = request.args.get("month", current_month())
    summary = month_summary(month)
    return jsonify({
        "month": month,
        "income": summary["income"],
        "expenses": summary["expenses"],
        "balance": summary["balance"],
        "savings_rate": summary["savings_rate"],
        "by_category": summary["by_category"],
        "budgets": summary["budgets"],
        "transactions": summary["transactions"],
        "recommendations": make_recommendations(summary),
    })

@app.post("/api/predict")
def predict():
    data = request.get_json(silent=True) or {}
    description = str(data.get("description", "")).strip()
    if len(description) < 2:
        return jsonify({"error": "Enter a transaction description with at least 2 characters."}), 400
    prediction = classifier.predict([description])[0]
    probabilities = classifier.predict_proba([description])[0]
    confidence = float(max(probabilities)) * 100
    return jsonify({"category": prediction, "confidence": round(confidence, 1)})

@app.post("/api/transactions")
def add_transaction():
    data = request.get_json(silent=True) or {}
    description = str(data.get("description", "")).strip()
    kind = data.get("kind")
    category = str(data.get("category", "")).strip()
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0
    tx_date = str(data.get("tx_date", date.today().isoformat()))
    if not description or len(description) > 120:
        return jsonify({"error": "Description is required (maximum 120 characters)."}), 400
    if amount <= 0 or amount > 100000000:
        return jsonify({"error": "Enter a valid amount greater than zero."}), 400
    if kind not in ("income", "expense"):
        return jsonify({"error": "Choose income or expense."}), 400
    if kind == "expense" and category not in CATEGORIES:
        return jsonify({"error": "Choose a valid expense category."}), 400
    if kind == "income":
        category = "Income"
    try:
        datetime.strptime(tx_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Choose a valid transaction date."}), 400
    with get_db() as conn:
        conn.execute(
            "INSERT INTO transactions(description, amount, category, kind, tx_date) VALUES (?, ?, ?, ?, ?)",
            (description, amount, category, kind, tx_date)
        )
        conn.commit()
    return jsonify({"ok": True})

@app.delete("/api/transactions/<int:transaction_id>")
def delete_transaction(transaction_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Transaction not found."}), 404
    return jsonify({"ok": True})

@app.post("/api/budgets")
def save_budget():
    data = request.get_json(silent=True) or {}
    category = str(data.get("category", "")).strip()
    try:
        limit = float(data.get("monthly_limit", -1))
    except (TypeError, ValueError):
        limit = -1
    if category not in CATEGORIES or limit < 0 or limit > 100000000:
        return jsonify({"error": "Choose a category and enter a valid non-negative budget."}), 400
    with get_db() as conn:
        conn.execute(
            "INSERT INTO budgets(category, monthly_limit) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (category, limit)
        )
        conn.commit()
    return jsonify({"ok": True})

@app.get("/api/export")
def export_csv():
    month = request.args.get("month", current_month())
    rows = month_transactions(month)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Description", "Category", "Amount (INR)"])
    for r in rows:
        writer.writerow([r["tx_date"], r["kind"], r["description"], r["category"], r["amount"]])
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=budget-{month}.csv"}
    )

init_db()

if __name__ == "__main__":
    app.run(debug=True)
