import traceback
from werkzeug.wsgi import ClosingIterator
from slack import WebClient
from pprint import pprint
import configparser

################### -CONFIGURATION- ##########################
config = configparser.ConfigParser()
config.read("config.ini")

BOT_TOKEN = config.get("SLACK", "BOT_TOKEN")

bot = WebClient(token=BOT_TOKEN)

# Fax members
# fax_members = ["Amberley Wilson", "Stacey", "Jason", "Candi Smith"]
fax_members = ["james couldron"]


class AfterThisResponse:
    def __init__(self, app=None):
        self.callbacks = []
        if app:
            self.init_app(app)

    def __call__(self, callback):
        self.callbacks.append(callback)
        return callback

    def init_app(self, app):
        # install extensioe
        app.after_this_response = self

        # install middleware
        app.wsgi_app = AfterThisResponseMiddleware(app.wsgi_app, self)

    def flush(self):
        try:
            for fn in self.callbacks:
                try:
                    fn()
                except Exception:
                    traceback.print_exc()
        finally:
            self.callbacks = []


class AfterThisResponseMiddleware:
    def __init__(self, application, after_this_response_ext):
        self.application = application
        self.after_this_response_ext = after_this_response_ext

    def __call__(self, environ, start_response):
        iterator = self.application(environ, start_response)
        try:
            return ClosingIterator(
                iterator, [self.after_this_response_ext.flush])
        except Exception:
            traceback.print_exc()
            return iterator


def get_user_id(username):
    members = bot.users_list()["members"]
    if members:
        for member in members:
            if member["profile"]["display_name"] == username:
                return member["id"]


def get_member_block(name):
    member_block = []
    try:
        if name == "fax":
            for member in fax_members:
                member_block.append(
                    {
                        "label": member,
                        "value": get_user_id(member)
                    },
                )
        else:
            for member in bot.users_list()["members"]:

                if not member["is_bot"]:
                    if member["profile"]["display_name"] != "":
                        if "bot" not in member["profile"]["display_name"].lower(
                        ):
                            member_id = member["id"]
                            member_block.append(
                                {
                                    "label": member["profile"]["display_name"],
                                    "value": member_id
                                },
                            )
    except Exception as e:
        print(e)
    return member_block

# pprint(get_member_block("email"))
