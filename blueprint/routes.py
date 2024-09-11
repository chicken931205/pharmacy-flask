import secrets

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash

from models import db, User, Product, CounsellingHistory

routes_bp = Blueprint('routes', __name__)


@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')


@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        new_user = User(
            full_name=data['fullName'],
            phone=data['phone'],
            pharmacy=data['pharmacy'],
            email=data['email'],
            password=data['password'],
            payment_method=data['paymentMethod']
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('routes.dashboard'))
    return render_template('signup.html')


@routes_bp.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.all()
    records = CounsellingHistory.query.filter_by(user_id=current_user.id).all()
    not_cashed_out_price_sum = 0
    not_cashed_out_count = 0

    for record in records:
        product_price = record.product.price
        if not record.cashed_out:
            not_cashed_out_price_sum += product_price
            not_cashed_out_count += 1

    return render_template(
        'dashboard.html',
        products=products,
        records=records,
        cashed_out_price_sum=current_user.accumulated_amount,
        cashed_out_count=current_user.products_cashed_out,
        not_cashed_out_price_sum=current_user.counselling_fee,
        not_cashed_out_count=current_user.products_not_cashed_out
    )


@routes_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for('routes.dashboard'))

    user_id_for_history = None
    user_for_history = None
    scroll_to_id = None

    products = Product.query.all()
    users = User.query.filter(User.id != current_user.id).all()

    records = None
    if request.method == "GET":
        user_id_for_history = request.args.get('viewHistories')

    for user in users:
        if user_id_for_history == str(user.id):
            records = user.counselling_histories
            user_for_history = user
            scroll_to_id = 'counsellingHistory'

    return render_template(
        'admin-dashboard.html',
        records=records,
        user_for_history=user_for_history,
        users=users,
        products=products,
        cashed_out_price_sum=sum(user.accumulated_amount for user in users),
        cashed_out_count=sum(user.products_cashed_out for user in users),
        not_cashed_out_price_sum=sum(user.counselling_fee for user in users),
        not_cashed_out_count=sum(user.products_not_cashed_out for user in users),
        scroll_to_id=scroll_to_id
    )


def update_user(user, commit=True):
    full_name = request.form.get('fullName')
    new_password = request.form.get('password')
    pharmacy_name = request.form.get('pharmacy')
    pharmacy_phone = request.form.get('phone')
    payment_method = request.form.get('paymentMethod')

    user.full_name = full_name
    user.pharmacy = pharmacy_name
    user.phone = pharmacy_phone
    user.payment_method = payment_method

    if new_password:
        user.password = generate_password_hash(new_password)

    if commit:
        try:
            db.session.commit()
            db.session.refresh(user)
        except Exception as e:
            db.session.rollback()
    else:
        return user


@routes_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        update_user(current_user)

    return render_template(
        'profile.html',
        user=current_user
    )


@routes_bp.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user = User.query.filter(User.id == user_id).first()
    if request.method == 'POST':
        user = update_user(user, False)
        user.counselling_fee = float(request.form.get('cfee'))
        user.products_not_cashed_out = int(request.form.get('pcnout'))
        user.products_cashed_out = int(request.form.get('pcout'))
        user.accumulated_amount = float(request.form.get('accamt'))

        try:
            db.session.commit()
            db.session.refresh(user)
        except Exception as e:
            db.session.rollback()

    return render_template(
        'profile.html',
        user=user
    )


@routes_bp.route('/delete/<int:user_id>', methods=['GET'])
@login_required
def delete_profile(user_id):
    user = User.query.filter(User.id == user_id).first()
    histories = CounsellingHistory.query.filter_by(user_id=user_id).all()
    for history in histories:
        db.session.delete(history)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('routes.admin'))


@routes_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))


@routes_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    else:
        return redirect(url_for('routes.login'))


@routes_bp.route('/add-counselling', methods=['POST'])
@login_required
def add_counselling():
    product_id = request.form.get('product_id')
    counselling_indication = request.form.get('counselling')
    quantity = request.form.get('quantity')

    try:
        counselling_history = CounsellingHistory(
            product_id=product_id,
            counselling_indication=counselling_indication,
            cashed_out=False,
            user_id=current_user.id,
            quantity=quantity
        )
        db.session.add(counselling_history)
        db.session.flush()

        current_user.products_not_cashed_out += 1
        current_user.counselling_fee += counselling_history.product.price

        db.session.commit()
    except Exception as e:
        print("Counselling not added, error: ", e)
        db.session.rollback()

    return redirect(url_for('routes.dashboard'))


@routes_bp.route('/delete-counselling-history/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    record = CounsellingHistory.query.get_or_404(record_id)

    if not record.cashed_out:
        current_user.counselling_fee -= record.product.price
        current_user.products_not_cashed_out -= 1

    try:
        db.session.delete(record)
        db.session.commit()
    except:
        print("Failed to delete counselling history, error: ", e)
        db.session.rollback()
    return redirect(url_for('routes.dashboard'))


@routes_bp.route('/cash_out', methods=['POST'])
@login_required
def cash_out():
    records_to_update = CounsellingHistory.query.filter_by(
        user_id=current_user.id,
        cashed_out=False
    ).all()

    accumulated_sum = current_user.counselling_fee
    count_of_products = current_user.products_not_cashed_out
    for record in records_to_update:
        record.cashed_out = True

    current_user.products_not_cashed_out = 0
    current_user.counselling_fee = 0

    current_user.accumulated_amount += accumulated_sum
    current_user.products_cashed_out += count_of_products

    send_email(accumulated_sum, records_to_update)

    try:
        db.session.commit()
    except Exception as e:
        print("Failed to cash out, error: ", e)
        db.session.rollback()
    return redirect(url_for('routes.dashboard'))


def send_email(accumulated_sum, counselling_histories):
    from flask_mail import Message
    from app import mail
    try:
        msg = Message('Cashout Summary', recipients=['hassan.l@phldistributions.com', current_user.email])
        msg.body = f"User {current_user.full_name} has cashed out.\n\n"
        msg.body += "Counselings:\n"
        for record in counselling_histories:
            msg.body += f"- {record.product.name}: ${record.product.price} for {record.counselling_indication}\n"
        msg.body += f"\nTotal cashed out: ${accumulated_sum}\n"
        msg.body += f"\nProfile Information:\nFull Name: {current_user.full_name}\nEmail: {current_user.email}\nPharmacy Phone: {current_user.phone}\nPharmacy Name: {current_user.pharmacy}\nPayment Method: {current_user.payment_method}"

        mail.send(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_password_reset_email(email, new_password):
    from flask_mail import Message
    from app import mail
    try:
        msg = Message('Password Reset Request', recipients=[email])
        msg.body = f"Your new password is:\n{new_password}\n\nYou can always reset your password by visitng the Profile page."
        mail.send(msg)
        print(f'Password reset email sent to {email}')
    except Exception as e:
        print(f"Failed to send email: {e}")


@routes_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user is not None:
            new_password = secrets.token_urlsafe(16)
            user.password = generate_password_hash(new_password)
            db.session.commit()

            send_password_reset_email(email, new_password)
        return render_template('confirm-mail.html', email=email)
    return render_template('forgot-password.html')
