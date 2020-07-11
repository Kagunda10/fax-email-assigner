import traceback
from werkzeug.wsgi import ClosingIterator
from slack import WebClient

# BOT_TOKEN = "xoxb-899759167666-1240407393364-L6Rox22GlanzoNEBZnYuEJo4"
BOT_TOKEN = "xoxb-535944217620-1223630838033-UAKWKPtfNzKjv1VGuYYMFOOr"

bot = WebClient(token=BOT_TOKEN)


# Fax members
# fax_members = ["Amberley Wilson", "Candi Smith", "Stacey", "Jason"]
fax_members= ["James C", "caleb njiiri"] 
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
            return ClosingIterator(iterator, [self.after_this_response_ext.flush])
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
                member_id = member["id"]
                member_block.append(
                                {
                                    "label": member["profile"]["display_name"],
                                    "value": member_id
                                },
                )
    return member_block  
