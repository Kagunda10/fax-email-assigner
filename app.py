'''
TODO
- Fetch the list of usernames from google sheets 
'''

from slack import WebClient
from main import  reply
from flask import Flask, request, jsonify, make_response
import configparser
from pprint import pprint
import json
from utils import AfterThisResponse, get_member_block


################### -CONFIGURATION- ##########################
config = configparser.ConfigParser()
config.read("config.ini")

BOT_TOKEN = config.get("SLACK", "BOT_TOKEN")
USER_TOKEN = config.get("SLACK", "USER_TOKEN")
archive_channel = "#" + config.get("SLACK", "ARCHIVE")
bot_id = config.get("SLACK", "BOT_ID")
email_channel = "#" + config.get("SLACK", "EMAIL")
fax_channel = "#" + config.get("SLACK", "FAX")

bot = WebClient(token=BOT_TOKEN)
user = WebClient(token=USER_TOKEN)

fax_members_block = get_member_block("fax")
email_members_block = get_member_block("email")

app = Flask(__name__)
AfterThisResponse(app)
    
@app.route("/message_actions", methods=["POST"])
def interactivity():
    try:
        # Parse the request payload
        form_json = json.loads(request.form["payload"])

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
                        "title": "Choose Member",
                        "submit_label": "Submit",
                        "callback_id": form_json["message"]["ts"],
                        "state": json.dumps(form_json["message"]["blocks"]),
                        "elements": [
                            {
                                "label": "Member's Name",
                                "type": "select",
                                "name": "email_assignee",
                                "placeholder": "Choose Member",
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
                        "title": "Choose Member",
                        "submit_label": "Submit",
                        "callback_id": form_json["message"]["ts"],
                        "state": json.dumps(form_json["message"]["blocks"]),
                        "elements": [
                            {
                                "label": "Member's Name",
                                "type": "select",
                                "name": "fax_assignee",
                                "placeholder": "Choose Member",
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
            elif selection == "fax_completed":

                # Change the assignment footer to completed
                message_block = form_json["message"]["blocks"]
                completed_by = bot.users_info(
                    user=user_id
                )["user"]["name"]

                try:
                    if message_block[4]:
                        message_block[4]["elements"].clear()
                        message_block[4]["elements"] = [{"text": f":eyes: Completed by @{completed_by}", "type": "mrkdwn", "verbatim": False}]
                except IndexError:
                    message_block +=  [{
                        "type": "divider"
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f":eyes: Completed by @{completed_by}"
                                }
                            ]
                        }]
                
                del message_block[2]

                try:
                    # Delete the original message in the DM
                    bot.chat_delete(
                        channel= form_json["channel"]["id"],
                        ts= form_json["message"]["ts"]
                    )
                except Exception as e:
                    user.chat_delete(
                        channel= form_json["channel"]["id"],
                        ts= form_json["message"]["ts"]
                    )   
                #Move to the archive channel
                bot.chat_postMessage(
                    channel= archive_channel,
                    text = "",
                    blocks=message_block
                )
            elif selection == "email_completed":
                # Change the assignment footer to completed
                message_block = form_json["message"]["blocks"]
                completed_by = bot.users_info(
                    user=user_id
                )["user"]["name"]

                try:
                    if message_block[5]:
                        message_block[5]["elements"].clear()
                        message_block[5]["elements"] = [{"text": f":eyes: Completed by @{completed_by}", "type": "mrkdwn", "verbatim": False}]
                except IndexError:
                    message_block +=  [{
                        "type": "divider"
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f":eyes: Completed by @{completed_by}"
                                }
                            ]
                        }]
                
                del message_block[3]

                try:
                    # Delete the original message in the DM
                    bot.chat_delete(
                        channel= form_json["channel"]["id"],
                        ts= form_json["message"]["ts"]
                    )
                except Exception as e:
                    user.chat_delete(
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
                    submission_json[3]["elements"].clear()
                    submission_json[3]["elements"] = [
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
                        },
                    ]

                    # Move the message to the assigned users im
                    if len(submission_json) == 6:
                        submission_json[5]["elements"].clear()
                        submission_json[5]["elements"] = [
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
                    user.chat_delete(
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
                                "text": ":white_check_mark:Complete"
                            },
                            "style": "primary",
                            "value": "fax_completed"
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
                    user.chat_delete(
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
        
    except Exception as e:
        print(e)
    return make_response("", 200)

@app.route("/events", methods=["POST"])
def events_handler():
    payload = request.json
    # pprint(payload)
    # try:
    #     @app.after_this_response
    #     def do_after():

    #         if payload["event"]["type"] == "message":
    #             try:
    #                 if payload["event"]["user"] != bot_id:
    #                     url = payload["event"]["files"][0]["url_private"]
    #                     channel = fax_channel

    #                     # Post the message with the fax and added blocks
    #                     res = bot.chat_postMessage(
    #                         channel=channel,
    #                         blocks = [
    #                             {
    #                                 "type": "section",
    #                                 "text": {
    #                                     "type": "mrkdwn",
    #                                     "text": "*You have a new fax:fax:*"
    #                                 }
    #                             },
    #                             {
    #                                 "type": "section",
    #                                 "text": {
    #                                     "type": "mrkdwn",
    #                                     "text": f"*Fax:* <{url}|link>"
    #                                 }
    #                             },
    #                             {
    #                                 "type": "actions",
    #                                 "elements": [
    #                                     {
    #                                         "type": "button",
    #                                         "text": {
    #                                             "type": "plain_text",
    #                                             "emoji": True,
    #                                             "text": ":bust_in_silhouette:Assign"
    #                                         },
    #                                         "style": "primary",
    #                                         "value": "assign_fax"
    #                                     },                    
    #                                     {
    #                                         "type": "button",
    #                                         "text": {
    #                                             "type": "plain_text",
    #                                             "emoji": True,
    #                                             "text": ":white_check_mark:Complete"
    #                                         },
    #                                         "style": "primary",
    #                                         "value": "fax_completed"
    #                                     }
    #                                 ]
    #                             }
    #                         ]
    #                     )
    #             except KeyError:
    #                 print("Invalid event")
    # except Exception as e:
    #     print(e)
    # return make_response("", 200)

    return payload["challenge"]

if __name__ == "__main__":
    app.run(debug=True)
    
