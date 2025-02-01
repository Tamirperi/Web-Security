
# Create your views here.
import json
import os
from django.shortcuts import render, redirect
from django.db import connection
import hashlib
import random
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


def home_view(request):
    return render(request, 'users/home.html')  # נטען את ה-HTML המתאים

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'password_config.json')
with open(config_path, 'r') as config_file:
    PASSWORD_CONFIG = json.load(config_file)


def validate_password(password):
    config = load_password_config()
    errors = []


    # בדיקת אורך סיסמה
    if len(password) < config['password_length']:
        errors.append(f"Password must be at least {config['password_length']} characters long.")

    # בדיקת אותיות גדולות
    if config['password_complexity']['uppercase'] and not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")

    # בדיקת אותיות קטנות
    if config['password_complexity']['lowercase'] and not any(char.islower() for char in password):
        errors.append("Password must contain at least one lowercase letter.")

    # בדיקת ספרות
    if config['password_complexity']['numbers'] and not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one digit.")

    # בדיקת תווים מיוחדים
    if config['password_complexity']['special_characters'] and not any(char in "!@#$%^&*()_+" for char in password):
        errors.append("Password must contain at least one special character.")

    return errors

##################
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if getattr(settings, 'SECURITY_MODE', True):  # מצב **מאובטח**
            # בדיקת תקינות הסיסמה לפי קובץ הקונפיגורציה
            password_errors = validate_password(password)
            if password_errors:
                return render(request, 'users/register.html', {'error': password_errors})

            # בדיקת שם משתמש באופן מאובטח
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = %s", [username])
                existing_user = cursor.fetchone()

            if existing_user:
                return render(request, 'users/register.html', {'error': 'Username already exists'})

            # הצפנת סיסמה עם HASH
            hashed_password = make_password(password)

            # הכנסת המשתמש עם מנגנון הגנה נגד SQL Injection
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                    [username, hashed_password, email]
                )

        else:  # מצב **פגיע**
            # בדיקה לא בטוחה של שם המשתמש
            query = f"SELECT id FROM users WHERE username = '{username}'"
            with connection.cursor() as cursor:
                cursor.execute(query)
                existing_user = cursor.fetchone()

            if existing_user:
                return render(request, 'users/register.html', {'error': 'Username already exists'})

            # הכנסת משתמש ללא הצפנת סיסמה
            query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
            with connection.cursor() as cursor:
                cursor.execute(query)

                # **התקפה פוטנציאלית** - מחיקת כל הלקוחות אם שם המשתמש מכיל שאילתה זדונית
                if "DELETE FROM customers" in username:
                    cursor.execute("DELETE FROM customers")

        return redirect('success')

    return render(request, 'users/register.html')

