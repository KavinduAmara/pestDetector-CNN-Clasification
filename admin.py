from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    conn = sqlite3.connect('pest.db')  # Replace with your database file
    conn.row_factory = sqlite3.Row
    return conn

@admin_bp.route('/admin')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Example: Fetch all users
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    
    conn.close()
    return render_template('admin/index.html', users=users)

@admin_bp.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password_hash = request.form['password_hash']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, password_hash))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin.index'))
    
    return render_template('admin/add_user.html')

@admin_bp.route('/admin/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password_hash = request.form['password_hash']
        
        cur.execute('UPDATE users SET username = ?, email = ?, password_hash = ? WHERE id = ?',
                    (username, email, password_hash, id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin.index'))
    
    cur.execute('SELECT * FROM users WHERE id = ?', (id,))
    user = cur.fetchone()
    conn.close()
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/admin/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin.index'))

# Route to view all pests
@admin_bp.route('/pests')
def pests():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM pests')
    pests = cur.fetchall()
    conn.close()
    return render_template('admin/pests.html', pests=pests)

# Route to add a new pest
@admin_bp.route('/pests/add', methods=['GET', 'POST'])
def add_pest():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image_url = request.form['image_url']
        control_methods = request.form['control_methods']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO pests (name, description, image_url, control_methods) VALUES (?, ?, ?, ?)',
                    (name, description, image_url, control_methods))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin.pests'))
    
    return render_template('admin/add_pest.html')

# Route to edit a pest
@admin_bp.route('/pests/edit/<int:id>', methods=['GET', 'POST'])
def edit_pest(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image_url = request.form['image_url']
        control_methods = request.form['control_methods']
        
        cur.execute('UPDATE pests SET name = ?, description = ?, image_url = ?, control_methods = ? WHERE id = ?',
                    (name, description, image_url, control_methods, id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin.pests'))
    
    cur.execute('SELECT * FROM pests WHERE id = ?', (id,))
    pest = cur.fetchone()
    conn.close()
    
    return render_template('admin/edit_pest.html', pest=pest)

# Route to delete a pest
@admin_bp.route('/pests/delete/<int:id>', methods=['POST'])
def delete_pest(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM pests WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin.pests'))

@admin_bp.route('/recommendations')
def recommendations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM recommendations')
    recommendations = cur.fetchall()
    conn.close()
    return render_template('admin/recommendations.html', recommendations=recommendations)

# Route to add a new recommendation
@admin_bp.route('/recommendations/add', methods=['GET', 'POST'])
def add_recommendation():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        pest_id = request.form['pest_id']
        recommendation = request.form['recommendation']
        
        cur.execute('INSERT INTO recommendations (pest_id, recommendation) VALUES (?, ?)',
                    (pest_id, recommendation))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin.recommendations'))
    
    # Fetch all pests for selection in the form
    cur.execute('SELECT * FROM pests')
    pests = cur.fetchall()
    conn.close()
    
    return render_template('admin/add_recommendation.html', pests=pests)

# Route to edit a recommendation
@admin_bp.route('/recommendations/edit/<int:id>', methods=['GET', 'POST'])
def edit_recommendation(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        pest_id = request.form['pest_id']
        recommendation = request.form['recommendation']
        
        cur.execute('UPDATE recommendations SET pest_id = ?, recommendation = ? WHERE id = ?',
                    (pest_id, recommendation, id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin.recommendations'))
    
    cur.execute('SELECT * FROM recommendations WHERE id = ?', (id,))
    recommendation = cur.fetchone()
    
    # Fetch all pests for selection in the form
    cur.execute('SELECT * FROM pests')
    pests = cur.fetchall()
    conn.close()
    
    return render_template('admin/edit_recommendation.html', recommendation=recommendation, pests=pests)

# Route to delete a recommendation
@admin_bp.route('/recommendations/delete/<int:id>', methods=['POST'])
def delete_recommendation(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM recommendations WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin.recommendations'))
