import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import dotenv_values

config = dotenv_values(".env")

smtp_host = config['SMTP_HOST']
smtp_port = config['SMTP_PORT']
smtp_username = config['SMTP_USER']
smtp_password = config['SMTP_PASSWORD']
sender_email = config['SENDER_EMAIL']


#This function defines the structure of the mail based on the document info
def formatMethod(toEmail : str, toName : str, shippingYear : str, shippingMonth :str, shippingIds : []):
  try:
    #Create a multipart message for sending both plain text and HTML content
    message = MIMEMultipart('alternative')

    # Set email header details
    message['Subject'] = 'Returned and cancelled orders info'
    message['From'] = sender_email
    message['To'] = toEmail

    #Calculate the total number of orders and create a string of shipping ids
    totalOrders = len(shippingIds)
    ordersStrings = ", ".join(shippingIds)

    #Plain text version of the email body
    text = f"""\
    Hi {toName}, How are you?
    We are reaching to you because you have cancelled or returned a total of {totalOrders} orders in {shippingYear}/{shippingMonth}.
    These are the shipping ids of the orders you have cancelled or returned: {ordersStrings}
    """

    #HTML version of the email body
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

    #Create MIMEText objects for the plain text and HTML parts of the message
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html') 

    #Attach the text and HTML parts to the message
    message.attach(part1)
    message.attach(part2) 

    #Return the complete message object
    return message   
  except Exception as e:
     print(e)
     return "An exception was encountered. The mail message wasn't properly formatted."

def sendEmail(toEmail : str, toName : str, shippingYear : str, shippingMonth :str, shippingIds : []):

  #Create an email message using the formatMethod function
  message = formatMethod(toEmail, toName, shippingYear, shippingMonth, shippingIds)
  try: 
      #Establish a connection to the SMTP server
      with smtplib.SMTP(smtp_host, smtp_port) as smtp:
          #Upgrade the connection to use TLS
          smtp.starttls()
          smtp.login(user=smtp_username, password= smtp_password)
          smtp.sendmail(sender_email, toEmail, message.as_string())
      #If the email is sent successfully, return a success message
      return "Message sent"
  except Exception as e:
      #If an exception occurs, print the error and return an error message
      print(e)
      return "An exception was encountered. The message wasn't sent" 

    
    