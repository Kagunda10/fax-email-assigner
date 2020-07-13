'''
TODO
- Fetch the list of usernames from google sheets 
-  Add the assigned user and the fax number to a google sheet
- Remove all hardcoded variables and implement a config file
'''

from slack import WebClient
from main import fetch_unread, reply
from flask import Flask, request, jsonify, make_response
from pprint import pprint
import json
from utils import AfterThisResponse, get_member_block

BOT_TOKEN = "xoxb-899759167666-1240407393364-L6Rox22GlanzoNEBZnYuEJo4"
# BOT_TOKEN = "xoxb-535944217620-1223630838033-UAKWKPtfNzKjv1VGuYYMFOOr"
USER_TOKEN = "xoxp-899759167666-914750686518-1234435004515-13364650811f9606492b0c2e4ab61231"
# USER_TOKEN = "xoxp-535944217620-535998288195-1196342482263-19d91c224d99ce3ea3e3a7d0cd45098c"
bot = WebClient(token=BOT_TOKEN)
user = WebClient(token=USER_TOKEN)

fax_members_block = get_member_block("fax")
email_members_block = get_member_block("email")

archive_channel = "#random"

app = Flask(__name__)
AfterThisResponse(app)
    
@app.route("/message_actions", methods=["POST"])
def interactivity():

    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # pprint(form_json)
    user_id = form_json["user"]["id"]
    

    #Check to see the type of interactivity
    if form_json["type"] == "block_actions":
        trigger_id = form_json["trigger_id"]
        # Check to see what the user's selection was and update the message accordingly
        selection = form_json["actions"][0]["value"]

        if selection == "assign_email":          
            # Open dialog
            open_dialog = bot.dialog_open(
                trigger_id=trigger_id,
                dialog={
                    "title": "Select the member",
                    "submit_label": "Submit",
                    "callback_id": form_json["message"]["ts"],
                    "state": json.dumps(form_json["message"]["blocks"]),
                    "elements": [
                        {
                            "label": "Username",
                            "type": "select",
                            "name": "email_assignee",
                            "placeholder": "Select a user",
                            "options": email_members_block
                        }
                    ]
                }
            )
        elif selection == "assign_fax":
            # Open dialog
            open_dialog = bot.dialog_open(
                trigger_id=trigger_id,
                dialog={
                    "title": "Select the member",
                    "submit_label": "Submit",
                    "callback_id": form_json["message"]["ts"],
                    "state": json.dumps(form_json["message"]["blocks"]),
                    "elements": [
                        {
                            "label": "Username",
                            "type": "select",
                            "name": "fax_assignee",
                            "placeholder": "Select a user",
                            "options": fax_members_block
                        }
                    ]
                }
            )
                
        elif selection == "reply":
            param = {"from": form_json["message"]["blocks"][1]["fields"][1]["text"].split("|")[1].replace(">", ""),
                    "to": form_json["message"]["blocks"][1]["fields"][0]["text"].split("|")[1].replace(">", ""),
                    "subject": form_json["message"]["blocks"][1]["fields"][2]["text"].split("\n")[1]}
            open_dialog = bot.dialog_open(
                trigger_id=form_json["trigger_id"],
                dialog={
                    "title": "Enter the reply",
                    "submit_label": "Submit",
                    "callback_id": user_id,
                    "state": json.dumps(param),
                    "elements": [
                            {
                            "label": "Reply",
                            "name": "reply_email",
                            "type": "textarea",
                            "hint": "Provide the email body.",
                            }
                
                    ]
                }
            )
        elif selection == "completed":
            # Change the assignment footer to completed
            message_block = form_json["message"]["blocks"]
            pprint(message_block)
            completed_by = bot.users_info(
                user=user_id
            )["user"]["name"]
            message_block[4]["elements"].clear()
            message_block[4]["elements"] = [{"text": f":eyes: Completed by @{completed_by}", "type": "mrkdwn", "verbatim": False}]
            del message_block[2]

            # Delete the original message in the DM
            bot.chat_delete(
                channel= form_json["channel"]["id"],
                ts= form_json["message"]["ts"]
            )

            #Move to the archive channel
            bot.chat_postMessage(
                channel= archive_channel,
                text = "",
                blocks=message_block
            )


    # Handle the dialog submissions        
    elif form_json["type"] == "dialog_submission":
        submission = form_json["submission"]
        # print(submission)

        # Handle email assignment
        if list(submission.keys())[0] == "email_assignee":
            assignee_id = submission["email_assignee"]
            assignee_username = bot.users_info(
                user=assignee_id
            )["user"]["name"]
            

            
            @app.after_this_response
            def do_after():
                submission_json = json.loads(form_json["state"])
                # Open conversation with the user
                im_id = bot.conversations_open(
                    users = assignee_id
                )["channel"]["id"]

                # Move the message to the assigned users im
                # Remove assign button
                submission_json[2]["elements"].clear()
                submission_json[2]["elements"] = [
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
                            "text": ":done:Completed"
                        },
                        "style": "primary",
                        "value": "completed"
                    },
                ]

                # Move the message to the assigned users im
                if len(submission_json) == 5:
                    submission_json[4]["elements"].clear()
                    submission_json[4]["elements"] = [
                            {
                                "type": "mrkdwn",
                                "text": f"👀 Assigned to: @{assignee_username}"
                            },
                    ]
                else:
                    submission_json += [{
                    "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"👀 Assigned to: @{assignee_username}"
                            }
                        ]
                    }]
                res = bot.chat_postMessage(
                    channel=im_id,
                    text="",
                    blocks=submission_json
                )

                # Delete the previous message once assigned
                bot.chat_delete(
                    channel=form_json["channel"]["id"],
                    ts = form_json["callback_id"]
                )
        elif list(submission.keys())[0] == "fax_assignee":
            assignee_id = submission["fax_assignee"]
            assignee_username = bot.users_info(
                user=assignee_id
            )["user"]["name"]
            
            @app.after_this_response
            def do_after():
                submission_json = json.loads(form_json["state"])
                # Open conversation with the user
                im_id = bot.conversations_open(
                    users = assignee_id
                )["channel"]["id"]



                submission_json[2]["elements"].clear()
                submission_json[2]["elements"] = [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": ":bust_in_silhouette:Assign"
                        },
                        "style": "primary",
                        "value": "assign_fax"
                    },                    
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": ":done:Completed"
                        },
                        "style": "primary",
                        "value": "completed"
                    },
                ]

                # Move the message to the assigned users im
                if len(submission_json) == 5:
                    submission_json[4]["elements"].clear()
                    submission_json[4]["elements"] = [
                            {
                                "type": "mrkdwn",
                                "text": f"👀 Assigned to: @{assignee_username}"
                            },
                    ]
                else:
                    submission_json += [{
                    "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"👀 Assigned to: @{assignee_username}"
                            }
                        ]
                    }]
                res = bot.chat_postMessage(
                    channel=im_id,
                    text="",
                    blocks=submission_json
                )

                # Delete the previous message once assigned
                bot.chat_delete(
                    channel=form_json["channel"]["id"],
                    ts = form_json["callback_id"]
                )

        elif list(submission.keys())[0] == "reply_email":
            body = submission["reply_email"]
            submission_json = json.loads(form_json["state"])
            
            @app.after_this_response
            def do_after():
                
                # Reply to the email
                reply(from_email= submission_json["from"],
                        to=submission_json["to"],
                        subject=submission_json["subject"],
                        content=body)
    
    return make_response("", 200)

