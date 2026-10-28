# Nexus

Nexus is a Python/Flask personal finance application designed to help users understand and manage their money through budgeting, transaction tracking, savings goals, and financial insights.

The project was built as a learning project to practice **Python, Flask, CSV data handling, templates, UI design, and application logic**.

## Features

- **Student Mode** — simplified financial planning for students
- **Budget Management** — create and manage spending budgets
- **Transaction Tracking** — record and search transactions
- **Financial Health Score** — get an overview of your financial situation
- **What-If Simulator** — explore how different spending decisions could affect your finances
- **Can I Afford This?** — check whether a purchase fits within your available budget
- **Savings Goal** — track progress toward a savings target
- **Emergency Buffer** — keep track of money reserved for unexpected expenses
- **Money Learning** — basic financial education and useful money-management information
- **Reports** — view and export financial information
- **Demo Data** — sample data is included to make testing easier

## Tech Stack

- **Python**
- **Flask**
- **HTML**
- **CSS**
- **CSV**
- **Jinja2 Templates**

## Project Structure

```text
Nexus/
│
├── app.py
├── requirements.txt
│
├── templates/
│   ├── ...
│
├── static/
│   ├── ...
│
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/tabishjilani-CS50/Nexus.git
cd Nexus
```

### 2. Create a virtual environment

```bash
py -m venv venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

Then open the local Flask address shown in your terminal.

## Data Storage

Nexus uses **CSV files** for storing financial data rather than a database. This keeps the project simple and makes the underlying data easy to understand and inspect.

## What I Learned

Building Nexus helped me practice:

- Building web applications with Flask
- Working with CSV files in Python
- Creating and using Flask routes
- Passing data between Python and HTML templates
- Designing a simple web interface
- Implementing financial calculations and application logic
- Debugging Python and Flask applications
- Organizing a multi-file Python project

## Future Improvements

Some possible future improvements include:

- Database support
- User accounts and authentication
- More advanced financial analytics
- Interactive charts
- Automated financial reports
- API integrations
- Improved mobile responsiveness

## Author

**Tabish Jilani**

Python / Flask Developer & AI Engineering Student

GitHub: [@tabishjilani-CS](https://github.com/tabishjilani-CS)

---

*Built as a learning project to strengthen Python, Flask, and software development skills.*
