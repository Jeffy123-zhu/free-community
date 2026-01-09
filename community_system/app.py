"""Flask main application"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import get_db, init_db, calculate_quarter
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'community_system_secret_key'

@app.route('/')
def index():
    """Dashboard"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM event_profiles')
    total_events = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(volunteer_hours), 0) FROM contributions')
    total_hours = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(cash_donation), 0) FROM contributions')
    total_cash = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(material_value), 0) FROM contributions')
    total_material = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT ep.*, et.name as event_type_name 
        FROM event_profiles ep 
        LEFT JOIN event_types et ON ep.event_type_id = et.id 
        ORDER BY ep.event_date DESC LIMIT 5
    ''')
    recent_events = cursor.fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         total_events=total_events,
                         total_hours=total_hours,
                         total_cash=total_cash,
                         total_material=total_material,
                         recent_events=recent_events)

@app.route('/events')
def event_list():
    """Event list"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ep.*, et.name as event_type_name, o.name as org_name
        FROM event_profiles ep 
        LEFT JOIN event_types et ON ep.event_type_id = et.id 
        LEFT JOIN organizations o ON ep.organization_id = o.id
        ORDER BY ep.event_date DESC
    ''')
    events = cursor.fetchall()
    conn.close()
    return render_template('event_list.html', events=events)

@app.route('/events/add', methods=['GET', 'POST'])
def add_event():
    """Add event"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        event_date = request.form['event_date']
        quarter = calculate_quarter(event_date)
        
        cursor.execute('''
            INSERT INTO event_profiles 
            (event_name, event_date, event_type_id, location, description,
             organization_id, coordinator_name, coordinator_phone, coordinator_email,
             expected_participants, actual_participants, income, expense, notes, status, quarter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['event_name'],
            event_date,
            request.form.get('event_type_id') or None,
            request.form.get('location'),
            request.form.get('description'),
            request.form.get('organization_id') or None,
            request.form.get('coordinator_name'),
            request.form.get('coordinator_phone'),
            request.form.get('coordinator_email'),
            request.form.get('expected_participants') or 0,
            request.form.get('actual_participants') or 0,
            request.form.get('income') or 0,
            request.form.get('expense') or 0,
            request.form.get('notes'),
            request.form.get('status', 'In Progress'),
            quarter
        ))
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        flash('Event added successfully!', 'success')
        return redirect(url_for('edit_event', event_id=event_id))
    
    cursor.execute('SELECT * FROM event_types')
    event_types = cursor.fetchall()
    cursor.execute('SELECT * FROM organizations ORDER BY name')
    organizations = cursor.fetchall()
    conn.close()
    
    return render_template('add_event.html', event_types=event_types, organizations=organizations)


@app.route('/events/<int:event_id>')
def view_event(event_id):
    """View event details"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ep.*, et.name as event_type_name, o.name as org_name
        FROM event_profiles ep 
        LEFT JOIN event_types et ON ep.event_type_id = et.id 
        LEFT JOIN organizations o ON ep.organization_id = o.id
        WHERE ep.id = ?
    ''', (event_id,))
    event = cursor.fetchone()
    
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('event_list'))
    
    cursor.execute('SELECT * FROM contributions WHERE event_id = ?', (event_id,))
    contributions = cursor.fetchall()
    
    cursor.execute('''
        SELECT COALESCE(SUM(volunteer_hours), 0) as total_hours,
               COALESCE(SUM(cash_donation), 0) as total_cash,
               COALESCE(SUM(material_value), 0) as total_material
        FROM contributions WHERE event_id = ?
    ''', (event_id,))
    summary = cursor.fetchone()
    
    conn.close()
    return render_template('view_event.html', event=event, contributions=contributions, summary=summary)

@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    """Edit event"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        event_date = request.form['event_date']
        quarter = calculate_quarter(event_date)
        
        cursor.execute('''
            UPDATE event_profiles SET
            event_name=?, event_date=?, event_type_id=?, location=?, description=?,
            organization_id=?, coordinator_name=?, coordinator_phone=?, coordinator_email=?,
            expected_participants=?, actual_participants=?, income=?, expense=?, notes=?, status=?, quarter=?
            WHERE id=?
        ''', (
            request.form['event_name'],
            event_date,
            request.form.get('event_type_id') or None,
            request.form.get('location'),
            request.form.get('description'),
            request.form.get('organization_id') or None,
            request.form.get('coordinator_name'),
            request.form.get('coordinator_phone'),
            request.form.get('coordinator_email'),
            request.form.get('expected_participants') or 0,
            request.form.get('actual_participants') or 0,
            request.form.get('income') or 0,
            request.form.get('expense') or 0,
            request.form.get('notes'),
            request.form.get('status', 'In Progress'),
            quarter,
            event_id
        ))
        conn.commit()
        flash('Event updated successfully!', 'success')
    
    cursor.execute('SELECT * FROM event_profiles WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    cursor.execute('SELECT * FROM event_types')
    event_types = cursor.fetchall()
    cursor.execute('SELECT * FROM organizations ORDER BY name')
    organizations = cursor.fetchall()
    cursor.execute('SELECT * FROM contributions WHERE event_id = ?', (event_id,))
    contributions = cursor.fetchall()
    cursor.execute('SELECT * FROM volunteers ORDER BY name')
    volunteers = cursor.fetchall()
    
    conn.close()
    return render_template('edit_event.html', event=event, event_types=event_types, 
                         organizations=organizations, contributions=contributions, volunteers=volunteers)

@app.route('/events/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Delete event"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contributions WHERE event_id = ?', (event_id,))
    cursor.execute('DELETE FROM event_profiles WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    flash('Event deleted', 'success')
    return redirect(url_for('event_list'))

@app.route('/events/<int:event_id>/contributions/add', methods=['POST'])
def add_contribution(event_id):
    """Add contribution record"""
    conn = get_db()
    cursor = conn.cursor()
    
    volunteer_id = request.form.get('volunteer_id') or None
    volunteer_name = request.form['volunteer_name']
    volunteer_contact = request.form.get('volunteer_contact')
    
    # If volunteer selected, update their info
    if volunteer_id:
        cursor.execute('SELECT name FROM volunteers WHERE id = ?', (volunteer_id,))
        vol = cursor.fetchone()
        if vol:
            volunteer_name = vol['name']
    
    cursor.execute('''
        INSERT INTO contributions (event_id, volunteer_id, volunteer_name, volunteer_contact, 
                                   volunteer_hours, cash_donation, material_description, material_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        event_id,
        volunteer_id,
        volunteer_name,
        volunteer_contact,
        request.form.get('volunteer_hours') or 0,
        request.form.get('cash_donation') or 0,
        request.form.get('material_description'),
        request.form.get('material_value') or 0
    ))
    conn.commit()
    conn.close()
    flash('Contribution added successfully!', 'success')
    return redirect(url_for('edit_event', event_id=event_id))

