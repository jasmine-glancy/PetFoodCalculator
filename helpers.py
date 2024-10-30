"""Contains additional checks and decorators (i.e. is user logged in, login decorator)"""

from flask import Flask, session, redirect, url_for
from functools import wraps

# Configure application
app = Flask(__name__)

def clear_variable_list():
    """Clear all pet session variables, code reformatting suggested by CoPilot"""
    
    for variable in list(session.keys()):
        if variable != "user_id":
            session.pop(variable, None)
   

def login_required(f):
    """Requires a user to login to access the routes decorated"""
    
    @wraps(f)
    def decorated_funtion(*args, **kwargs):
        if session.get("user_id") == None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    
    return decorated_funtion

# ----------------- Custom Jinja Template Filters ----------------- #

@app.template_filter("capitalize")
def capitalize(username):
    cap_username = username.title()
    
    return cap_username