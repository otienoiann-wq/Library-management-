# Library Management System

A complete web-based Library Management System built with **Python + Flask + SQLite + Bootstrap 5**.

Perfect as an IT student project / final year project.

## Features

- Admin Login / Logout
- **Books Management** (Add, Edit, Delete, Search)
- **Members Management** (Register, Edit, Delete, Search)
- **Issue Book** with customizable loan period
- **Return Book** with automatic fine calculation
- Overdue tracking
- Dashboard with live statistics
- Reports (Overdue books + Most borrowed books)
- Responsive UI (Bootstrap 5)

## Default Login

```
Username: admin
Password: admin123
```

## Tech Stack

- Python 3.8+
- Flask 3
- Flask-SQLAlchemy
- SQLite
- Bootstrap 5 + Bootstrap Icons

## Project Structure

```
library-management-system/
├── app.py                 # Main application
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── books.html
│   ├── add_book.html
│   ├── edit_book.html
│   ├── members.html
│   ├── add_member.html
│   ├── edit_member.html
│   ├── issue.html
│   ├── issues.html
│   └── reports.html
└── static/                # (optional custom CSS/JS)
```

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/library-management-system.git
cd library-management-system
```

### 2. Create virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

Open your browser and go to:  
**http://127.0.0.1:5000**

## Screenshots

(Add screenshots of Dashboard, Books, Issue page, Reports after running)

## Future Improvements (Optional)

- Member login portal
- Email notifications for due dates
- Barcode / QR code support
- Export reports to PDF / Excel
- Book reservation system
- Role-based access (Librarian / Super Admin)

## Author

IT Student Project – Library Management System

---

Feel free to star ⭐ the repo if you find it useful!
