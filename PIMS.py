import mysql.connector
from mysql.connector import Error
from tabulate import tabulate
import re

def get_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="1234",  
            database="personal_info_db"
        )
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return None

def validate_date(date_str):
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    return bool(re.match(pattern, date_str))

def validate_phone(phone):
    return bool(re.match(r"^\d{10}$", phone))  

def validate_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


def add_person():
    name = input("Enter full name: ").strip()
    dob = input("Enter date of birth (YYYY-MM-DD): ").strip()
    gender = input("Enter gender (Male/Female/Other): ").strip()
    phone = input("Enter phone number: ").strip()
    email = input("Enter email: ").strip()
    address = input("Enter address: ").strip()

    # Validation
    if not name:
        print("❌ Name cannot be empty!")
        return
    if dob and not validate_date(dob):
        print("❌ Invalid date format. Use YYYY-MM-DD.")
        return
    if phone and not validate_phone(phone):
        print("❌ Phone must be 10 digits.")
        return
    if email and not validate_email(email):
        print("❌ Invalid email format.")
        return

    conn = get_connection()
    if conn is None: return
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO Persons (name, dob, gender, phone, email, address) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, dob or None, gender or None, phone or None, email or None, address or None))
        conn.commit()
        print("✅ Personal information added successfully!")
    except Error as e:
        print(f"❌ Error inserting record: {e}")
    finally:
        cursor.close()
        conn.close()

def view_persons():
    conn = get_connection()
    if conn is None: return
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Persons;")
    rows = cursor.fetchall()

    if not rows:
        print("\n📌 No records found in database.")
    else:
        headers = [desc[0] for desc in cursor.description]
        print("\n📌 Stored Personal Information:")
        print(tabulate(rows, headers, tablefmt="grid"))

    cursor.close()
    conn.close()

def update_person():
    try:
        person_id = int(input("Enter Person ID to update: "))
    except ValueError:
        print("❌ Invalid ID. Must be a number.")
        return

    print("Leave blank if you don’t want to update a field.")
    new_phone = input("Enter new phone number: ").strip()
    new_email = input("Enter new email: ").strip()
    new_address = input("Enter new address: ").strip()

    # Validate fields
    if new_phone and not validate_phone(new_phone):
        print("❌ Phone must be 10 digits.")
        return
    if new_email and not validate_email(new_email):
        print("❌ Invalid email format.")
        return

    conn = get_connection()
    if conn is None: return
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Persons WHERE person_id=%s", (person_id,))
    if cursor.fetchone() is None:
        print("❌ Person ID not found.")
        cursor.close()
        conn.close()
        return

    try:
        if new_phone:
            cursor.execute("UPDATE Persons SET phone=%s WHERE person_id=%s", (new_phone, person_id))
        if new_email:
            cursor.execute("UPDATE Persons SET email=%s WHERE person_id=%s", (new_email, person_id))
        if new_address:
            cursor.execute("UPDATE Persons SET address=%s WHERE person_id=%s", (new_address, person_id))

        conn.commit()
        print("✅ Information updated successfully!")
    except Error as e:
        print(f"❌ Error updating record: {e}")
    finally:
        cursor.close()
        conn.close()

def delete_person():
    try:
        person_id = int(input("Enter Person ID to delete: "))
    except ValueError:
        print("❌ Invalid ID. Must be a number.")
        return

    conn = get_connection()
    if conn is None: return
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Persons WHERE person_id=%s", (person_id,))
    if cursor.fetchone() is None:
        print("❌ Person ID not found.")
        cursor.close()
        conn.close()
        return

    try:
        cursor.execute("DELETE FROM Persons WHERE person_id=%s", (person_id,))
        conn.commit()
        print("🗑️ Record deleted successfully!")
    except Error as e:
        print(f"❌ Error deleting record: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    try:
        while True:
            print("\n===== 📋 Personal Information Management System =====")
            print("1. Add Person")
            print("2. View All Persons")
            print("3. Update Person Info")
            print("4. Delete Person")
            print("5. Exit\n")

            choice = input("Enter choice: ")

            if choice == "1":
                add_person()
            elif choice == "2":
                view_persons()
            elif choice == "3":
                update_person()
            elif choice == "4":
                delete_person()
            elif choice == "5":
                print("👋 Exiting... Bye!")
                break
            else:
                print("❌ Invalid choice, try again.")
    except KeyboardInterrupt:
        print("\n👋 Program interrupted. Exiting safely...")

if __name__ == "__main__":
    main()
