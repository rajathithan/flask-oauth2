import json, logging, httplib2
from flask import current_app, Flask, redirect, request, session, url_for, render_template
from oauth2client.contrib.flask_util import UserOAuth2

oauth2 = UserOAuth2()

def create_app(config, debug=False, testing=False, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(config)

    app.debug = debug
    app.testing = testing

    # config overrides
    if config_overrides:
        app.config.update(config_overrides)

    # Configure logging
    if not app.testing:
        logging.basicConfig(level=logging.INFO)

    # Setup the data model.
    with app.app_context():
        model = get_model()
        model.init_app(app)

    # [START init_app]
    # Initalize the OAuth2 helper.
    oauth2.init_app(
        app,
        scopes=['email', 'profile'],
        authorize_callback=_request_user_info)
    # [END init_app]

    # [START logout]
    # Add a logout handler.
    @app.route('/logout')
    def logout():
        # Delete the user's profile and the credentials stored by oauth2.
        del session['profile']
        session.modified = True
        oauth2.storage.delete()
        return redirect(request.referrer or '/')
    # [END logout]

    @app.route("/")
    def index():
        return render_template("base.html")

    @app.errorhandler(500)
    def server_error(e):
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500
    return app


def get_model():
    model_backend = current_app.config['DATA_BACKEND']
    if model_backend == 'sqlLite':
        from . import model_sqlLite
        model = model_sqlLite
    else:
        raise ValueError(
            "No appropriate databackend configured. "
            "Please specify datastore, cloudsql, or mongodb")

    return model
    

# [START request_user_info]
def _request_user_info(credentials):
    """
    Makes an HTTP request to the Google OAuth2 API to retrieve the user's basic
    profile information, including full name and photo, and stores it in the
    Flask session.
    """
    http = httplib2.Http()
    credentials.authorize(http)
    resp, content = http.request(
        'https://www.googleapis.com/oauth2/v3/userinfo')

    if resp.status != 200:
        current_app.logger.error(
            "Error while obtaining user profile: \n%s: %s", resp, content)
        return None
    session['profile'] = json.loads(content.decode('utf-8'))

# [END request_user_info]