"""
╔══════════════════════════════════════════════════════════╗
║       AUTOMATED BULK EMAIL SENDER WITH TEMPLATES        ║
║       Python Developer Internship Program                ║
║       Hasnain Karimain Educational Academy               ║
╚══════════════════════════════════════════════════════════╝

Features:
  - Send emails using SMTP (smtplib)
  - Bulk sending from CSV/JSON contact list
  - Predefined email templates with placeholders
  - Email personalization {name}, {company}
  - Email history tracking (JSON)
  - Retry mechanism for failed emails
  - File attachments (PDF, images)
  - HTML email templates
  - Schedule emails
  - GUI version (Tkinter)
  - Modular code & error handling
"""

import smtplib
import csv
import json
import os
import time
import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import re
import threading

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
HISTORY_FILE   = "email_history.json"
TEMPLATES_FILE = "templates.json"
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 587
MAX_RETRIES    = 3


# ══════════════════════════════════════════════
#  MODULE 1 — EMAIL VALIDATION
# ══════════════════════════════════════════════

def is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
    return re.match(pattern, email.strip()) is not None


# ══════════════════════════════════════════════
#  MODULE 2 — SMTP CONNECTION
# ══════════════════════════════════════════════

def connect_smtp(sender_email: str, app_password: str):
    """Connect to Gmail SMTP server securely."""
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(sender_email.strip().lower(), app_password.strip())
        return server
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed! Check email and app password.")
        return None
    except smtplib.SMTPConnectError:
        print("❌ Connection error! Check internet connection.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ══════════════════════════════════════════════
#  MODULE 3 — TEMPLATE MANAGEMENT
# ══════════════════════════════════════════════

def load_templates() -> dict:
    """Load email templates from JSON file."""
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "r") as f:
            return json.load(f)
    # Default templates
    default = {
        "welcome": {
            "subject": "Welcome to {company}!",
            "body": "Hello {name},\n\nWelcome to {company}! We are thrilled to have you on board.\n\nBest regards,\nThe {company} Team"
        },
        "newsletter": {
            "subject": "Monthly Newsletter from {company}",
            "body": "Dear {name},\n\nHere is your monthly newsletter from {company}.\n\nStay tuned for more updates!\n\nBest regards,\n{company}"
        },
        "internship": {
            "subject": "Internship Offer - {company}",
            "body": "Dear {name},\n\nCongratulations! We are pleased to offer you an internship at {company}.\n\nPlease confirm your acceptance.\n\nBest regards,\nHR Team - {company}"
        }
    }
    save_templates(default)
    return default


def save_templates(templates: dict):
    """Save templates to JSON file."""
    with open(TEMPLATES_FILE, "w") as f:
        json.dump(templates, f, indent=4)


def apply_template(template: dict, name: str, company: str) -> tuple:
    """Replace placeholders in template with actual values."""
    subject = template["subject"].replace("{name}", name).replace("{company}", company)
    body    = template["body"].replace("{name}", name).replace("{company}", company)
    return subject, body


# ══════════════════════════════════════════════
#  MODULE 4 — EMAIL HISTORY
# ══════════════════════════════════════════════

def load_history() -> list:
    """Load email history from JSON file."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history: list):
    """Save email history to JSON file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


