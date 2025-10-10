from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from database.db_connection import get_connection, ensure_table_exists
from mysql.connector import Error, IntegrityError

app = Flask(__name__)
app.secret_key = "supersecretkey"   # required for flash messages
ensure_table_exists()

import re

def normalize_phone(phone):
    """Cleans and standardizes Indian phone numbers."""
    phone = phone.strip()
    # Remove all non-digit characters (+, spaces, -, etc.)
    phone = re.sub(r'\D', '', phone)

    # Remove leading country code '91' or '0' if present
    if phone.startswith('91') and len(phone) > 10:
        phone = phone[2:]
    elif phone.startswith('0') and len(phone) > 10:
        phone = phone[1:]

    # Ensure it's exactly 10 digits
    return phone[-10:] if len(phone) >= 10 else phone

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_connection()
    if conn is None:
        flash("❌ Unable to connect to the database. Please check if MySQL is running.", "danger")
        return render_template('index.html', persons=[], headers=[], is_empty=True)

    cursor = conn.cursor()

    # Handle search query (from form)
    search_query = request.args.get('q', '').strip()

    if search_query:
        sql = """
            SELECT * FROM Persons
            WHERE name LIKE %s OR email LIKE %s OR phone LIKE %s
        """
        wildcard = f"%{search_query}%"
        cursor.execute(sql, (wildcard, wildcard, wildcard))
    else:
        cursor.execute("SELECT * FROM Persons")

    persons = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]

    cursor.close()
    conn.close()

    is_empty = len(persons) == 0

    return render_template(
        'index.html',
        persons=persons,
        headers=headers,
        is_empty=is_empty,
        search_query=search_query
    )

@app.route('/add', methods=['GET', 'POST'])
def add_person():
    if request.method == 'POST':
        name = request.form['name'].strip()
        dob = request.form['dob'].strip()
        gender = request.form['gender'].strip()
        phone = normalize_phone(request.form['phone'])
        email = request.form['email'].strip()   # ✅ Added line
        address = request.form['address'].strip()

        # 🧱 Basic mandatory field check
        if not name or not phone or not email:
            flash("⚠️ Name, phone, and email are required fields.", "warning")
            return redirect(url_for('add_person'))

        # 🧠 Validate date of birth format and logic
        if dob:
            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                if dob_date > date.today():
                    flash("⚠️ Date of birth cannot be in the future.", "warning")
                    return redirect(url_for('add_person'))
            except ValueError:
                flash("⚠️ Invalid date format. Use YYYY-MM-DD.", "warning")
                return redirect(url_for('add_person'))

        # 📞 Validate phone
        if not phone.isdigit() or len(phone) != 10:
            flash("⚠️ Phone number must be exactly 10 digits.", "warning")
            return redirect(url_for('add_person'))

        # 📧 Validate email format
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            flash("⚠️ Invalid email address format.", "warning")
            return redirect(url_for('add_person'))

        # Database logic
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT IFNULL(MAX(person_id), 0) + 1 FROM Persons")
        new_id = cursor.fetchone()[0]

        try:
            cursor.execute("""
                INSERT INTO Persons (person_id, name, dob, gender, phone, email, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (new_id, name, dob or None, gender, phone, email, address))
            conn.commit()
            flash(f"✅ Person added successfully! Assigned ID: {new_id}", "success")

        except IntegrityError as e:
            if "phone" in str(e):
                flash("⚠️ This phone number is already registered.", "warning")
            elif "email" in str(e):
                flash("⚠️ This email is already registered.", "warning")
            else:
                flash(f"❌ Database Integrity Error: {e}", "danger")
            conn.rollback()

        except Error as e:
            flash(f"❌ Database Error: {e}", "danger")
            conn.rollback()

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('index'))

    return render_template('add_person.html', current_date=date.today().isoformat())


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_person(id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        gender = request.form['gender'].strip()
        phone = normalize_phone(request.form['phone'])
        email = request.form['email'].strip()
        address = request.form['address'].strip()

        # Validations
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash("⚠️ Invalid email format.", "warning")
            return redirect(url_for('update_person', id=id))

        if not phone.isdigit() or len(phone) != 10:
            flash("⚠️ Phone must be 10 digits.", "warning")
            return redirect(url_for('update_person', id=id))

        cursor.execute("""
            UPDATE Persons SET gender=%s, phone=%s, email=%s, address=%s WHERE person_id=%s
        """, (gender, phone, email, address, id))
        conn.commit()
        flash("✅ Record updated!", "info")
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM Persons WHERE person_id=%s", (id,))
    person = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_person.html', person=person)


@app.route('/delete/<int:id>')
def delete_person(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Persons WHERE person_id=%s", (id,))
    conn.commit()

    # Reset auto increment if table is empty
    cursor.execute("SELECT COUNT(*) FROM Persons")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("ALTER TABLE Persons AUTO_INCREMENT = 1")

    conn.commit()
    flash("🗑️ Record deleted!", "warning")
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
