import time
import pyzmail
import imapclient
import smtplib
import email.message
from pprint import pprint
import mailparser
import html2markdown
import configparser
from slack import WebClient
import sched


config = configparser.ConfigParser()
config.read("config.ini")
BOT_TOKEN = config.get("SLACK", "BOT_TOKEN")

imap_server = "imap.gmail.com"
smtp_server = "smtp.gmail.com"
addr = config.get("EMAIL", "ADDRESS")
pwd = config.get("EMAIL", "PASSWORD")

readonly_state = False

def fetch_unread():

  unseen_msgs = list()
  # Login
  imapobj = imapclient.IMAPClient(imap_server, ssl=True)
  imapobj.login(addr, pwd)
  
  # Fetch folders
  for fol in imapobj.list_folders():
    if ("[Gmail]" not in fol[2]):

      # Select folder
      imapobj.select_folder(f"{fol[2]}", readonly=readonly_state)
      unseen_uids = imapobj.search(["UNSEEN"])

      # Fetch messages
      try:
        if unseen_uids:
          for uid in unseen_uids:
            msg = {}
            raw_message = imapobj.fetch([uid], ['BODY[]', 'FLAGS'])
            # pprint(raw_message)
            message = pyzmail.PyzMessage.factory(raw_message[uid][b'BODY[]'])
            msg["uid"] = uid
            msg["Subject"] = message.get_subject()
            msg["from"] = message.get_addresses('from')[0][1]
            msg["to"] = message.get_addresses('to')[0][1]
            # mail = mailparser.parse_from_bytes(raw_message[uid][b'BODY[]'])
            # print(mail.text_plain)

            if message.text_part != None:
              body = message.text_part.get_payload().decode(message.text_part.charset)
              msg["body"] = body
              
            else:
              raw_body = message.html_part.get_payload().decode(message.html_part.charset)
              parsed_body = html2markdown.convert(raw_body)
              msg["body"] = parsed_body
            unseen_msgs.append(msg)
            # pprint(msg)
              # Logout
            
            
      except Exception as e:
        print(e)
      # finally:
        # imapobj.logout()
      imapobj.close_folder()
  imapobj.logout()

  return unseen_msgs
  # return None

def reply(from_email, to, subject, content):
  stmpobj = smtplib.SMTP(smtp_server, 587)
  if not subject.startswith("Re"):
      subject = "Re: " + subject
  
  stmpobj.starttls()

  msg = email.message.EmailMessage()
  msg["from"] = from_email
  msg["to"] = to
  msg["Subject"] = subject
  msg.set_content(content)

  # Login
  stmpobj.login(addr, pwd)

  # Reply
  res = stmpobj.send_message(msg)
  pprint(res)

def post_unread():
    unread_messages = fetch_unread()
    if unread_messages:
        for msg in unread_messages:
            res = bot.chat_postMessage(
                channel = email_channel,
                text = "",
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*You have a new email:inbox_tray:*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*From:*\n{msg['from']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*To:*\n{msg['to']}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Subject:*\n{msg['Subject']}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": msg["body"]
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": ":bust_in_silhouette:Assign"
                                },
                                "style": "primary",
                                "value": "assign_email"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": ":email:Reply"
                                },
                                "value": "reply"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": ":white_check_mark:Complete"
                                },
                                "style": "primary",
                                "value": "email_completed"
                            }
                        ]
                    },
                ]
            )

while True:
  post_unread()
  time.sleep(300)
# reply(addr, "caleb.njiiri@gmail.com","tyui", "Netflix is a joke" )
# pprint(fetch_unread())





  
  
