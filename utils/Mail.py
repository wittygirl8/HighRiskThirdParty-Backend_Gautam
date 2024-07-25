import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app as app


class Mail:
    def __init__(self):
        self.sender_address = app.config.get("EMAIL_SENDER_ADDRESS")
        self.sender_pass = app.config.get("EMAIL_SENDER_PASSWORD")

    def send_mail_for_new_user(self, email, name, password):
        mail_body = (f'Dear {name},\n\nWelcome to Project Name! Your account has been created successfully. Please find '
                     f'your login credentials below:\n\nUSERNAME: {email}\nPASSWORD: {password}\n\nBest regards,'
                     f'\n\nEY-GSK TEAM\n\n---\n\nThis is an auto-generated email; please DO NOT REPLY.')
        self.send_mail(email, "Welcome to Project Name", mail_body)

    def send_mail(self, email, subject, mail_content):
        try:
            receiver_address = email
            message = MIMEMultipart()
            message['From'] = self.sender_address
            message['To'] = receiver_address
            message['Subject'] = subject
            message.attach(MIMEText(mail_content, 'plain'))
            session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
            session.ehlo()
            session.starttls()  # enable security
            session.login(self.sender_address, self.sender_pass)  # login with mail_id and password
            text = message.as_string()
            session.sendmail(self.sender_address, receiver_address, text)
            session.quit()
        except Exception as e:
            traceback.print_exc()
            print(e)
