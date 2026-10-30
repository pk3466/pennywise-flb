# Pennywise — AI-Based Personal Budget Planner

A beginner-friendly Finance & Banking project built with Flask, SQLite, and a real machine-learning text classifier.

## Features

- Add income and expense transactions.
- Predict an expense category from its description using TF-IDF + Multinomial Naive Bayes.
- View monthly income, expenses, balance, and savings rate.
- Visualize expense categories with a doughnut chart.
- Set monthly category budgets and see progress.
- Receive rule-based financial recommendations based on recorded activity.
- Export monthly transactions to CSV.
- Delete transactions and switch between months.

## Requirements

- Python 3.10 or newer
- Internet connection for the Google Font and Chart.js CDN (the core app runs locally; charts need the Chart.js CDN).

## Run locally

1. Extract the ZIP file.
2. Open a terminal in the extracted `ai_personal_budget_planner` folder.
3. Create and activate a virtual environment (recommended):

   **Windows**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   python app.py
   ```
6. Open `http://127.0.0.1:5000` in your browser.

The SQLite database `budget.db` is created automatically on first run.

## How the AI/ML part works

1. The app has a small labeled training set of example transaction descriptions grouped into expense categories.
2. `TfidfVectorizer` converts words and two-word phrases into numerical features.
3. `MultinomialNB` learns which words are associated with each category.
4. When a user types a description such as "Uber ride to college", the model predicts a category and returns its confidence score.
5. The suggested category is filled into the transaction form. The user can change it before saving.

This is a real supervised machine-learning implementation, but it is a classroom prototype trained on a small demonstration dataset. Its predictions are not guaranteed to be correct. A larger, diverse, real-world labeled dataset would improve accuracy.

## Project architecture

- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Backend:** Python Flask REST endpoints
- **Machine learning:** Scikit-learn TF-IDF + Multinomial Naive Bayes
- **Database:** SQLite

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/dashboard?month=YYYY-MM` | Monthly summary and transactions |
| POST | `/api/predict` | Predict category from description |
| POST | `/api/transactions` | Add income or expense |
| DELETE | `/api/transactions/<id>` | Delete a transaction |
| POST | `/api/budgets` | Save/update a category budget |
| GET | `/api/export?month=YYYY-MM` | Download monthly CSV |

## Suggested demo

1. Add income: `Monthly stipend`, ₹15,000.
2. Add expense: `Uber ride to college`, ₹250. Observe the AI category suggestion.
3. Add expense: `Lunch at cafe`, ₹180.
4. Add expense: `Netflix subscription`, ₹199.
5. Set a Food monthly budget, for example ₹2,500.
6. Show the dashboard, spending chart, budget progress, and AI insights.
7. Export the month as a CSV file.

## Important note

Use fictional/demo transactions for classroom evaluation. Do not enter bank passwords, card numbers, UPI PINs, or other sensitive financial information. This project is an educational budgeting assistant, not regulated financial advice.
