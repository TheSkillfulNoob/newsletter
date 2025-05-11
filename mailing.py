import smtplib
import ssl
import pandas as pd
from email.message import EmailMessage
my_email = "theskillfulnoob2002@gmail.com"
app_pw = "wyxl fwfv vqpr udde"

def send_newsletter(csv_path, subject, plain_body, html_body, attachment_path=None, debug_email = None):
    if debug_email or not csv_path:
        bcc_list = [debug_email]
    else:
        df = pd.read_csv(csv_path)
        bcc_list = df['email'].tolist()
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = my_email
    msg['To'] = my_email  # visible To field (yourself or generic newsletter identity)
    msg['Bcc'] = ', '.join(bcc_list)
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype='html')

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf',
                               filename=attachment_path)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(my_email, app_pw)
        smtp.send_message(msg)