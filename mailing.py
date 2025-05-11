import smtplib
import ssl
import pandas as pd
from email.message import EmailMessage
my_email = "theskillfulnoob2002@gmail.com"
app_pw = "wyxl fwfv vqpr udde"

html_content = f"""
<html>
  <body style="font-family:Arial, sans-serif; margin:0; padding:0;">
    <div style="background-color:#E0F7FA; padding:24px;">
      <div style="margin-top:20px;">
		<div style="background-color:#FFFACD; padding:16px; border-radius:8px;">
			<h2 style="color:#4CAF50; margin-top:0;">Your Weekly Digest</h2>
			<p>Welcome to May! Summer is a good time to touch more grass ☀️</p>
			<span style="font-style:italic; color: #0000ff;">Significant Newsletter revamps this week </span>:
				<ul>
    				<li>Reduced verbosity with strict word limits on auto formatting app,</li>
        			<li>Responded to need for more figures (readability) by fine-tuning P.1 Layout</li>
					<li>Injected content nutrition with P.2 Graphs (hope it's a meaningful attempt)</li>
				</ul>
			<br>
			<p>Hope you'll enjoy the read with more insights, and feel less stuffed reading it!</p>
		</div>
  
        <p style="font-style:italic; color: #3994cc;">Stay inspired and informed.
			<br>Feel free to <b>give me feedback</b> from time to time - love to hear from you too! ❤️
			<br>- Andrew
		</p>
      </div>
    </div>

    <div style="background-color:#F0F0F0; padding:16px; font-size:0.9em; color:#555; text-align:center;">
      You received this email because you're subscribed to Andrew's Weekly Newsletter.
      <br>
      You can <a href="mailto:{my_email}">Unsubscribe</a> by emailing me.
    </div>
  </body>
</html>
"""

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