import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import dotenv_values



config = dotenv_values(".env")

smtp_server = config['SMTP_SERVER']
smtp_port = config['SMTP_PORT']
smtp_username = config['SMTP_USER']
smtp_password = config['SMTP_PASSWORD']
sender_email = config['SENDER_EMAIL']
# message = f'Subject: {subject}\n\n{body}'


 
def formatMethod(toEmail : str, toName : str, shippingYear : str, shippingMonth :str, shippingIds : []):

  message = MIMEMultipart('alternative')
  message['Subject'] = 'Returned and cancelled orders info'
  message['From'] = sender_email
  message['To'] = toEmail

  totalOrders = len(shippingIds)
  ordersStrings = ", ".join(shippingIds)
  text = f"""\
  Hi {toName}, How are you?
  We are reaching to you because you have cancelled or returned a total of {totalOrders} orders in {shippingYear}/{shippingMonth}.
  These are the shipping ids of the orders you have cancelled or returned: {ordersStrings}
  """
  html = f"""\
  <html>
    <body>
      <p>Hi {toName}<br>
        How are you?<br>
        We are reaching to you because you have cancelled or returned a total of {totalOrders} orders in {shippingYear}/{shippingMonth}.<br>
        These are the shipping ids of the orders you have cancelled or returned: {ordersStrings}
      </p>
    </body>
  </html>
  """

  part1 = MIMEText(text, 'plain')
  part2 = MIMEText(html, 'html') 

  message.attach(part1)
  message.attach(part2) 

  return message   

def sendEmail(toEmail : str, toName : str, shippingYear : str, shippingMonth :str, shippingIds : []):

  message = formatMethod(toEmail, toName, shippingYear, shippingMonth, shippingIds)
  try: 
      with smtplib.SMTP(smtp_server, smtp_port) as smtp:
          smtp.starttls()
          smtp.login(smtp_username, smtp_password)
          smtp.sendmail(sender_email, toEmail, message.as_string())
      return "Message sent"
  except Exception as e:
      print(e)
      return "An exception was encountered. The message wasn't sent" 

    
    