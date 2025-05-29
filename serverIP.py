from flask import Flask, request, jsonify, render_template, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Secret key for session management

# Store the server data (list of servers)
servers_data = []

# Admin credentials (for simplicity, hardcoded)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

@app.route('/')
def index():
    # Check if user is logged in as admin
    is_admin = 'admin' in session
    return render_template('index.html', is_admin=is_admin)  # Pass admin status to the template

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = username  # Set session for admin
            return redirect(url_for('index'))  # Redirect to the main page
        return 'Invalid credentials! Please try again.'
    return render_template('login.html')  # Serve login page

@app.route('/logout')
def logout():
    session.pop('admin', None)  # Remove admin session
    return redirect(url_for('index'))  # Redirect to main page

@app.route('/add', methods=['POST'])
def add_server():
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 403  # Only allow access for admin
    # Get the data from the request
    data = request.get_json()
    ip = data.get('ip')
    name = data.get('name')
    if not ip or not name:
        return jsonify({"error": "IP and name are required"}), 400
    # Add the server data to the list
    servers_data.append({
        'id': len(servers_data) + 1,  # Assign a unique ID
        'ip': ip,
        'name': name
    })
    return jsonify({"message": "Server added successfully"}), 200

@app.route('/list', methods=['GET'])
def list_servers():
    return jsonify(servers_data)  # Returns the server data as a JSON response

# NEW ROUTE: Edit server
@app.route('/update/<int:id>', methods=['PUT'])
def update_server(id):
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 403  # Only allow access for admin
    data = request.get_json()
    ip = data.get('ip')
    name = data.get('name')
    if not ip or not name:
        return jsonify({"error": "IP and name are required"}), 400
    # Find the server by ID and update it
    for server in servers_data:
        if server['id'] == id:
            server['ip'] = ip
            server['name'] = name
            return jsonify({"message": "Server updated successfully"}), 200
    return jsonify({"error": "Server not found"}), 404

# NEW ROUTE: Delete server
@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_server(id):
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 403  # Only allow access for admin
    # Find the server by ID and remove it
    global servers_data
    servers_data = [server for server in servers_data if server['id'] != id]
    return jsonify({"message": "Server deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)