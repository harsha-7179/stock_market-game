from flask import render_template, redirect, url_for, request, flash, session
from app import app, db
from app.models import User, StockTransaction
from werkzeug.security import generate_password_hash, check_password_hash
import pytz
# ✅ Import from flask_login
from flask_login import login_required, login_user, logout_user, current_user
from flask import render_template, session, redirect, url_for
from app import app, db
from app.models import User, StockTransaction
from flask_login import current_user, login_required
from sqlalchemy import func, case


@app.route('/')
def home():
    return render_template("index.html")

import re  # ✅ Add at top if not already

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("❌ Username already taken.")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("❌ Email already registered.")
            return redirect(url_for('register'))

        # Password validation (optional)
        import re
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(pattern, password):
            flash("❌ Password must meet the criteria.")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("✅ Registration successful!")
        return redirect(url_for('login'))

    return render_template("register.html")



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for('login'))


from flask_login import login_user  # already imported at the top

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)  # ✅ THIS LINE IS MISSING
            flash("Logged in successfully!")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!")
            return redirect(url_for('login'))

    return render_template("login.html")




from sqlalchemy import func, case
import pytz



@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    balance = user.balance

    total_buy = db.session.query(
        func.sum(StockTransaction.price * StockTransaction.shares)
    ).filter_by(user_id=user.id, type='BUY').scalar() or 0

    total_sell = db.session.query(
        func.sum(StockTransaction.price * StockTransaction.shares)
    ).filter_by(user_id=user.id, type='SELL').scalar() or 0

    total_earnings = total_sell - total_buy

    holdings_query = db.session.query(
        StockTransaction.stock_name,
        (
            func.sum(case((StockTransaction.type == 'BUY', StockTransaction.shares), else_=0)) -
            func.sum(case((StockTransaction.type == 'SELL', StockTransaction.shares), else_=0))
        ).label('total_shares')
    ).filter_by(user_id=user.id).group_by(StockTransaction.stock_name).all()

    holdings = {stock: shares for stock, shares in holdings_query if shares > 0}

    # ✅ Get recent transactions
    recent_transactions = StockTransaction.query.filter_by(user_id=user.id)\
        .order_by(StockTransaction.timestamp.desc()).limit(5).all()

    # ✅ Convert to IST
    ist = pytz.timezone('Asia/Kolkata')
    for txn in recent_transactions:
        if txn.timestamp.tzinfo is None:
            txn.timestamp = txn.timestamp.replace(tzinfo=pytz.utc)
        txn.timestamp = txn.timestamp.astimezone(ist)

    # ✅ Track level change
    level = int(balance // 10000)
    prev_level = session.get('prev_level')
    popup_message = None
    popup_class = ""

    if prev_level is not None:
        if level > prev_level:
            popup_message = "🎉 Congratulations! You leveled up!"
            popup_class = "level-up"
        elif level < prev_level:
            popup_message = "⚠️ Level decreased. Better luck next time!"
            popup_class = "level-down"

    session['prev_level'] = level


    # ✅ Get stock prices
    stocks = generate_fake_stock_prices()

    return render_template(
        'dashboard.html',
        user=user,
        balance=balance,
        level=level,
        total_earnings=total_earnings,
        holdings=holdings,
        transactions=recent_transactions,
        stocks=stocks,
        chart_labels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        chart_data=[1000, 1200, 1500, 1300, 1800],
        popup_message=popup_message,
        popup_class=popup_class
    )


@app.route('/buy', methods=["GET", "POST"])
@login_required
def buy():
    stocks = generate_fake_stock_prices()

    if request.method == "POST":
        stock = request.form['stock']
        price = float(request.form['price'])
        shares = int(request.form['shares'])

        user = current_user
        total_cost = price * shares

        if user.balance < total_cost:
            flash("Insufficient balance!")
        else:
            user.balance -= total_cost
            transaction = StockTransaction(user_id=user.id, stock_name=stock, shares=shares, price=price, type='BUY')
            db.session.add(transaction)
            db.session.commit()
            flash(f"Bought {shares} shares of {stock}!")

        return redirect(url_for('dashboard'))

    return render_template('buy.html', stocks=stocks)
@app.route('/sell', methods=["GET", "POST"])
@login_required
def sell():
    stocks = generate_fake_stock_prices()

    if request.method == "POST":
        stock = request.form['stock']
        price = float(request.form['price'])
        shares = int(request.form['shares'])

        user = current_user
        total_bought = db.session.query(db.func.sum(StockTransaction.shares)).filter_by(user_id=user.id, stock_name=stock, type='BUY').scalar() or 0
        total_sold = db.session.query(db.func.sum(StockTransaction.shares)).filter_by(user_id=user.id, stock_name=stock, type='SELL').scalar() or 0
        owned = total_bought - total_sold

        if shares > owned:
            flash("Not enough shares to sell!")
        else:
            user.balance += price * shares
            transaction = StockTransaction(user_id=user.id, stock_name=stock, shares=shares, price=price, type='SELL')
            db.session.add(transaction)
            db.session.commit()
            flash(f"Sold {shares} shares of {stock}!")

        return redirect(url_for('dashboard'))

    return render_template('sell.html', stocks=stocks)


# here down is stock changing plan code bro 

import random

def generate_fake_stock_prices():
    base_prices = {
        'ESYASOFT': 3640.55,
        'TCS': 1523.20,
        'WIPRO': 432.90,
        'RELIANCE': 2845.75,
        'HDFCBANK': 1689.30
    }
    
    fluctuated_prices = {}
    for stock, price in base_prices.items():
        # Change price randomly by ±1% to 5%
        change_percent = random.uniform(-0.05, 0.05)
        new_price = round(price * (1 + change_percent), 2)
        fluctuated_prices[stock] = new_price

    return fluctuated_prices
@app.route('/reset')
@login_required
def reset():
    user = current_user

    # Reset balance
    user.balance = 100000.0

    # Delete user's transactions
    StockTransaction.query.filter_by(user_id=user.id).delete()

    db.session.commit()
    flash("Portfolio reset successfully!")
    return redirect(url_for('dashboard'))
@app.route('/forgot-password', methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form['username']
        new_password = request.form['new_password']

        user = User.query.filter_by(username=username).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Password reset successful! Please login.")
            return redirect(url_for('login'))
        else:
            flash("Username not found.")
    
    return render_template("forgot_password.html")
@app.route('/delete_account', methods=["POST"])
@login_required
def delete_account():
    user = current_user

    # Delete all transactions first (to avoid foreign key constraints)
    StockTransaction.query.filter_by(user_id=user.id).delete()

    # Delete user
    db.session.delete(user)
    db.session.commit()

    flash("Your account has been permanently deleted.")
    return redirect(url_for('home'))
