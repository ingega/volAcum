# -*- coding: utf-8 -*- 
import smtplib
from email.message import EmailMessage
import time
path=""

def escribirlog(mensaje):
    miarch=open(path +"log.txt","a")
    msj=mensaje + " " + time.asctime(time.gmtime()) + "\n"
    miarch.write(msj)
    miarch.close()
    print(msj)

def enviarcorreo(asunto,mensaje, filepath=None):

    try:

        # Create an email message object
        message = EmailMessage()

        email_subject = "Invercrypto mesage " + asunto
        sender_email_address = "ingega@gmail.com"
        receiver_email_address = "visualega@hotmail.com"

        # Configure email headers
        message['Subject'] = email_subject
        message['From'] = sender_email_address
        message['To'] = receiver_email_address

        # Set email body text
        message.set_content(mensaje)

        email_smtp = "smtp.gmail.com"

        # Attach a file if provided
        if filepath:
            with open(filepath, 'rb') as file:
                file_data = file.read()
                file_name = filepath.split("/")[-1]
                message.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

        # Set smtp server and port
        server = smtplib.SMTP(email_smtp, '587')

        # Identify this client to the SMTP server
        server.ehlo()

        # Secure the SMTP connection
        server.starttls()

        sender_email_address = "ingega@gmail.com"
        email_password = "zqfzvaxijwlsjjhq"

        # Login to email account
        server.login(sender_email_address, email_password)

        # Send email
        server.send_message(message)

        # Close connection to server
        server.quit()

        print("se ha mandado el correo de manera correctamente")
    except Exception as err:
        msg="there's no posible send a mail, that beacuse a server or client side errror " + str(err)
        escribirlog(msg)
        return False