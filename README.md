================================================================
        TASKFLOW TEAM TASK MANAGER
        Full-Stack Web Application
================================================================

PROJECT OVERVIEW
----------------
TaskFlow is a full-stack Team Task Management Web Application
similar to Trello and Asana. Multiple users can create projects,
assign tasks, and track progress with role-based access control.

DEVELOPER: TUMMURU TEJASREE
SUBMISSION DATE: 10/05/2026
LIVE URL: [Your Railway URL here]
GITHUB: [Your GitHub URL here]


===============================================================
TECH STACK
===============================================================

FRONTEND:
  - HTML5
  - CSS3
  - Vanilla JavaScript

BACKEND:
  - Python 3
  - Flask (Web Framework)
  - Flask-CORS (Cross Origin Resource Sharing)
  - Werkzeug (Password Hashing)
  - PyJWT (JSON Web Token Authentication)

DATABASE:
  - SQLite (Local Development)

DEPLOYMENT:
  - Railway (Live Hosting)

AUTHENTICATION:
  - JWT Token Based Authentication


===================================================
FEATURES
===================================================

1. USER AUTHENTICATION
   - Signup with Name, Email, Password
   - Secure Login with JWT Token
   - Token stored in localStorage
   - Auto redirect if not logged in

2. PROJECT MANAGEMENT
   - Create Projects
   - Creator automatically becomes Admin
   - Admin can add members by email
   - Admin can remove members
   - Members can view assigned projects

3. TASK MANAGEMENT
   - Create tasks with Title, Description
   - Set Due Date and Priority (High/Medium/Low)
   - Assign tasks to team members
   - Update status: To Do, In Progress, Done
   - Delete tasks (Admin only)

5. DASHBOARD
   - Total Projects count
   - Tasks by Status (To Do, In Progress, Done)
   - Overdue Tasks count
   - Tasks assigned to me
   - Recent Tasks list

6. ROLE BASED ACCESS CONTROL
   Admin:
     - Create, Edit, Delete tasks
     - Add and Remove members
     - Manage entire project

   Member:
     - View assigned tasks only
     - Update status of own tasks only
     - Cannot create or delete tasks


================================================================
PROJECT STRUCTURE
================================================================

taskflow/
  |
  |-- backend/
  |     |-- app.py              (Flask API - all routes)
  |     |-- requirements.txt    (Python packages)
  |     |-- taskmanager.db      (SQLite database - auto created)
  |
  |-- frontend/
  |     |-- signin.html         (Login page)
  |     |-- signup.html         (Register page)
  |     |-- dashboard.html      (Dashboard with stats)
  |     |-- projects.html       (Projects list page)
  |     |-- project.html        (Project detail + Kanban)
  |
  |-- Procfile                  (Railway deployment)
  |-- README.txt                (This file)


================================================================
DATABASE DESIGN
================================================================

TABLE: users
  - id (Primary Key)
  - name
  - email (Unique)
  - password (Hashed)
  - created_at

TABLE: projects
  - id (Primary Key)
  - name
  - description
  - admin_id (Foreign Key â†’ users)
  - created_at

TABLE: project_members
  - id (Primary Key)
  - project_id (Foreign Key â†’ projects)
  - user_id (Foreign Key â†’ users)
  - role (admin / member)
  - joined_at

TABLE: tasks
  - id (Primary Key)
  - project_id (Foreign Key â†’ projects)
  - title
  - description
  - due_date
  - priority (high / medium / low)
  - status (todo / inprogress / done)
  - assigned_to (Foreign Key â†’ users)
  - created_by (Foreign Key â†’ users)
  - created_at


================================================================
API ENDPOINTS
================================================================

AUTH:
  POST   /api/auth/signup       Register new user
  POST   /api/auth/login        Login user
  GET    /api/auth/me           Get current user

PROJECTS:
  GET    /api/projects          List all my projects
  POST   /api/projects          Create new project
  GET    /api/projects/:id      Get project details

MEMBERS:
  GET    /api/projects/:id/members      List members
  POST   /api/projects/:id/members      Add member by email
  DELETE /api/projects/:id/members/:uid Remove member

TASKS:
  GET    /api/projects/:id/tasks    List all tasks
  POST   /api/projects/:id/tasks    Create new task
  PUT    /api/tasks/:id             Update task
  DELETE /api/tasks/:id             Delete task

DASHBOARD:
  GET    /api/dashboard         Get stats and recent tasks


================================================================
LOCAL SETUP STEPS
================================================================

STEP 1 - Make sure Python is installed
  python --version
  (Should show Python 3.7.0)

STEP 2 - Install required packages
  pip install flask flask-cors werkzeug PyJWT

STEP 3 - Go to backend folder
  cd backend

STEP 4 - Run the server
  python app.py

STEP 5 - Open browser
  http://localhost:8000

STEP 6 - Create account
  - Click Sign Up
  - Enter your name, email, password
  - You are logged in!


================================================================
DEPLOYMENT STEPS (RAILWAY)
================================================================

STEP 1 - Create GitHub account at https://github.com

STEP 2 - Install Git from https://git-scm.com

STEP 3 - Push code to GitHub
  git init
  git add .
  git commit -m "TaskFlow initial commit"
  git remote add origin https://github.com/USERNAME/taskflow.git
  git push -u origin main

STEP 4 - Go to https://railway.app
  - Sign up with GitHub
  - Click New Project
  - Select Deploy from GitHub
  - Choose your repository

STEP 5 - Add Environment Variables in Railway
  SECRET_KEY = your-secret-key-here
  JWT_SECRET = your-jwt-secret-here
  PORT       = 8000

STEP 6 - Get Live URL
  Railway Dashboard â†’ Settings â†’ Domains â†’ Generate Domain

STEP 7 - Your app is live!
  https://taskflow-xxxx.railway.app


================================================================
DEMO CREDENTIALS
================================================================

After running locally, signup with any account.

Example:
  Name     : Admin User
  Email    : admin@demo.com
  Password : admin123


================================================================
IMPORTANT NOTES
================================================================

1. Deployment is MANDATORY - app must be publicly accessible
2. Non-working applications will not be evaluated
3. Backend and frontend must be connected properly
4. Use environment variables for SECRET_KEY and JWT_SECRET
5. Candidates must be able to explain their code


================================================================
ESTIMATED TIME
================================================================

Development Time : 8 to 12 hours
Timeline         : 1 to 2 days


================================================================
CONTACT
================================================================

Name    : TUMMURU TEJA SREE
Email   : tejasreetummuru@gmail.com
GitHub  : [Your GitHub Profile URL]
College : MALLA REDDY COLLEGE OF ENGINEERING FOR WOMEN


================================================================
        END OF README
================================================================