def add_to_history(email: str, subject: str, status: str):
    """Add a sent email record to history."""
    history = load_history()
    history.append({
        "email"    : email,
        "subject"  : subject,
        "status"   : status,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_history(history)


# ══════════════════════════════════════════════
#  MODULE 5 — SEND SINGLE EMAIL
# ══════════════════════════════════════════════

def send_email(server, sender: str, recipient: str, subject: str,
               body: str, html: bool = False, attachment: str = "") -> bool:
    """Send a single email with optional HTML and attachment."""
    if not is_valid_email(recipient):
        print(f"❌ Invalid email: {recipient}")
        add_to_history(recipient, subject, "Failed - Invalid Email")
        return False

    try:
        msg = MIMEMultipart("alternative" if html else "mixed")
        msg["From"]    = sender
        msg["To"]      = recipient.strip().lower()
        msg["Subject"] = subject

        if html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        # Attachment
        if attachment and os.path.exists(attachment):
            with open(attachment, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition",
                                f"attachment; filename={os.path.basename(attachment)}")
                msg.attach(part)

        server.sendmail(sender, recipient.strip().lower(), msg.as_string())
        print(f"✅ Email sent to {recipient}")
        add_to_history(recipient, subject, "Sent")
        return True

    except Exception as e:
        print(f"❌ Failed to send to {recipient}: {e}")
        add_to_history(recipient, subject, f"Failed - {str(e)}")
        return False


# ══════════════════════════════════════════════
#  MODULE 6 — BULK SENDING WITH RETRY
# ══════════════════════════════════════════════

def send_bulk(server, sender: str, contacts: list, subject: str,
              body: str, html: bool = False, attachment: str = ""):
    """Send emails to multiple recipients with retry mechanism."""
    success = 0
    failed  = 0
    failed_list = []

    for contact in contacts:
        email   = contact.get("email", "")
        name    = contact.get("name", "User")
        company = contact.get("company", "Our Company")

        # Personalize body
        personal_body    = body.replace("{name}", name).replace("{company}", company)
        personal_subject = subject.replace("{name}", name).replace("{company}", company)

        sent = False
        for attempt in range(1, MAX_RETRIES + 1):
            if send_email(server, sender, email, personal_subject,
                         personal_body, html, attachment):
                success += 1
                sent = True
                break
            else:
                if attempt < MAX_RETRIES:
                    print(f"   🔄 Retrying ({attempt}/{MAX_RETRIES})...")
                    time.sleep(2)

        if not sent:
            failed += 1
            failed_list.append(email)

        time.sleep(1)  # Avoid spam detection

    print(f"\n📊 Bulk Send Complete:")
    print(f"   ✅ Sent    : {success}")
    print(f"   ❌ Failed  : {failed}")
    if failed_list:
        print(f"   Failed emails: {', '.join(failed_list)}")


# ══════════════════════════════════════════════
#  MODULE 7 — LOAD CONTACTS
# ══════════════════════════════════════════════

def load_contacts_csv(filepath: str) -> list:
    """Load contacts from CSV file."""
    contacts = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                contacts.append(row)
        print(f"✅ Loaded {len(contacts)} contacts from CSV.")
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return contacts


def load_contacts_json(filepath: str) -> list:
    """Load contacts from JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            contacts = json.load(f)
        print(f"✅ Loaded {len(contacts)} contacts from JSON.")
        return contacts
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


# ══════════════════════════════════════════════
#  MODULE 8 — HTML EMAIL TEMPLATE
# ══════════════════════════════════════════════

def get_html_template(name: str, company: str, message: str) -> str:
    """Generate a styled HTML email template."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white;
                    border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                📧 Message from {company}
            </h2>
            <p style="color: #555; font-size: 16px;">Dear <strong>{name}</strong>,</p>
            <p style="color: #555; font-size: 15px; line-height: 1.6;">{message}</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px; text-align: center;">
                © 2024 {company} | This is an automated email.
            </p>
        </div>
    </body>
    </html>
    """


# ══════════════════════════════════════════════
#  MODULE 9 — CLI MENU
# ══════════════════════════════════════════════

def cli_menu():
    print("\n" + "═" * 55)
    print("   📧  AUTOMATED BULK EMAIL SENDER  📧")
    print("   Hasnain Karimain Educational Academy")
    print("═" * 55)

    sender_email = ""
    app_password = ""
    server       = None
    contacts     = []
    templates    = load_templates()

    while True:
        print("\n─── MAIN MENU ───")
        print("1.  Setup Email (Login)")
        print("2.  Send Single Email")
        print("3.  Load Contacts (CSV)")
        print("4.  Load Contacts (JSON)")
        print("5.  Send Bulk Email")
        print("6.  Choose Template")
        print("7.  Send HTML Email")
        print("8.  Send Email with Attachment")
        print("9.  Schedule Email")
        print("10. View Email History")
        print("11. Launch GUI")
        print("12. Exit")

        choice = input("\nSelect option (1-12): ").strip()

        # ── 1. Setup ──────────────────────────
        if choice == "1":
            sender_email = input("Enter your Gmail: ").strip().lower()
            if not is_valid_email(sender_email):
                print("❌ Invalid email format.")
                continue
            app_password = input("Enter App Password (16 digits): ").strip()
            print("🔄 Connecting...")
            server = connect_smtp(sender_email, app_password)
            if server:
                print(f"✅ Connected as {sender_email}")

        # ── 2. Single Email ───────────────────
        elif choice == "2":
            if not server:
                print("⚠️  Setup email first (Option 1).")
                continue
            to      = input("Recipient email: ").strip()
            subject = input("Subject: ").strip()
            body    = input("Message: ").strip()
            send_email(server, sender_email, to, subject, body)

        # ── 3. Load CSV ───────────────────────
        elif choice == "3":
            path     = input("Enter CSV file path: ").strip()
            contacts = load_contacts_csv(path)
            if contacts:
                print("Sample contact:", contacts[0])

        # ── 4. Load JSON ──────────────────────
        elif choice == "4":
            path     = input("Enter JSON file path: ").strip()
            contacts = load_contacts_json(path)
            if contacts:
                print("Sample contact:", contacts[0])

        # ── 5. Bulk Send ──────────────────────
        elif choice == "5":
            if not server:
                print("⚠️  Setup email first (Option 1).")
                continue
            if not contacts:
                print("⚠️  Load contacts first (Option 3 or 4).")
                continue
            subject = input("Email subject: ").strip()
            body    = input("Email message (use {name} and {company}): ").strip()
            send_bulk(server, sender_email, contacts, subject, body)

        # ── 6. Template ───────────────────────
        elif choice == "6":
            if not server:
                print("⚠️  Setup email first.")
                continue
            print("\nAvailable templates:")
            for i, key in enumerate(templates.keys(), 1):
                print(f"  {i}. {key}")
            t_name = input("Enter template name: ").strip().lower()
            if t_name not in templates:
                print("❌ Template not found.")
                continue
            to      = input("Recipient email: ").strip()
            name    = input("Recipient name: ").strip()
            company = input("Company name: ").strip()
            subject, body = apply_template(templates[t_name], name, company)
            send_email(server, sender_email, to, subject, body)

        # ── 7. HTML Email ─────────────────────
        elif choice == "7":
            if not server:
                print("⚠️  Setup email first.")
                continue
            to      = input("Recipient email: ").strip()
            name    = input("Recipient name: ").strip()
            company = input("Company name: ").strip()
            subject = input("Subject: ").strip()
            message = input("Message: ").strip()
            html_body = get_html_template(name, company, message)
            send_email(server, sender_email, to, subject, html_body, html=True)

        # ── 8. Attachment ─────────────────────
        elif choice == "8":
            if not server:
                print("⚠️  Setup email first.")
                continue
            to         = input("Recipient email: ").strip()
            subject    = input("Subject: ").strip()
            body       = input("Message: ").strip()
            attachment = input("Attachment file path: ").strip()
            send_email(server, sender_email, to, subject, body,
                      attachment=attachment)

        # ── 9. Schedule ───────────────────────
        elif choice == "9":
            if not server:
                print("⚠️  Setup email first.")
                continue
            to      = input("Recipient email: ").strip()
            subject = input("Subject: ").strip()
            body    = input("Message: ").strip()
            delay   = input("Send after how many seconds? ").strip()
            delay   = int(delay) if delay.isdigit() else 5
            print(f"⏰ Email scheduled to send in {delay} seconds...")
            time.sleep(delay)
            send_email(server, sender_email, to, subject, body)

        # ── 10. History ───────────────────────
        elif choice == "10":
            history = load_history()
            if not history:
                print("⚠️  No email history found.")
                continue
            print(f"\n📋 EMAIL HISTORY ({len(history)} records):")
            print(f"{'#':<4} {'Email':<30} {'Subject':<25} {'Status':<10} {'Time'}")
            print("─" * 90)
            for i, h in enumerate(history[-10:], 1):
                print(f"{i:<4} {h['email']:<30} {h['subject'][:23]:<25} {h['status']:<10} {h['timestamp']}")

        # ── 11. GUI ───────────────────────────
        elif choice == "11":
            print("\n🖥️  Launching GUI...")
            launch_gui()

        # ── 12. Exit ──────────────────────────
        elif choice == "12":
            if server:
                try:
                    server.quit()
                except:
                    pass
            print("\n👋 Goodbye!")
            break

        else:
            print("⚠️  Invalid choice. Enter 1-12.")


# ══════════════════════════════════════════════
#  MODULE 10 — GUI (TKINTER)
# ══════════════════════════════════════════════

def launch_gui():
    root = tk.Tk()
    root.title("📧 Bulk Email Sender")
    root.geometry("800x650")
    root.configure(bg="#1e1e2e")

    BG     = "#1e1e2e"
    FG     = "#cdd6f4"
    ACCENT = "#89b4fa"
    BTN_BG = "#313244"
    GREEN  = "#a6e3a1"
    RED    = "#f38ba8"

    server_ref    = [None]
    sender_ref    = [""]
    contacts_ref  = [[]]
    templates     = load_templates()

    tk.Label(root, text="📧 Automated Bulk Email Sender",
             font=("Consolas", 14, "bold"), bg=BG, fg=ACCENT).pack(pady=8)
    tk.Label(root, text="Hasnain Karimain Educational Academy",
             font=("Consolas", 9), bg=BG, fg=FG).pack()

    # ── Login Frame ───────────────────────────
    login_frame = tk.LabelFrame(root, text=" Setup Email ",
                                font=("Consolas", 10), bg=BG, fg=ACCENT)
    login_frame.pack(fill="x", padx=20, pady=8)

    tk.Label(login_frame, text="Gmail:", font=("Consolas", 10),
             bg=BG, fg=FG).grid(row=0, column=0, padx=8, pady=5, sticky="w")
    email_entry = tk.Entry(login_frame, font=("Consolas", 10),
                           bg="#313244", fg=FG, insertbackground=FG,
                           relief="flat", bd=4, width=30)
    email_entry.grid(row=0, column=1, padx=8, pady=5)

    tk.Label(login_frame, text="App Password:", font=("Consolas", 10),
             bg=BG, fg=FG).grid(row=0, column=2, padx=8, sticky="w")
    pwd_entry = tk.Entry(login_frame, font=("Consolas", 10), show="*",
                         bg="#313244", fg=FG, insertbackground=FG,
                         relief="flat", bd=4, width=20)
    pwd_entry.grid(row=0, column=3, padx=8, pady=5)

    def do_connect():
        email = email_entry.get().strip().lower()
        pwd   = pwd_entry.get().strip()
        if not is_valid_email(email):
            messagebox.showerror("Error", "Invalid email!")
            return
        status_label.config(text="🔄 Connecting...", fg=ACCENT)
        root.update()
        s = connect_smtp(email, pwd)
        if s:
            server_ref[0] = s
            sender_ref[0] = email
            status_label.config(text=f"✅ Connected as {email}", fg=GREEN)
        else:
            status_label.config(text="❌ Connection failed!", fg=RED)

    btn_cfg = dict(font=("Consolas", 9, "bold"), bg=BTN_BG, fg=FG,
                   relief="flat", padx=8, pady=5, cursor="hand2")

    tk.Button(login_frame, text="🔌 Connect", command=do_connect,
              **btn_cfg).grid(row=0, column=4, padx=8)

    # ── Send Frame ────────────────────────────
    send_frame = tk.LabelFrame(root, text=" Compose Email ",
                               font=("Consolas", 10), bg=BG, fg=ACCENT)
    send_frame.pack(fill="x", padx=20, pady=5)

    tk.Label(send_frame, text="To:", font=("Consolas", 10),
             bg=BG, fg=FG).grid(row=0, column=0, padx=8, pady=4, sticky="w")
    to_entry = tk.Entry(send_frame, font=("Consolas", 10),
                        bg="#313244", fg=FG, insertbackground=FG,
                        relief="flat", bd=4, width=35)
    to_entry.grid(row=0, column=1, padx=8, pady=4, sticky="w")

    tk.Label(send_frame, text="Subject:", font=("Consolas", 10),
             bg=BG, fg=FG).grid(row=1, column=0, padx=8, pady=4, sticky="w")
    subject_entry = tk.Entry(send_frame, font=("Consolas", 10),
                             bg="#313244", fg=FG, insertbackground=FG,
                             relief="flat", bd=4, width=35)
    subject_entry.grid(row=1, column=1, padx=8, pady=4, sticky="w")

    tk.Label(send_frame, text="Template:", font=("Consolas", 10),
             bg=BG, fg=FG).grid(row=0, column=2, padx=8, sticky="w")
    tmpl_var = tk.StringVar(value="none")
    tmpl_menu = ttk.Combobox(send_frame, textvariable=tmpl_var,
                              values=["none"] + list(templates.keys()),
                              width=15, state="readonly")
    tmpl_menu.grid(row=0, column=3, padx=8)

    tk.Label(send_frame, text="Name:", font=("Consolas", 10),
             bg=BG, fg=FG).grid(row=1, column=2, padx=8, sticky="w")
    name_entry = tk.Entry(send_frame, font=("Consolas", 10),
                          bg="#313244", fg=FG, insertbackground=FG,
                          relief="flat", bd=4, width=15)
    name_entry.grid(row=1, column=3, padx=8)

    tk.Label(send_frame, text="Message:", font=("Consolas", 10),
             bg=BG, fg=FG).grid(row=2, column=0, padx=8, pady=4, sticky="nw")
    msg_box = scrolledtext.ScrolledText(send_frame, height=5,
                                        font=("Consolas", 10),
                                        bg="#313244", fg=FG,
                                        insertbackground=FG, relief="flat", bd=4)
    msg_box.grid(row=2, column=1, columnspan=3, padx=8, pady=4, sticky="ew")

    def do_send():
        if not server_ref[0]:
            messagebox.showwarning("Warning", "Connect email first!")
            return
        to      = to_entry.get().strip()
        subject = subject_entry.get().strip()
        body    = msg_box.get("1.0", "end").strip()
        name    = name_entry.get().strip() or "User"
        tmpl    = tmpl_var.get()

        if tmpl != "none" and tmpl in templates:
            subject, body = apply_template(templates[tmpl], name, "HK Academy")

        if send_email(server_ref[0], sender_ref[0], to, subject, body):
            status_label.config(text=f"✅ Email sent to {to}", fg=GREEN)
        else:
            status_label.config(text=f"❌ Failed to send to {to}", fg=RED)

    def do_load_contacts():
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")])
        if not path:
            return
        if path.endswith(".csv"):
            contacts_ref[0] = load_contacts_csv(path)
        else:
            contacts_ref[0] = load_contacts_json(path)
        status_label.config(
            text=f"✅ Loaded {len(contacts_ref[0])} contacts", fg=GREEN)

    def do_bulk_send():
        if not server_ref[0]:
            messagebox.showwarning("Warning", "Connect email first!")
            return
        if not contacts_ref[0]:
            messagebox.showwarning("Warning", "Load contacts first!")
            return
        subject = subject_entry.get().strip()
        body    = msg_box.get("1.0", "end").strip()

        def run():
            send_bulk(server_ref[0], sender_ref[0],
                     contacts_ref[0], subject, body)
            status_label.config(
                text=f"✅ Bulk send complete!", fg=GREEN)

        threading.Thread(target=run, daemon=True).start()
        status_label.config(text="🔄 Sending bulk emails...", fg=ACCENT)

    def do_view_history():
        history = load_history()
        hist_win = tk.Toplevel(root)
        hist_win.title("Email History")
        hist_win.configure(bg=BG)
        hist_win.geometry("700x400")
        tree = ttk.Treeview(hist_win,
                            columns=("Email","Subject","Status","Time"),
                            show="headings")
        for col in ("Email","Subject","Status","Time"):
            tree.heading(col, text=col)
            tree.column(col, width=150)
        for h in history:
            tree.insert("", "end",
                       values=(h["email"], h["subject"],
                               h["status"], h["timestamp"]))
        tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ── Buttons ───────────────────────────────
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(pady=8)

    tk.Button(btn_frame, text="📤 Send Email",    command=do_send,         **btn_cfg).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="📂 Load Contacts", command=do_load_contacts,**btn_cfg).grid(row=0, column=1, padx=5)
    tk.Button(btn_frame, text="📨 Bulk Send",     command=do_bulk_send,    **btn_cfg).grid(row=0, column=2, padx=5)
    tk.Button(btn_frame, text="📋 History",       command=do_view_history, **btn_cfg).grid(row=0, column=3, padx=5)

    # ── Status ────────────────────────────────
    status_label = tk.Label(root, text="Ready — Connect your email to begin",
                             font=("Consolas", 9), bg="#313244", fg=FG,
                             anchor="w")
    status_label.pack(fill="x", padx=20, pady=8)

    root.mainloop()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    cli_menu()
