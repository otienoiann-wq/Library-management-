from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'library-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELS ====================

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    category = db.Column(db.String(50), default='General')
    quantity = db.Column(db.Integer, default=1)
    available = db.Column(db.Integer, default=1)
    published_year = db.Column(db.Integer)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Book {self.title}>'


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')  # Active / Inactive

    def __repr__(self):
        return f'<Member {self.name}>'


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    fine = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Issued')  # Issued / Returned

    book = db.relationship('Book', backref=db.backref('issues', lazy=True))
    member = db.relationship('Member', backref=db.backref('issues', lazy=True))

    def __repr__(self):
        return f'<Issue {self.id}>'


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # plain for demo (hash in real apps)


# ==================== HELPERS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def calculate_fine(due_date, return_date=None):
    """Simple fine: 5 currency units per day overdue"""
    if return_date is None:
        return_date = datetime.utcnow()
    if return_date > due_date:
        days = (return_date - due_date).days
        return days * 5.0
    return 0.0


# ==================== ROUTES ====================

@app.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin_id'] = admin.id
            session['username'] = admin.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_books = Book.query.count()
    total_members = Member.query.count()
    issued_books = Issue.query.filter_by(status='Issued').count()
    overdue = Issue.query.filter(
        Issue.status == 'Issued',
        Issue.due_date < datetime.utcnow()
    ).count()

    recent_issues = Issue.query.order_by(Issue.issue_date.desc()).limit(5).all()
    return render_template('dashboard.html',
                           total_books=total_books,
                           total_members=total_members,
                           issued_books=issued_books,
                           overdue=overdue,
                           recent_issues=recent_issues)


# ---------- BOOKS ----------

@app.route('/books')
@login_required
def books():
    q = request.args.get('q', '')
    if q:
        books_list = Book.query.filter(
            (Book.title.ilike(f'%{q}%')) |
            (Book.author.ilike(f'%{q}%')) |
            (Book.isbn.ilike(f'%{q}%')) |
            (Book.category.ilike(f'%{q}%'))
        ).all()
    else:
        books_list = Book.query.order_by(Book.title).all()
    return render_template('books.html', books=books_list, q=q)


@app.route('/books/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        category = request.form.get('category') or 'General'
        quantity = int(request.form.get('quantity', 1))
        year = request.form.get('published_year') or None

        if Book.query.filter_by(isbn=isbn).first():
            flash('A book with this ISBN already exists.', 'danger')
            return redirect(url_for('add_book'))

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            category=category,
            quantity=quantity,
            available=quantity,
            published_year=int(year) if year else None
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('books'))
    return render_template('add_book.html')


