import datetime
import time
from twilio.rest import Client
from flask import Flask, request

# Your Account SID from twilio.com/console
account_sid = "AC8c14921fcae1fead46c9a56bbd46d606"
# Your Auth Token from twilio.com/console
auth_token = "8965b33b265c904b8270dd9124f9334c"

client = Client(account_sid, auth_token)


def notify_phone(output):
    message = f"{output}"
    message = client.messages.create(
        to="+13035796207",
        from_="+18573922435",
        body=message)


app = Flask(__name__)


@app.route('/sms', methods=['POST'])
def receive_sms():
    # Get the SMS message details from the request
    message_body = request.form['Body']
    message_from = request.form['From']

    # Print the message details to the console
    print(f"Received a message from {message_from}: {message_body}")

    return ''


def wait_for_message():
    latest_message_date_sent = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)

    while True:
        # Use the Twilio API to fetch the latest incoming SMS messages
        messages = client.messages.list(
            limit=1,
            to='+18573922435',
            date_sent_after=latest_message_date_sent
        )

        if messages:
            message = messages[0]

            # Extract the message body and sender information
            message_body = message.body

            message_from = message.from_

            # Set the latest message date_sent to the date_sent of the most recently processed message
            latest_message_date_sent = message.date_sent

            return message_body

        # Wait for a few seconds before checking for new messages again
        time.sleep(5)


def digest_message(message_body):
    # Process the message contents here
    print(message_body)

def placed(book, team, ml,ev):
    if book.upper() == 'BARSTOOL':
        book = 'barstool'
    elif book.upper() == 'DRAFTKINGS':
        book = 'dk'
    elif book.upper() =='MYBOOKIEAG':
        book = 'mb'
    elif book.upper() =='BETONLINEAG':
        book = 'bonline'
    rounded_ev = int(ev)

    message = f'\nSuccessfully placed!\n{book} {team} @{ml}'
    # ev:{rounded_ev}%'

    notify_phone(message)

