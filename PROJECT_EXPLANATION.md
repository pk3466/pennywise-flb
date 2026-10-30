# FLB Project Explanation

## Project title
AI-Based Personal Budget Planner

## Problem statement
Many people find it difficult to monitor daily expenses, understand where their money goes, and maintain a monthly budget. Manual tracking can be time-consuming and users may miss spending patterns.

## Proposed solution
Pennywise is a web-based personal budget planner. Users record income and expenses. A machine-learning model predicts an expense category from the transaction description. The dashboard calculates monthly totals, savings rate, and category-wise spending. Users can set budgets and receive suggestions based on their financial activity.

## Objectives
- Make personal income and expense tracking simple.
- Use machine learning to categorize expenses from text.
- Show spending patterns visually.
- Help users compare spending with category budgets.
- Provide understandable savings and budget recommendations.

## AI/ML implementation
The project uses supervised text classification:
- TF-IDF converts the transaction description into numeric word features.
- Multinomial Naive Bayes classifies the description into a category.
- Categories include Food, Transport, Shopping, Bills, Entertainment, Health, Education, and Personal Care.
- The model returns its predicted category and a confidence score.

The budget recommendations are generated from the user's recorded income, expenses, savings rate, and budget limits. Be clear during evaluation: the expense categorizer is the trained ML component; the recommendation engine is a transparent rule-based component.

## System flow
1. User enters a transaction description and amount.
2. Frontend sends the description to Flask.
3. Scikit-learn predicts the expense category.
4. User confirms or changes the suggested category.
5. Flask stores the transaction in SQLite.
6. Dashboard fetches monthly data and calculates totals.
7. Chart.js displays category spending.
8. Recommendation logic checks savings rate and budget usage.

## Division of work for two students
**Student 1 — Frontend and user experience**
- Design the dashboard using HTML and CSS.
- Implement transaction form and browser-side interactions.
- Display charts and budget progress using JavaScript and Chart.js.

**Student 2 — Backend and AI/ML**
- Build Flask API endpoints.
- Create and manage SQLite tables.
- Train and integrate the TF-IDF + Naive Bayes classifier.
- Implement monthly calculations and recommendations.

Both students should understand the complete workflow and test the project together.

## Limitations and future scope
- The classifier uses a small demonstration dataset, so accuracy is limited.
- Transactions are entered manually; bank account integration is not included.
- The current prototype uses one local database and does not include user login.
- Future versions can use a larger labeled dataset, CSV bank-statement import, user accounts, recurring payments, and personalized forecasting.

## Short presentation script
"Good morning. Our project is AI-Based Personal Budget Planner, named Pennywise. The problem we are solving is that people often struggle to track their daily expenses and understand their spending habits.

Our application allows users to add their income and expenses. Its machine-learning model reads the transaction description and predicts a category such as Food, Transport, Shopping, or Bills. We used TF-IDF to convert text into numerical features and Multinomial Naive Bayes for classification.

The dashboard shows total income, expenses, available balance, savings rate, and a chart of category-wise spending. Users can also set monthly budgets and receive suggestions when they are close to or above their limits.

We built the frontend using HTML, CSS, and JavaScript, the backend using Python Flask, the database using SQLite, and the machine-learning model using Scikit-learn. This project demonstrates how AI can make personal financial management easier and more organized. Thank you."