@app.route('/contributions/<int:contribution_id>/delete', methods=['POST'])
def delete_contribution(contribution_id):
    """Delete contribution"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT event_id FROM contributions WHERE id = ?', (contribution_id,))
    result = cursor.fetchone()
    event_id = result['event_id'] if result else None
    cursor.execute('DELETE FROM contributions WHERE id = ?', (contribution_id,))
    conn.commit()
    conn.close()
    flash('Contribution deleted', 'success')
    return redirect(url_for('edit_event', event_id=event_id))


# ========== Volunteers (Individual Accounts) ==========
@app.route('/volunteers')
def volunteer_list():
    """Volunteer list"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.*, 
               COALESCE(SUM(c.volunteer_hours), 0) as total_hours,
               COALESCE(SUM(c.cash_donation), 0) as total_cash,
               COALESCE(SUM(c.material_value), 0) as total_material,
               COUNT(c.id) as contribution_count
        FROM volunteers v
        LEFT JOIN contributions c ON v.id = c.volunteer_id
        GROUP BY v.id
        ORDER BY v.name
    ''')
    volunteers = cursor.fetchall()
    conn.close()
    return render_template('volunteers.html', volunteers=volunteers)

@app.route('/volunteers/add', methods=['POST'])
def add_volunteer():
    """Add volunteer"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO volunteers (name, phone, email, address, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        request.form['name'],
        request.form.get('phone'),
        request.form.get('email'),
        request.form.get('address'),
        request.form.get('notes')
    ))
    conn.commit()
    conn.close()
    flash('Volunteer added successfully!', 'success')
    return redirect(url_for('volunteer_list'))

@app.route('/volunteers/<int:vol_id>')
def view_volunteer(vol_id):
    """View volunteer details and contribution history"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM volunteers WHERE id = ?', (vol_id,))
    volunteer = cursor.fetchone()
    
    if not volunteer:
        flash('Volunteer not found', 'error')
        return redirect(url_for('volunteer_list'))
    
    cursor.execute('''
        SELECT c.*, ep.event_name, ep.event_date
        FROM contributions c
        JOIN event_profiles ep ON c.event_id = ep.id
        WHERE c.volunteer_id = ?
        ORDER BY ep.event_date DESC
    ''', (vol_id,))
    contributions = cursor.fetchall()
    
    cursor.execute('''
        SELECT COALESCE(SUM(volunteer_hours), 0) as total_hours,
               COALESCE(SUM(cash_donation), 0) as total_cash,
               COALESCE(SUM(material_value), 0) as total_material
        FROM contributions WHERE volunteer_id = ?
    ''', (vol_id,))
    totals = cursor.fetchone()
    
    conn.close()
    return render_template('view_volunteer.html', volunteer=volunteer, contributions=contributions, totals=totals)

@app.route('/volunteers/<int:vol_id>/delete', methods=['POST'])
def delete_volunteer(vol_id):
    """Delete volunteer"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE contributions SET volunteer_id = NULL WHERE volunteer_id = ?', (vol_id,))
    cursor.execute('DELETE FROM volunteers WHERE id = ?', (vol_id,))
    conn.commit()
    conn.close()
    flash('Volunteer deleted', 'success')
    return redirect(url_for('volunteer_list'))

# ========== Organizations ==========
@app.route('/organizations')
def organization_list():
    """Organization list"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM organizations ORDER BY name')
    organizations = cursor.fetchall()
    conn.close()
    return render_template('organizations.html', organizations=organizations)

@app.route('/organizations/add', methods=['POST'])
def add_organization():
    """Add organization"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO organizations (name, type, size, contact_name, contact_phone, contact_email)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        request.form['name'],
        request.form.get('type'),
        request.form.get('size'),
        request.form.get('contact_name'),
        request.form.get('contact_phone'),
        request.form.get('contact_email')
    ))
    conn.commit()
    conn.close()
    flash('Organization added successfully!', 'success')
    return redirect(url_for('organization_list'))

@app.route('/organizations/<int:org_id>/delete', methods=['POST'])
def delete_organization(org_id):
    """Delete organization"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM organizations WHERE id = ?', (org_id,))
    conn.commit()
    conn.close()
    flash('Organization deleted', 'success')
    return redirect(url_for('organization_list'))

# ========== Event Types ==========
@app.route('/event-types')
def event_type_list():
    """Event type list"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM event_types ORDER BY name')
    event_types = cursor.fetchall()
    conn.close()
    return render_template('event_types.html', event_types=event_types)

@app.route('/event-types/add', methods=['POST'])
def add_event_type():
    """Add event type"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO event_types (name, description) VALUES (?, ?)',
                      (request.form['name'], request.form.get('description')))
        conn.commit()
        flash('Event type added successfully!', 'success')
    except:
        flash('This type already exists', 'error')
    conn.close()
    return redirect(url_for('event_type_list'))

@app.route('/event-types/<int:type_id>/delete', methods=['POST'])
def delete_event_type(type_id):
    """Delete event type"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM event_types WHERE id = ?', (type_id,))
    conn.commit()
    conn.close()
    flash('Event type deleted', 'success')
    return redirect(url_for('event_type_list'))


# ========== Reports ==========
@app.route('/reports')
def reports():
    """Reports page"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT quarter FROM event_profiles ORDER BY quarter DESC')
    quarters = [row['quarter'] for row in cursor.fetchall()]
    conn.close()
    return render_template('reports.html', quarters=quarters)

@app.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate quarterly report"""
    quarter = request.form['quarter']
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ep.*, et.name as event_type_name
        FROM event_profiles ep
        LEFT JOIN event_types et ON ep.event_type_id = et.id
        WHERE ep.quarter = ?
        ORDER BY ep.event_date
    ''', (quarter,))
    events = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) FROM event_profiles WHERE quarter = ?', (quarter,))
    total_events = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COALESCE(SUM(c.volunteer_hours), 0) as total_hours,
               COALESCE(SUM(c.cash_donation), 0) as total_cash,
               COALESCE(SUM(c.material_value), 0) as total_material
        FROM contributions c
        JOIN event_profiles ep ON c.event_id = ep.id
        WHERE ep.quarter = ?
    ''', (quarter,))
    totals = cursor.fetchone()
    
    cursor.execute('''
        SELECT COALESCE(SUM(actual_participants), 0) FROM event_profiles WHERE quarter = ?
    ''', (quarter,))
    total_participants = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT et.name, COUNT(*) as count,
               COALESCE(SUM(ep.actual_participants), 0) as participants
        FROM event_profiles ep
        LEFT JOIN event_types et ON ep.event_type_id = et.id
        WHERE ep.quarter = ?
        GROUP BY et.name
    ''', (quarter,))
    by_type = cursor.fetchall()
    
    conn.close()
    
    return render_template('report_result.html', 
                         quarter=quarter, events=events,
                         total_events=total_events,
                         total_hours=totals['total_hours'],
                         total_cash=totals['total_cash'],
                         total_material=totals['total_material'],
                         total_participants=total_participants,
                         by_type=by_type)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
