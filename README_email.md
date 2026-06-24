# 📧 Automated Bulk Email Sender with Templates

**Python Developer Internship Program**  
Hasnain Karimain Educational Academy — Software House & Training Center

---

## 📌 Project Overview

A CLI + GUI based Automated Bulk Email Sender built in Python that sends personalized emails to multiple recipients using templates, SMTP, and contact lists.

---

## ✅ Features

### Core Features
- Send emails using Gmail SMTP
- Bulk sending from CSV/JSON contact list
- Predefined email templates with placeholders
- Email personalization ({name}, {company})
- Email history tracking (JSON)

### Advanced Features
- Proper error handling (invalid email, connection error)
- Modular code structure (10 modules)
- Secure login using App Password
- Retry mechanism (3 attempts) for failed emails
- Case-insensitive email handling

### Bonus Features
- 📎 File attachments (PDF, images)
- 🎨 HTML email templates (styled emails)
- ⏰ Schedule emails (send after X seconds)
- 🖥️ GUI version using Tkinter
- 📋 Email history viewer

---

## 🚀 How to Run

### Requirements
- Python 3.x (no extra libraries needed)
- Gmail account with App Password

### Setup Gmail App Password
1. Go to myaccount.google.com
2. Security → 2-Step Verification → ON
3. Search "App passwords"
4. Create → Copy 16-digit password

### Run Program
```bash
python email_sender.py
```

### Menu Options
```
1.  Setup Email (Login)
2.  Send Single Email
3.  Load Contacts (CSV)
4.  Load Contacts (JSON)
5.  Send Bulk Email
6.  Choose Template
7.  Send HTML Email
8.  Send Email with Attachment
9.  Schedule Email
10. View Email History
11. Launch GUI
12. Exit
```

---

## 📁 Project Structure

```
Bulk Email Sender/
│
├── email_sender.py      ← Main Python file (CLI + GUI)
├── contacts.csv         ← Sample CSV contact list
├── contacts.json        ← Sample JSON contact list
├── templates.json       ← Auto-created email templates
├── email_history.json   ← Auto-created sent email history
└── README.md            ← This file
```

---

## 🧠 Code Modules

| Module | Function | Description |
|--------|----------|-------------|
| 1 | `is_valid_email()` | Email validation |
| 2 | `connect_smtp()` | Gmail SMTP connection |
| 3 | `load/save_templates()` | Template management |
| 4 | `load/save_history()` | Email history |
| 5 | `send_email()` | Single email sender |
| 6 | `send_bulk()` | Bulk email with retry |
| 7 | `load_contacts_csv/json()` | Contact loading |
| 8 | `get_html_template()` | HTML email generator |
| 9 | `cli_menu()` | CLI interface |
| 10 | `launch_gui()` | Tkinter GUI |

---

## 📧 Email Templates

| Template | Subject | Usage |
|----------|---------|-------|
| welcome | Welcome to {company}! | New user welcome |
| newsletter | Monthly Newsletter | Regular updates |
| internship | Internship Offer | Job offers |

---

## 🎥 Demo Video

[Click here to watch Demo Video](https://drive.google.com/file/d/1Q5Whw7p_inJxtgec15o3C09L7QagPA0_/view?usp=sharing)

---

*Built with ❤️ using Python — No external libraries required*