@app.route('/books/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.isbn = request.form.get('isbn')
        book.category = request.form.get('category') or 'General'
        new_qty = int(request.form.get('quantity', 1))
        diff = new_qty - book.quantity
        book.quantity = new_qty
        book.available = max(0, book.available + diff)
        year = request.form.get('published_year')
        book.published_year = int(year) if year else None
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books'))
    return render_template('edit_book.html', book=book)


@app.route('/books/delete/<int:id>')
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    if Issue.query.filter_by(book_id=id, status='Issued').first():
        flash('Cannot delete book that is currently issued.', 'danger')
        return redirect(url_for('books'))
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted.', 'info')
    return redirect(url_for('books'))


# ---------- MEMBERS ----------

@app.route('/members')
@login_required
def members():
    q = request.args.get('q', '')
    if q:
        members_list = Member.query.filter(
            (Member.name.ilike(f'%{q}%')) |
            (Member.email.ilike(f'%{q}%')) |
            (Member.phone.ilike(f'%{q}%'))
        ).all()
    else:
        members_list = Member.query.order_by(Member.name).all()
    return render_template('members.html', members=members_list, q=q)


@app.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if Member.query.filter_by(email=email).first():
            flash('Member with this email already exists.', 'danger')
            return redirect(url_for('add_member'))

        member = Member(name=name, email=email, phone=phone, address=address)
        db.session.add(member)
        db.session.commit()
        flash('Member registered successfully!', 'success')
        return redirect(url_for('members'))
    return render_template('add_member.html')


@app.route('/members/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    member = Member.query.get_or_404(id)
    if request.method == 'POST':
        member.name = request.form.get('name')
        member.email = request.form.get('email')
        member.phone = request.form.get('phone')
        member.address = request.form.get('address')
        member.status = request.form.get('status', 'Active')
        db.session.commit()
        flash('Member updated!', 'success')
        return redirect(url_for('members'))
    return render_template('edit_member.html', member=member)


@app.route('/members/delete/<int:id>')
@login_required
def delete_member(id):
    member = Member.query.get_or_404(id)
    if Issue.query.filter_by(member_id=id, status='Issued').first():
        flash('Cannot delete member who has issued books.', 'danger')
        return redirect(url_for('members'))
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted.', 'info')
    return redirect(url_for('members'))


# ---------- ISSUE / RETURN ----------

@app.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_book():
    if request.method == 'POST':
        book_id = int(request.form.get('book_id'))
        member_id = int(request.form.get('member_id'))
        days = int(request.form.get('days', 14))

        book = Book.query.get_or_404(book_id)
        member = Member.query.get_or_404(member_id)

        if book.available <= 0:
            flash('No copies available for this book.', 'danger')
            return redirect(url_for('issue_book'))

        if member.status != 'Active':
            flash('Member is not active.', 'danger')
            return redirect(url_for('issue_book'))

        due = datetime.utcnow() + timedelta(days=days)
        issue = Issue(
            book_id=book_id,
            member_id=member_id,
            due_date=due,
            status='Issued'
        )
        book.available -= 1
        db.session.add(issue)
        db.session.commit()
        flash(f'Book "{book.title}" issued to {member.name}. Due: {due.strftime("%Y-%m-%d")}', 'success')
        return redirect(url_for('issues'))

    books = Book.query.filter(Book.available > 0).order_by(Book.title).all()
    members = Member.query.filter_by(status='Active').order_by(Member.name).all()
    return render_template('issue.html', books=books, members=members)


@app.route('/return/<int:id>')
@login_required
def return_book(id):
    issue = Issue.query.get_or_404(id)
    if issue.status == 'Returned':
        flash('This book is already returned.', 'warning')
        return redirect(url_for('issues'))

    issue.return_date = datetime.utcnow()
    issue.fine = calculate_fine(issue.due_date, issue.return_date)
    issue.status = 'Returned'
    issue.book.available += 1
    db.session.commit()

    msg = f'Book returned successfully.'
    if issue.fine > 0:
        msg += f' Fine: {issue.fine:.2f}'
    flash(msg, 'success')
    return redirect(url_for('issues'))


@app.route('/issues')
@login_required
def issues():
    status = request.args.get('status', 'all')
    query = Issue.query
    if status == 'issued':
        query = query.filter_by(status='Issued')
    elif status == 'returned':
        query = query.filter_by(status='Returned')
    elif status == 'overdue':
        query = query.filter(Issue.status == 'Issued', Issue.due_date < datetime.utcnow())

    issues_list = query.order_by(Issue.issue_date.desc()).all()
    return render_template('issues.html', issues=issues_list, status=status, now=datetime.utcnow())


# ---------- REPORTS ----------

@app.route('/reports')
@login_required
def reports():
    overdue_issues = Issue.query.filter(
        Issue.status == 'Issued',
        Issue.due_date < datetime.utcnow()
    ).all()

    # Most borrowed books
    from sqlalchemy import func
    popular = db.session.query(
        Book.title, Book.author, func.count(Issue.id).label('times')
    ).join(Issue).group_by(Book.id).order_by(func.count(Issue.id).desc()).limit(10).all()

    return render_template('reports.html', overdue=overdue_issues, popular=popular, now=datetime.utcnow())


# ==================== INIT DB ====================

def init_db():
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', password='admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created → username: admin  |  password: admin123")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
