from flask import request, jsonify, render_template, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from models import db, User, Book

bcrypt = Bcrypt()

def register_routes(app):

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "GET":
            return render_template("register.html")

        data = request.form
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        new_user = User(name=data['name'], email=data['email'], password=hashed_password, role=data.get('role', 'user'))
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity={'email': user.email, 'role': user.role})
            session['user_role'] = user.role

            return redirect(url_for('books'))
        flash("Invalid credentials, please try again.", "error")
        return redirect(url_for('login')) 



    @app.route("/books", methods=["GET", "POST"])
    def books():
        
        user_role = session.get('user_role', None)

        if request.method == "GET":
            books = Book.query.all()
            return render_template("books.html", books=books, user_role=user_role)    
            
        if request.method == "POST" and user_role == 'admin':
            title = request.form['title']
            author = request.form['author']
            genre = request.form['genre']
            new_book = Book(title=title, author=author, genre=genre, available=True)
            db.session.add(new_book)
            db.session.commit()
            return redirect(url_for('books')) 
        else:
            flash("You do not have permission to add a book.", "error")
            return redirect(url_for('books'))
    

    @app.route("/borrow/<int:book_id>", methods=["POST"])
    def borrow_book(book_id):
        book = Book.query.get(book_id)
        if not book or not book.available:
            return jsonify({"message": "Book not available"}), 400
        book.available = False
        db.session.commit()
        return redirect(url_for('books'))

    

    @app.route("/return/<int:book_id>", methods=["POST"])
    def return_book(book_id):
        book = Book.query.get(book_id)
        if not book or book.available:
            return jsonify({"message": "Invalid return attempt"}), 400
        book.available = True
        db.session.commit()
        return redirect(url_for('books'))