############
def add_customer(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        user_id = request.session.get('user_id')

        with connection.cursor() as cursor:
            if getattr(settings, 'SECURITY_MODE', True):  # מצב מאובטח
                cursor.execute(
                    "INSERT INTO customers (full_name, phone_number, address, user_id) VALUES (%s, %s, %s, %s)",
                    [full_name, phone_number, address, user_id]
                )
            else:  # מצב פגיע - SQL Injection אפשרי
                query = f"INSERT INTO customers (full_name, phone_number, address, user_id) VALUES ('{full_name}', '{phone_number}', '{address}', '{user_id}')"
                cursor.execute(query)  # שאילתה ישירה - חשופה ל-SQL Injection 

        return redirect('customer_success')

    return render(request, 'users/add_customer.html')


############
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if getattr(settings, 'SECURITY_MODE', True):  # אם SECURITY_MODE מופעל, מצב מאובטח
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, password FROM users WHERE username = %s", [username])
                user = cursor.fetchone()

            if user:
                stored_password = user[1]
                if check_password(password, stored_password):  # בדיקת סיסמה מול HASH
                    request.session['user_id'] = user[0]
                    return redirect('customer_list')
        else:
            # מצב **פגיע**: שימוש בשאילתה ישירה
            query = f"SELECT id, password FROM users WHERE username = '{username}' AND password = '{password}'"
            print(query)  # הצגת השאילתה (לבדיקות בלבד)

            with connection.cursor() as cursor:
                cursor.execute(query)
                user = cursor.fetchone()

            if user:
                request.session['user_id'] = user[0]
                return redirect('customer_list')

        return render(request, 'users/login.html', {'error': 'Invalid username or password'})

    return render(request, 'users/login.html')





def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        # בדיקת תקינות הסיסמה החדשה
        password_errors = validate_password(new_password)
        if password_errors:
            return render(request, 'users/change_password.html', {'error': password_errors})

        # בדיקת סיסמה נוכחית במסד הנתונים
        user_id = request.session.get('user_id')
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE id = %s AND password = %s",
                [user_id, current_password]
            )
            user = cursor.fetchone()

        if not user:
            # אם הסיסמה הנוכחית אינה נכונה
            return render(request, 'users/change_password.html', {'error': 'Current password is incorrect'})

        # עדכון הסיסמה במסד הנתונים
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                [new_password, user_id]
            )

        return redirect('password_success')  # הפניה למסך הצלחה

    return render(request, 'users/change_password.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # בדיקה אם המייל קיים במסד הנתונים
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", [email])
            user = cursor.fetchone()

        if user:
            # יצירת קוד איפוס ושמירתו כ-Hash
            reset_code = str(random.randint(100000, 999999))  # קוד אקראי בן 6 ספרות
            hashed_code = hashlib.sha1(reset_code.encode()).hexdigest()

            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE email = %s",
                    [hashed_code, email]
                )

            # הצגת הקוד על המסך
            return render(request, 'users/forgot_password.html', {
                'success': f'Your reset code is: {reset_code}'
            })
        else:
            # המייל לא נמצא במערכת
            return render(request, 'users/forgot_password.html', {
                'error': 'Email not found'
            })

    return render(request, 'users/forgot_password.html')

def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        reset_code = request.POST.get('reset_code')
        new_password = request.POST.get('new_password')

        # בדיקת קוד האיפוס
        hashed_code = hashlib.sha1(reset_code.encode()).hexdigest()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE email = %s AND password = %s",
                [email, hashed_code]
            )
            user = cursor.fetchone()

        if user:
            # **בדיקת תקינות הסיסמה החדשה לפי קובץ הקונפיגורציה**
            password_errors = validate_password(new_password)
            if password_errors:
                return render(request, 'users/reset_password.html', {'error': password_errors})

            # **שמירת הסיסמה החדשה עם הצפנה**
            hashed_password = make_password(new_password)

            # עדכון הסיסמה החדשה במסד הנתונים
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE email = %s",
                    [hashed_password, email]
                )
            return redirect('password_success')  # הפניה למסך הצלחה

        else:
            return render(request, 'users/reset_password.html', {'error': 'Invalid reset code or email'})

    return render(request, 'users/reset_password.html')



def customer_list(request):
    user_id = request.session.get('user_id')  # שליפת user_id מה-Session
    
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, full_name, phone_number, address FROM customers WHERE user_id = %s",
            [user_id]
        )
        customers = cursor.fetchall()

    return render(request, 'users/customer_list.html', {
        'customers': customers,
        'SECURITY_MODE': settings.SECURITY_MODE  # העברת המתג לטמפלט
    })


def update_customer(request, customer_id):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        phone_number = request.POST['phone_number']
        address = request.POST['address']

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE customers SET full_name = %s, phone_number = %s, address = %s WHERE id = %s",
                [full_name, phone_number, address, customer_id]
            )
        return redirect('customer_list')

    with connection.cursor() as cursor:
        cursor.execute("SELECT full_name, phone_number, address FROM customers WHERE id = %s", [customer_id])
        customer = cursor.fetchone()

    return render(request, 'users/update_customer.html', {'customer': customer})



def delete_customer(request, customer_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM customers WHERE id = %s", [customer_id])
    return redirect('customer_list')


def delete_user(request, user_id):
    # מחיקת המשתמש על פי user_id
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s", [user_id])

    return redirect('login')  # חזרה למסך ההתחברות לאחר המחיקה


def logout_view(request):
    request.session.flush()  # מחיקת כל הנתונים של ה-Session
    return redirect('login')  # הפניה חזרה למסך ההתחברות


def load_password_config():
    config_path = os.path.join(settings.BASE_DIR, 'password_config.json')
    with open(config_path, 'r') as file:
        return json.load(file)