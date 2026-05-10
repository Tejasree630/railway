from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, jwt, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'team-task-manager-secret-2024')
CORS(app, supports_credentials=True, origins=["*"])

JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-key-2024')
DB_PATH = os.environ.get('DB_PATH', 'taskmanager.db')

BASE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(BASE, '..', 'frontend')
print("Looking for frontend files in:", FRONTEND)

# ─── DB ─────────────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, description TEXT, admin_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS project_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'member', joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT,
            due_date TEXT, priority TEXT DEFAULT 'medium', status TEXT DEFAULT 'todo',
            assigned_to INTEGER, created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id),
            FOREIGN KEY (created_by) REFERENCES users(id));
    ''')
    conn.commit()
    conn.close()

# ─── AUTH HELPERS ────────────────────────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token: return jsonify({'error': 'Token missing'}), 401
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user_id = data['user_id']
        except jwt.ExpiredSignatureError: return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError: return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def is_admin(pid, uid):
    conn = get_db()
    row = conn.execute('SELECT role FROM project_members WHERE project_id=? AND user_id=?', (pid, uid)).fetchone()
    conn.close()
    return row and row['role'] == 'admin'

# ─── PAGE ROUTES ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(FRONTEND, 'signin.html')

@app.route('/signin')
def page_signin():
    return send_from_directory(FRONTEND, 'signin.html')

@app.route('/signup')
def page_signup():
    return send_from_directory(FRONTEND, 'signup.html')

@app.route('/dashboard')
def page_dashboard():
    return send_from_directory(FRONTEND, 'dashboard.html')

@app.route('/projects')
def page_projects():
    return send_from_directory(FRONTEND, 'projects.html')

@app.route('/project')
def page_project():
    return send_from_directory(FRONTEND, 'project.html')

@app.route('/favicon.ico')
def favicon(): return '', 204

# ─── AUTH API ─────────────────────────────────────────────────────────────────────
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name','').strip()
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    if not name or not email or not password:
        return jsonify({'error': 'All fields required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    conn = get_db()
    if conn.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
        conn.close(); return jsonify({'error': 'Email already registered'}), 409
    hashed = generate_password_hash(password)
    conn.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)', (name, email, hashed))
    conn.commit()
    user_id = conn.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()['id']
    conn.close()
    token = jwt.encode({'user_id': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}, JWT_SECRET, algorithm='HS256')
    return jsonify({'token': token, 'user': {'id': user_id, 'name': name, 'email': email}}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    conn.close()
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
    token = jwt.encode({'user_id': user['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}, JWT_SECRET, algorithm='HS256')
    return jsonify({'token': token, 'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}})

@app.route('/api/auth/me', methods=['GET'])
@token_required
def me():
    conn = get_db()
    user = conn.execute('SELECT id, name, email FROM users WHERE id=?', (request.user_id,)).fetchone()
    conn.close()
    return jsonify(dict(user)) if user else (jsonify({'error': 'Not found'}), 404)

# ─── PROJECTS API ─────────────────────────────────────────────────────────────────
@app.route('/api/projects', methods=['GET'])
@token_required
def get_projects():
    conn = get_db()
    rows = conn.execute('''
        SELECT p.*, u.name as admin_name, pm.role as my_role,
               (SELECT COUNT(*) FROM project_members WHERE project_id=p.id) as member_count,
               (SELECT COUNT(*) FROM tasks WHERE project_id=p.id) as task_count
        FROM projects p
        JOIN project_members pm ON p.id=pm.project_id AND pm.user_id=?
        JOIN users u ON p.admin_id=u.id ORDER BY p.created_at DESC
    ''', (request.user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/projects', methods=['POST'])
@token_required
def create_project():
    data = request.get_json()
    name = data.get('name','').strip()
    if not name: return jsonify({'error': 'Project name required'}), 400
    conn = get_db()
    conn.execute('INSERT INTO projects (name, description, admin_id) VALUES (?,?,?)',
                 (name, data.get('description',''), request.user_id))
    conn.commit()
    pid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.execute('INSERT INTO project_members (project_id, user_id, role) VALUES (?,?,?)', (pid, request.user_id, 'admin'))
    conn.commit()
    proj = conn.execute('SELECT * FROM projects WHERE id=?', (pid,)).fetchone()
    conn.close()
    return jsonify(dict(proj)), 201

@app.route('/api/projects/<int:pid>', methods=['GET'])
@token_required
def get_project(pid):
    conn = get_db()
    member = conn.execute('SELECT role FROM project_members WHERE project_id=? AND user_id=?', (pid, request.user_id)).fetchone()
    if not member: conn.close(); return jsonify({'error': 'Access denied'}), 403
    proj = conn.execute('SELECT p.*, u.name as admin_name, ? as my_role FROM projects p JOIN users u ON p.admin_id=u.id WHERE p.id=?',
                        (member['role'], pid)).fetchone()
    conn.close()
    return jsonify(dict(proj))

@app.route('/api/projects/<int:pid>/members', methods=['GET'])
@token_required
def get_members(pid):
    conn = get_db()
    if not conn.execute('SELECT id FROM project_members WHERE project_id=? AND user_id=?', (pid, request.user_id)).fetchone():
        conn.close(); return jsonify({'error': 'Access denied'}), 403
    members = conn.execute('''SELECT u.id, u.name, u.email, pm.role, pm.joined_at
        FROM project_members pm JOIN users u ON pm.user_id=u.id
        WHERE pm.project_id=? ORDER BY pm.role DESC, u.name''', (pid,)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in members])

@app.route('/api/projects/<int:pid>/members', methods=['POST'])
@token_required
def add_member(pid):
    if not is_admin(pid, request.user_id): return jsonify({'error': 'Admin access required'}), 403
    email = request.get_json().get('email','').strip().lower()
    conn = get_db()
    user = conn.execute('SELECT id, name, email FROM users WHERE email=?', (email,)).fetchone()
    if not user: conn.close(); return jsonify({'error': 'User not found'}), 404
    if conn.execute('SELECT id FROM project_members WHERE project_id=? AND user_id=?', (pid, user['id'])).fetchone():
        conn.close(); return jsonify({'error': 'User already in project'}), 409
    conn.execute('INSERT INTO project_members (project_id, user_id, role) VALUES (?,?,?)', (pid, user['id'], 'member'))
    conn.commit(); conn.close()
    return jsonify({'message': f'{user["name"]} added', 'user': dict(user)}), 201

@app.route('/api/projects/<int:pid>/members/<int:uid>', methods=['DELETE'])
@token_required
def remove_member(pid, uid):
    if not is_admin(pid, request.user_id): return jsonify({'error': 'Admin access required'}), 403
    conn = get_db()
    proj = conn.execute('SELECT admin_id FROM projects WHERE id=?', (pid,)).fetchone()
    if proj and proj['admin_id'] == uid: conn.close(); return jsonify({'error': 'Cannot remove admin'}), 400
    conn.execute('DELETE FROM project_members WHERE project_id=? AND user_id=?', (pid, uid))
    conn.commit(); conn.close()
    return jsonify({'message': 'Member removed'})

@app.route('/api/projects/<int:pid>/users', methods=['GET'])
@token_required
def project_users(pid):
    conn = get_db()
    if not conn.execute('SELECT id FROM project_members WHERE project_id=? AND user_id=?', (pid, request.user_id)).fetchone():
        conn.close(); return jsonify({'error': 'Access denied'}), 403
    users = conn.execute('SELECT u.id, u.name, u.email, pm.role FROM users u JOIN project_members pm ON u.id=pm.user_id WHERE pm.project_id=?', (pid,)).fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

# ─── TASKS API ────────────────────────────────────────────────────────────────────
@app.route('/api/projects/<int:pid>/tasks', methods=['GET'])
@token_required
def get_tasks(pid):
    conn = get_db()
    if not conn.execute('SELECT id FROM project_members WHERE project_id=? AND user_id=?', (pid, request.user_id)).fetchone():
        conn.close(); return jsonify({'error': 'Access denied'}), 403
    tasks = conn.execute('''SELECT t.*, u.name as assigned_name, cu.name as created_by_name
        FROM tasks t LEFT JOIN users u ON t.assigned_to=u.id LEFT JOIN users cu ON t.created_by=cu.id
        WHERE t.project_id=? ORDER BY t.created_at DESC''', (pid,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/projects/<int:pid>/tasks', methods=['POST'])
@token_required
def create_task(pid):
    if not is_admin(pid, request.user_id): return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json()
    title = data.get('title','').strip()
    if not title: return jsonify({'error': 'Task title required'}), 400
    conn = get_db()
    conn.execute('INSERT INTO tasks (project_id,title,description,due_date,priority,status,assigned_to,created_by) VALUES (?,?,?,?,?,?,?,?)',
                 (pid, title, data.get('description'), data.get('due_date'), data.get('priority','medium'),
                  data.get('status','todo'), data.get('assigned_to'), request.user_id))
    conn.commit()
    tid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    task = conn.execute('SELECT t.*, u.name as assigned_name, cu.name as created_by_name FROM tasks t LEFT JOIN users u ON t.assigned_to=u.id LEFT JOIN users cu ON t.created_by=cu.id WHERE t.id=?', (tid,)).fetchone()
    conn.close()
    return jsonify(dict(task)), 201

@app.route('/api/tasks/<int:tid>', methods=['PUT'])
@token_required
def update_task(tid):
    conn = get_db()
    task = conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
    if not task: conn.close(); return jsonify({'error': 'Task not found'}), 404
    member = conn.execute('SELECT role FROM project_members WHERE project_id=? AND user_id=?', (task['project_id'], request.user_id)).fetchone()
    if not member: conn.close(); return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    if member['role'] == 'member':
        if task['assigned_to'] != request.user_id: conn.close(); return jsonify({'error': 'Can only update your own tasks'}), 403
        data = {k: v for k, v in data.items() if k == 'status'}
    for field in ['title','description','due_date','priority','status','assigned_to']:
        if field in data:
            conn.execute(f'UPDATE tasks SET {field}=? WHERE id=?', (data[field], tid))
    conn.commit()
    task = conn.execute('SELECT t.*, u.name as assigned_name, cu.name as created_by_name FROM tasks t LEFT JOIN users u ON t.assigned_to=u.id LEFT JOIN users cu ON t.created_by=cu.id WHERE t.id=?', (tid,)).fetchone()
    conn.close()
    return jsonify(dict(task))

@app.route('/api/tasks/<int:tid>', methods=['DELETE'])
@token_required
def delete_task(tid):
    conn = get_db()
    task = conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
    if not task: conn.close(); return jsonify({'error': 'Task not found'}), 404
    if not is_admin(task['project_id'], request.user_id): conn.close(); return jsonify({'error': 'Admin access required'}), 403
    conn.execute('DELETE FROM tasks WHERE id=?', (tid,))
    conn.commit(); conn.close()
    return jsonify({'message': 'Task deleted'})

# ─── DASHBOARD API ────────────────────────────────────────────────────────────────
@app.route('/api/dashboard', methods=['GET'])
@token_required
def dashboard():
    conn = get_db()
    uid = request.user_id
    today = datetime.date.today().isoformat()
    stats = {
        'total_projects': conn.execute('SELECT COUNT(*) FROM project_members WHERE user_id=?', (uid,)).fetchone()[0],
        'total_tasks': conn.execute('SELECT COUNT(*) FROM tasks t JOIN project_members pm ON t.project_id=pm.project_id AND pm.user_id=?', (uid,)).fetchone()[0],
        'todo_tasks': conn.execute("SELECT COUNT(*) FROM tasks t JOIN project_members pm ON t.project_id=pm.project_id AND pm.user_id=? WHERE t.status='todo'", (uid,)).fetchone()[0],
        'inprogress_tasks': conn.execute("SELECT COUNT(*) FROM tasks t JOIN project_members pm ON t.project_id=pm.project_id AND pm.user_id=? WHERE t.status='inprogress'", (uid,)).fetchone()[0],
        'done_tasks': conn.execute("SELECT COUNT(*) FROM tasks t JOIN project_members pm ON t.project_id=pm.project_id AND pm.user_id=? WHERE t.status='done'", (uid,)).fetchone()[0],
        'overdue_tasks': conn.execute("SELECT COUNT(*) FROM tasks t JOIN project_members pm ON t.project_id=pm.project_id AND pm.user_id=? WHERE t.status!='done' AND t.due_date IS NOT NULL AND t.due_date < ?", (uid, today)).fetchone()[0],
        'my_tasks': conn.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND status!='done'", (uid,)).fetchone()[0],
    }
    recent = conn.execute('''SELECT t.*, u.name as assigned_name, p.name as project_name
        FROM tasks t JOIN project_members pm ON t.project_id=pm.project_id AND pm.user_id=?
        LEFT JOIN users u ON t.assigned_to=u.id JOIN projects p ON t.project_id=p.id
        ORDER BY t.created_at DESC LIMIT 5''', (uid,)).fetchall()
    conn.close()
    return jsonify({'stats': stats, 'recent_tasks': [dict(t) for t in recent]})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)