@app.route("/events", methods=["POST"])
def events_handler():
    payload = request.json
    
    @app.after_this_response
    def do_after():
        try:
            if payload["event"]["type"] == "message" and payload["event"]["user"] != "U016KJJQN0Y":
                # pprint(payload)
                # Get the file link and message ts
                url = payload["event"]["files"][0]["url_private"]
                ts = payload["event"]["ts"]
                channel = payload["event"]["channel"]
                text = payload["event"]["text"]

                # Delete the original message
                user.chat_delete(
                    channel= channel,
                    ts=ts
                )

                # Post the message with the fax and added blocks
                bot.chat_postMessage(
                    channel=channel,
                    blocks = [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*You have a new fax:fax:*"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Details*: {text}\n\n *Fax:* <{url}|link>"
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
                                    "value": "assign_fax"
                                }
                            ]
                        }
                    ]
                )
        except KeyError:
            print("Invalid event")
    return make_response("", 200)

    # return payload["challenge"]

def post_unread():
    unread_messages = fetch_unread()
    if unread_messages:
        for msg in unread_messages:
            res = bot.chat_postMessage(
                channel = '#faxtoslack',
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
                            }
                        ]
                    }
                ]
            )
            break


if __name__ == "__main__":
    # post_unread()
    app.run(debug=True)
    
