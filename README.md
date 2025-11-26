# MIS Institute Management System

A comprehensive web-based management system for educational institutions built with Flask and PostgreSQL.

## 🎯 Features

### User Roles

- **Admin**: Manage users, classes, subjects, and schedules
- **Teacher**: Take attendance, manage grades, assign homework, track weekly topics
- **Student**: View attendance, grades, homework, weekly topics, and timetable

### Core Functionality

- ✅ User Authentication (login/logout)
- ✅ Role-based Access Control
- ✅ Class Management
- ✅ Student Management
- ✅ Subject Management
- ✅ Attendance Tracking
- ✅ Grade Management (Quiz, Exam, Homework, Midterm, Final, Project)
- ✅ Homework Assignments
- ✅ Weekly Topics Tracking
- ✅ Timetable/Schedule Management

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Icons**: Bootstrap Icons

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL installed and running
- pgAdmin (optional, for database management)

### Step 1: Set Up PostgreSQL Database

1. Open pgAdmin or PostgreSQL command line
2. Create a new database:

```sql
CREATE DATABASE mis_system;
```

3. Run the schema file to create tables:
   - Open `database/schema.sql` in pgAdmin
   - Execute the SQL script

### Step 2: Configure Environment

1. Copy the example environment file:

```bash
copy .env.example .env
```

2. Edit `.env` and update the database credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mis_system
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

The application will start at: **http://localhost:5000**

## 🔐 Default Login Credentials

| Role  | Username | Password |
| ----- | -------- | -------- |
| Admin | admin    | admin123 |

**⚠️ Important**: Change the default admin password after first login!

## 📁 Project Structure

```
mis/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── db.py                  # Database connection and queries
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── database/
│   └── schema.sql         # PostgreSQL database schema
├── static/
│   └── css/
│       └── style.css      # Custom styles
└── templates/
    ├── base.html          # Base template
    ├── login.html         # Login page
    ├── dashboard.html     # Generic dashboard
    ├── admin/             # Admin templates
    │   ├── dashboard.html
    │   ├── users.html
    │   ├── add_user.html
    │   ├── classes.html
    │   ├── add_class.html
    │   ├── class_students.html
    │   ├── subjects.html
    │   └── add_subject.html
    ├── teacher/           # Teacher templates
    │   ├── dashboard.html
    │   ├── attendance.html
    │   ├── take_attendance.html
    │   ├── grades.html
    │   ├── add_grades.html
    │   ├── view_grades.html
    │   ├── homework.html
    │   ├── add_homework.html
    │   ├── topics.html
    │   └── manage_topics.html
    └── student/           # Student templates
        └── dashboard.html
```

## 🚀 Quick Start Guide

1. **Login as Admin** → Create classes
2. **Create Teachers** → Assign them to subjects
3. **Create Students** → Assign them to classes
4. **Login as Teacher** → Take attendance, add grades, assign homework
5. **Login as Student** → View all information

## 📝 Database Schema

### Tables

- `users` - All user accounts
- `classes` - Class/section information
- `teachers` - Teacher profiles
- `students` - Student profiles
- `subjects` - Course subjects
- `attendance` - Daily attendance records
- `grades` - Quiz, exam, homework grades
- `weekly_topics` - Syllabus tracking
- `homework` - Homework assignments
- `timetable` - Class schedules

## 🔧 Configuration Options

Edit `config.py` to customize:

- Database connection settings
- Session timeout
- Debug mode

## 👨‍💻 Development

### Running in Debug Mode

```bash
python app.py
```

### Creating New Admin User

The first admin is created automatically. To create additional admins, use the Admin panel.

## 📄 License

This project is created for educational purposes at EPU - MIS Department.

## 🤝 Support

For questions or issues, contact your instructor or raise an issue in the project repository.

---

**EPU - MIS Department © 2025**
