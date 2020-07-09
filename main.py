import time
import pyzmail
import imapclient
import smtplib
import email.message
from pprint import pprint
import mailparser

imap_server = "imap.gmail.com"
smtp_server = "smtp.gmail.com"
addr = "jamescouldron@gmail.com"
pwd = "95170305"
readonly_state = True

def fetch_unread():

  unseen_msgs = list()
  # Login
  imapobj = imapclient.IMAPClient(imap_server, ssl=True)
  imapobj.login(addr, pwd)
  
  # Fetch folders
  for fol in imapobj.list_folders():

    if fol[2] == 'INBOX':
      # Select folder
      imapobj.select_folder('INBOX', readonly=readonly_state)
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
              msg["body"] = message.html_part.get_payload().decode(message.html_part.charset)

            unseen_msgs.append(msg)
            # pprint(msg)
              # Logout
            
            
      except Exception as e:
        print(e)
      finally:
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

# reply(addr, "caleb.njiiri@gmail.com","tyui", "Netflix is a joke" )
# pprint(fetch_unread())





  
  
