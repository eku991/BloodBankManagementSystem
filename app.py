from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
from dsa import BloodQueue, BloodGroupHashMap, merge_sort_by_expiry

app = Flask(__name__)
app.secret_key = 'blood-bank-secret-key'
DATABASE = 'blood_bank.db'


# ==================== DATABASE SETUP ====================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS blood_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units INTEGER NOT NULL DEFAULT 1,
            donation_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'available'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transfusion_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units_used INTEGER NOT NULL,
            blood_unit_id INTEGER,
            transfusion_date TEXT NOT NULL,
            FOREIGN KEY (blood_unit_id) REFERENCES blood_units(id)
        )
    ''')
    conn.commit()
    conn.close()


# ==================== DSA HELPER FUNCTIONS ====================
def build_blood_queue(blood_group):
    """
    QUEUE (FIFO): Build a queue of available blood units for a given blood group.
    Oldest donations are at the front so they get used first.
    """
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM blood_units WHERE blood_group = ? AND status = ? ORDER BY donation_date ASC',
        (blood_group, 'available')
    ).fetchall()
    conn.close()

    queue = BloodQueue()
    for row in rows:
        queue.enqueue(dict(row))
    return queue


def build_blood_group_hashmap():
    """
    HASH MAP: Index all available blood units by blood group for fast lookup.
    """
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM blood_units WHERE status = ?', ('available',)
    ).fetchall()
    conn.close()

    hashmap = BloodGroupHashMap()
    for row in rows:
        unit = dict(row)
        hashmap.put(unit['blood_group'], unit)
    return hashmap


def get_sorted_by_expiry():
    """
    SORTING: Get all available blood units sorted by expiry date using merge sort.
    """
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM blood_units WHERE status = ?', ('available',)
    ).fetchall()
    conn.close()

    blood_units = [dict(row) for row in rows]
    sorted_units = merge_sort_by_expiry(blood_units)
    return sorted_units


# ==================== ROUTES ====================
@app.route('/')
def index():
    hashmap = build_blood_group_hashmap()
    group_counts = hashmap.get_all_groups()

    all_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    inventory = {g: group_counts.get(g, 0) for g in all_groups}
    total = hashmap.total_units()

    conn = get_db()
    expired = conn.execute(
        "SELECT COUNT(*) FROM blood_units WHERE status = 'available' AND expiry_date < ?",
        (datetime.now().strftime('%Y-%m-%d'),)
    ).fetchone()[0]
    recent_transfusions = conn.execute(
        'SELECT * FROM transfusion_log ORDER BY transfusion_date DESC LIMIT 5'
    ).fetchall()
    conn.close()

    return render_template('index.html',
                           inventory=inventory,
                           total=total,
                           expired_count=expired,
                           recent_transfusions=recent_transfusions)


@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        donor_name = request.form['donor_name']
        blood_group = request.form['blood_group']
        units = int(request.form['units'])
        donation_date = request.form['donation_date']
        expiry_date = (datetime.strptime(donation_date, '%Y-%m-%d') + timedelta(days=42)).strftime('%Y-%m-%d')

        conn = get_db()
        for _ in range(units):
            conn.execute(
                'INSERT INTO blood_units (donor_name, blood_group, units, donation_date, expiry_date) VALUES (?, ?, 1, ?, ?)',
                (donor_name, blood_group, donation_date, expiry_date)
            )
        conn.commit()
        conn.close()

        flash(f'Successfully added {units} unit(s) of {blood_group} blood from {donor_name}!', 'success')
        return redirect(url_for('donate'))

    return render_template('donate.html')


@app.route('/request_blood', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        blood_group = request.form['blood_group']
        units_needed = int(request.form['units'])

        queue = build_blood_queue(blood_group)

        if queue.size() < units_needed:
            flash(f'Not enough {blood_group} blood available! Only {queue.size()} unit(s) in stock.', 'danger')
            return redirect(url_for('request_blood'))

        conn = get_db()
        for _ in range(units_needed):
            unit = queue.dequeue()
            conn.execute(
                'UPDATE blood_units SET status = ? WHERE id = ?',
                ('used', unit['id'])
            )
            conn.execute(
                'INSERT INTO transfusion_log (patient_name, blood_group, units_used, blood_unit_id, transfusion_date) VALUES (?, ?, 1, ?, ?)',
                (patient_name, blood_group, unit['id'], datetime.now().strftime('%Y-%m-%d %H:%M'))
            )
        conn.commit()
        conn.close()

        flash(f'Successfully allocated {units_needed} unit(s) of {blood_group} to {patient_name} (FIFO order).', 'success')
        return redirect(url_for('request_blood'))

    hashmap = build_blood_group_hashmap()
    group_counts = hashmap.get_all_groups()
    return render_template('request_blood.html', group_counts=group_counts)


@app.route('/inventory')
def inventory():
    sort_by = request.args.get('sort', 'expiry')

    if sort_by == 'expiry':
        blood_units = get_sorted_by_expiry()
    else:
        conn = get_db()
        rows = conn.execute(
            'SELECT * FROM blood_units WHERE status = ? ORDER BY blood_group',
            ('available',)
        ).fetchall()
        conn.close()
        blood_units = [dict(row) for row in rows]

    today = datetime.now().strftime('%Y-%m-%d')
    for unit in blood_units:
        unit['is_expired'] = unit['expiry_date'] < today
        days_left = (datetime.strptime(unit['expiry_date'], '%Y-%m-%d') - datetime.now()).days
        unit['days_left'] = max(days_left, 0)

    return render_template('inventory.html', blood_units=blood_units, sort_by=sort_by)


@app.route('/emergency', methods=['GET', 'POST'])
def emergency():
    compatible = {
        'A+': ['A+', 'A-', 'O+', 'O-'],
        'A-': ['A-', 'O-'],
        'B+': ['B+', 'B-', 'O+', 'O-'],
        'B-': ['B-', 'O-'],
        'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        'AB-': ['A-', 'B-', 'AB-', 'O-'],
        'O+': ['O+', 'O-'],
        'O-': ['O-'],
    }

    results = None
    searched_group = None

    if request.method == 'POST':
        searched_group = request.form['blood_group']
        hashmap = build_blood_group_hashmap()
        compatible_groups = compatible.get(searched_group, [])

        results = []
        for group in compatible_groups:
            units = hashmap.get(group)
            sorted_units = merge_sort_by_expiry(units)
            results.append({
                'blood_group': group,
                'count': len(units),
                'units': sorted_units[:3],
                'is_exact': group == searched_group
            })

    return render_template('emergency.html',
                           results=results,
                           searched_group=searched_group)


@app.route('/history')
def history():
    conn = get_db()
    logs = conn.execute(
        'SELECT * FROM transfusion_log ORDER BY transfusion_date DESC'
    ).fetchall()
    conn.close()
    return render_template('history.html', logs=logs)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
