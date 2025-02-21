# -*- coding: UTF-8 -*-
from gevent import monkey

monkey.patch_all(thread=True)

# Import Standary Python Libraries
import socket
import os
import subprocess
import time
import sys
import hashlib
import logging
import datetime
import json
import uuid
import time
import random

# Import 3rd Party Libraries
from flask import Flask, redirect, request, abort, flash, current_app, session
from flask.wrappers import Request
from flask_session import Session
from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
    login_required,
    current_user,
    roles_required,
    uia_email_mapper,
)
from flask_security.signals import user_registered
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_migrate import Migrate, upgrade, init, migrate
from flaskext.markdown import Markdown
from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS
from flask_babel import Babel
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import exc

import redis

# Import Paths
cwp = sys.path[0]
sys.path.append(cwp)
sys.path.append("./classes")

# ----------------------------------------------------------------------------#
# Configuration Imports
# ----------------------------------------------------------------------------#
try:
    from conf import config

except:
    from dotenv import load_dotenv

    class configObj:
        pass

    load_dotenv()
    config = configObj()

    config.dbLocation = os.getenv("OSP_CORE_DB")
    config.redisHost = os.getenv("OSP_REDIS_HOST")
    config.redisPort = os.getenv("OSP_REDIS_PORT")
    config.redisPassword = os.getenv("OSP_REDIS_PASSWORD")
    config.secretKey = os.getenv("OSP_CORE_SECRETKEY")
    config.passwordSalt = os.getenv("OSP_CORE_PASSWORD_SALT")
    config.allowRegistration = os.getenv("OSP_CORE_ALLOWREGISTRATION").lower() in (
        "true",
        "1",
        "t",
    )
    config.requireEmailRegistration = os.getenv(
        "OSP_CORE_REQUIREEMAILREGISTRATION"
    ).lower() in ("true", "1", "t")
    config.debugMode = os.getenv("OSP_CORE_DEBUG").lower() in ("true", "1", "t")
    config.log_level = os.getenv("OSP_CORE_LOGLEVEL")
    config.ejabberdAdmin = os.getenv("OSP_EJABBERD_ADMIN")
    config.ejabberdPass = os.getenv("OSP_EJABBERD_PASSWORD")
    config.ejabberdHost = os.getenv("OSP_EJABBERD_ADMINDOMAIN")
    config.smtpSendAs = os.getenv("OSP_SMTP_SENDAS")
    config.smtpServerAddress = os.getenv("OSP_SMTP_SERVERADDRESS")
    config.smtpServerPort = os.getenv("OSP_SMTP_SERVERPORT")
    config.smtpEncryption = os.getenv("OSP_SMTP_ENCRYPTION")
    config.smtpUsername = os.getenv("OSP_SMTP_USERNAME")
    config.smtpPassword = os.getenv("OSP_SMTP_PASSWORD")
    if os.getenv("OSP_XMPP_DOMAIN") is not None:
        config.ospXMPPDomain = os.getenv("OSP_XMPP_DOMAIN")
    if os.getenv("OSP_EJABBERD_RPCHOST") is not None:
        config.ejabberdServer = os.getenv("OSP_EJABBERD_RPCHOST")
    if os.getenv("OSP_RECAPTCHA_ENABLED") is not None:
        config.RECAPTCHA_ENABLED = os.getenv("OSP_RECAPTCHA_ENABLED").lower() in (
            "true",
            "1",
            "t",
        )
    if os.getenv("OSP_RECAPTCHA_SITEKEY") is not None:
        config.RECAPTCHA_SITE_KEY = os.getenv("OSP_RECAPTCHA_SITEKEY")
    if os.getenv("OSP_RECAPTCHA_SECRETKEY") is not None:
        config.RECAPTCHA_SECRET_KEY = os.getenv("OSP_RECAPTCHA_SECRETKEY")

    if os.getenv("OSP_SENTRYIO_ENABLED") is not None:
        config.sentryIO_Enabled = os.getenv("OSP_SENTRYIO_ENABLED").lower() in (
            "true",
            "1",
            "t",
        )
    if os.getenv("OSP_SENTRYIO_DSN") is not None:
        config.sentryIO_DSN = os.getenv("OSP_SENTRYIO_DSN")
    if os.getenv("OSP_SENTRYIO_ENVIRONMENT") is not None:
        config.sentryIO_Environment = os.getenv("OSP_SENTRYIO_ENVIRONMENT")

# ----------------------------------------------------------------------------#
# Global Vars Imports
# ----------------------------------------------------------------------------#
from globals import globalvars

# Add Manual OSP XMPP Domain for those who need it
if hasattr(config, "ospXMPPDomain"):
    if config.ospXMPPDomain != "" and config.ospXMPPDomain != None:
        globalvars.defaultChatDomain = config.ospXMPPDomain

# ----------------------------------------------------------------------------#
# App Configuration Setup
# ----------------------------------------------------------------------------#
# Generate a Random UUID for Interprocess Handling
processUUID = str(uuid.uuid4())
globalvars.processUUID = processUUID
####### Sentry.IO Metrics and Error Logging (Disabled by Default) #######
if hasattr(config, "sentryIO_Enabled") and hasattr(config, "sentryIO_DSN"):
    if config.sentryIO_Enabled:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration

        sentryEnv = "Not Specified"
        if hasattr(config, "sentryIO_Environment"):
            sentryEnv = config.sentryIO_Environment

        sentry_sdk.init(
            dsn=config.sentryIO_DSN,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0,
            release=globalvars.version,
            environment=sentryEnv,
            server_name=globalvars.processUUID,
            _experiments={
                "profiles_sample_rate": 1.0,
            }
        )

coreNginxRTMPAddress = "127.0.0.1"

# Initialize RedisURL Variable
RedisURL = None
if config.redisPassword == "" or config.redisPassword is None:
    RedisURL = "redis://" + config.redisHost + ":" + str(config.redisPort)
else:
    RedisURL = (
        "redis://:"
        + config.redisPassword
        + "@"
        + config.redisHost
        + ":"
        + str(config.redisPort)
    )

app = Flask(__name__)

# Flask App Environment Setup
app.debug = config.debugMode
app.wsgi_app = ProxyFix(app.wsgi_app)
app.jinja_env.cache = {}
app.config["WEB_ROOT"] = globalvars.videoRoot
app.config["SQLALCHEMY_DATABASE_URI"] = config.dbLocation
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_MAX_OVERFLOW"] = -1
app.config["SQLALCHEMY_POOL_RECYCLE"] = 300
app.config["SQLALCHEMY_POOL_TIMEOUT"] = 600
app.config["MYSQL_DATABASE_CHARSET"] = "utf8"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "encoding": "utf8",
    "pool_use_lifo": "False",
    "pool_size": 10,
    "pool_pre_ping": True,
}
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_NAME"] = "ospSession"
app.config["SECRET_KEY"] = config.secretKey
app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
app.config["SECURITY_PASSWORD_SALT"] = config.passwordSalt
app.config["SECURITY_REGISTERABLE"] = config.allowRegistration
app.config["SECURITY_RECOVERABLE"] = True
app.config["SECURITY_CONFIRMABLE"] = config.requireEmailRegistration
app.config["SECURITY_SEND_REGISTER_EMAIL"] = config.requireEmailRegistration
app.config["SECURITY_CHANGABLE"] = True
app.config["SECURITY_TRACKABLE"] = True
app.config["SECURITY_EMAIL_SENDER"] = config.smtpSendAs
app.config["MAIL_DEFAULT_SENDER"] = config.smtpSendAs
app.config["MAIL_SERVER"] = config.smtpServerAddress
app.config["MAIL_PORT"] = int(config.smtpServerPort)
if config.smtpEncryption == "ssl":
    app.config["MAIL_USE_SSL"] = True
else:
    app.config["MAIL_USE_SSL"] = False
if config.smtpEncryption == "tls":
    app.config["MAIL_USE_TLS"] = True
else:
    app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = config.smtpUsername
app.config["MAIL_PASSWORD"] = config.smtpPassword
app.config["SECURITY_TWO_FACTOR_ENABLED_METHODS"] = ["authenticator"]
app.config["SECURITY_TWO_FACTOR"] = True
app.config["SECURITY_TWO_FACTOR_ALWAYS_VALIDATE"] = False
app.config["SECURITY_TWO_FACTOR_LOGIN_VALIDITY"] = "7 days"
app.config["SECURITY_TOTP_SECRETS"] = {"1": config.secretKey}
app.config["SECURITY_FLASH_MESSAGES"] = True
app.config["UPLOADED_PHOTOS_DEST"] = app.config["WEB_ROOT"] + "images"
app.config["UPLOADED_STICKERS_DEST"] = app.config["WEB_ROOT"] + "images"
app.config["UPLOADED_DEFAULT_DEST"] = app.config["WEB_ROOT"] + "images"
app.config["SECURITY_POST_LOGIN_VIEW"] = "/"
app.config["SECURITY_POST_LOGOUT_VIEW"] = "/"
app.config["SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED"] = (
    "Username or Email Already Associated with an Account",
    "error",
)
app.config["SECURITY_MSG_INVALID_PASSWORD"] = ("Invalid Username or Password", "error")
app.config["SECURITY_MSG_INVALID_EMAIL_ADDRESS"] = (
    "Invalid Username or Password",
    "error",
)
app.config["SECURITY_MSG_USER_DOES_NOT_EXIST"] = (
    "Invalid Username or Password",
    "error",
)
app.config["SECURITY_MSG_DISABLED_ACCOUNT"] = ("Account Disabled", "error")
app.config["VIDEO_UPLOAD_TEMPFOLDER"] = app.config["WEB_ROOT"] + "videos/temp"
app.config["VIDEO_UPLOAD_EXTENSIONS"] = ["PNG", "MP4"]
app.config["broker_url"] = RedisURL
app.config["result_backend"] = RedisURL
app.config["MAX_CONTENT_LENGTH"] = 4000000000

# ----------------------------------------------------------------------------#
# Monkey Fix Flask-Restx issue (https://github.com/pallets/flask/issues/4552#issuecomment-1109785314)
# ----------------------------------------------------------------------------#
class AnyJsonRequest(Request):
    def on_json_loading_failed(self, e):
        if e is not None:
            return super().on_json_loading_failed(e)


app.request_class = AnyJsonRequest

# ----------------------------------------------------------------------------#
# Set Logging Configuration
# ----------------------------------------------------------------------------#
if __name__ != "__main__":
    loglevel = logging.WARNING
    if hasattr(config, "log_level"):
        logOptions = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        if config.log_level in logOptions:
            loglevel = logOptions[config.log_level]
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(loglevel)

# Initialize Recaptcha
if hasattr(config, "RECAPTCHA_ENABLED"):
    if config.RECAPTCHA_ENABLED is True:
        app.logger.info(
            {
                "level": "info",
                "message": "REPATCHA_ENABLED set to True. Initializing Recaptcha",
            }
        )
        globalvars.recaptchaEnabled = True
        try:
            app.config["RECAPTCHA_PUBLIC_KEY"] = config.RECAPTCHA_SITE_KEY
            app.config["RECAPTCHA_PRIVATE_KEY"] = config.RECAPTCHA_SECRET_KEY
        except:
            app.logger.warning(
                {
                    "level": "warning",
                    "message": "Recaptcha Enabled, but missing Site Key or Secret Key in config.py.  Disabling ReCaptcha",
                }
            )
            globalvars.recaptchaEnabled = False

# ----------------------------------------------------------------------------#
# Modal Imports
# ----------------------------------------------------------------------------#
app.logger.info({"level": "info", "message": "Importing Database Classes"})
from classes import Stream
from classes import Channel
from classes import dbVersion
from classes import RecordedVideo
from classes import topics
from classes import settings
from classes import banList
from classes import Sec
from classes import upvotes
from classes import apikey
from classes import views
from classes import comments
from classes import invites
from classes import webhook
from classes import logs
from classes import subscriptions
from classes import notifications
from classes import stickers
from classes import panel
from classes import hub

# ----------------------------------------------------------------------------#
# Function Imports
# ----------------------------------------------------------------------------#
app.logger.info({"level": "info", "message": "Importing Function"})
from functions import database
from functions import system
from functions import securityFunc
from functions import votes
from functions import webhookFunc
from functions.ejabberdctl import ejabberdctl
from functions import cachedDbCalls
from functions.scheduled_tasks import message_tasks
from functions import celeryFunc

# ----------------------------------------------------------------------------#
# Begin App Initialization
# ----------------------------------------------------------------------------#

# Initialize Flask-BabelEx
app.logger.info({"level": "info", "message": "Initializing Flask-BabelEx"})
babel = Babel(app)

# Initialize Flask-Limiter
app.logger.info({"level": "info", "message": "Importing Flask-Limiter"})
app.config["RATELIMIT_STORAGE_URL"] = RedisURL
from classes.shared import limiter

limiter.init_app(app)

# Initialize Redis
app.logger.info({"level": "info", "message": "Initializing Redis"})
if config.redisPassword == "" or config.redisPassword is None:
    r = redis.Redis(host=config.redisHost, port=config.redisPort)
    app.config["SESSION_REDIS"] = r
else:
    r = redis.Redis(
        host=config.redisHost, port=config.redisPort, password=config.redisPassword
    )
    app.config["SESSION_REDIS"] = r
r.flushdb()

# Initialize Flask-SocketIO
app.logger.info({"level": "info", "message": "Initializing Flask-SocketIO"})
from classes.shared import socketio

if config.redisPassword == "" or config.redisPassword is None:
    socketio.init_app(
        app,
        logger=False,
        engineio_logger=False,
        message_queue="redis://" + config.redisHost + ":" + str(config.redisPort),
        ping_interval=20,
        ping_timeout=40,
        cookie=None,
        cors_allowed_origins=[],
    )
else:
    socketio.init_app(
        app,
        logger=False,
        engineio_logger=False,
        message_queue="redis://:"
        + config.redisPassword
        + "@"
        + config.redisHost
        + ":"
        + str(config.redisPort),
        ping_interval=20,
        ping_timeout=40,
        cookie=None,
        cors_allowed_origins=[],
    )

# Begin Database Initialization
app.logger.info({"level": "info", "message": "Loading Database Object"})
from classes.shared import db

db.init_app(app)
db.app = app
migrateObj = Migrate(app, db)

# Handle Session Rollback Issues
@app.errorhandler(exc.SQLAlchemyError)
def handle_db_exceptions(error):
    app.logger.error(error)
    db.session.rollback()


# Initialize Flask-Session
app.logger.info({"level": "info", "message": "Initializing Flask-Session"})
Session(app)

# Initialize Flask-CORS Config
app.logger.info({"level": "info", "message": "Initializing Flask-CORS"})
cors = CORS(app, resources={r"/apiv1/*": {"origins": "*"}})

# Initialize Flask-Caching
app.logger.info({"level": "info", "message": "Performing Flask Caching Initialization"})

from classes.shared import cache

redisCacheOptions = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_KEY_PREFIX": "OSP_FC",
    "CACHE_REDIS_HOST": config.redisHost,
    "CACHE_REDIS_PORT": config.redisPort,
}
if config.redisPassword != "" and config.redisPassword is not None:
    redisCacheOptions["CACHE_REDIS_PASSWORD"] = config.redisPassword
cache.init_app(app, config=redisCacheOptions)

# Initialize Debug Toolbar
app.logger.info({"level": "info", "message": "Initializing Flask-Debug"})
toolbar = DebugToolbarExtension(app)

# Initialize Flask-Security
app.logger.info({"level": "info", "message": "Initializing Flask-Security"})
try:
    sysSettings = cachedDbCalls.getSystemSettings()
    app.config["SECURITY_TOTP_ISSUER"] = sysSettings.siteName
except:
    app.config["SECURITY_TOTP_ISSUER"] = "OSP"
    app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = [
        {"email": {"mapper": uia_email_mapper, "case_insensitive": True}}
    ]

user_datastore = SQLAlchemyUserDatastore(db, Sec.User, Sec.Role)
security = Security(
    app,
    user_datastore,
    register_form=Sec.ExtendedRegisterForm,
    confirm_register_form=Sec.ExtendedConfirmRegisterForm,
    login_form=Sec.OSPLoginForm,
)

# Initialize Flask-Uploads
app.logger.info({"level": "info", "message": "Initializing Flask-Uploads"})
photos = UploadSet("photos", IMAGES)
stickerUploads = UploadSet("stickers", IMAGES)
configure_uploads(app, (photos, stickerUploads))

# Initialize Flask-Markdown
app.logger.info({"level": "info", "message": "Initializing Flask-Markdown"})
md = Markdown(app, extensions=["tables"])

# Initialize ejabberdctl
app.logger.info(
    {"level": "info", "message": "Initializing ejabberd XML-RPC connection"}
)
ejabberd = None

if hasattr(config, "ejabberdServer"):
    globalvars.ejabberdServer = config.ejabberdServer

try:
    ejabberd = ejabberdctl(
        config.ejabberdHost,
        config.ejabberdAdmin,
        config.ejabberdPass,
        server=globalvars.ejabberdServer,
    )
    app.logger.info(ejabberd.status())
except Exception as e:
    app.logger.error(
        {"level": "error", "message": "ejabberdctl failed to load: " + str(e)}
    )

# Loop Check if OSP DB Init is Currently Being Handled by and Process
#OSP_DB_INIT_HANDLER = None
#while OSP_DB_INIT_HANDLER != globalvars.processUUID:
#    OSP_DB_INIT_HANDLER = r.get("OSP_DB_INIT_HANDLER")
#    if OSP_DB_INIT_HANDLER != None:
#        OSP_DB_INIT_HANDLER = OSP_DB_INIT_HANDLER.decode("utf-8")
#    else:
#        r.set("OSP_DB_INIT_HANDLER", globalvars.processUUID)
#        time.sleep(random.random())

# Once Attempt Database Load and Validation
app.logger.info(
    {"level": "info", "message": "Performing Initial Database Initialization"}
)
try:
    database.init(app, user_datastore)
except Exception as e:
    db.session.rollback()
    app.logger.error(
        {
            "level": "error",
            "message": "DB Load Fail due to Upgrade or Issues: " + str(e),
        }
    )
# Clear Process from OSP DB Init
r.delete("OSP_DB_INIT_HANDLER")

if r.get("OSP_SYSTEM_FIXES_HANDLER") is None:
    # Perform System Fixes
    r.set("OSP_SYSTEM_FIXES_HANDLER", globalvars.processUUID, ex=60)
    app.logger.info({"level": "info", "message": "Performing OSP System Fixes"})
    try:
        system.systemFixes(app)
    except:
        app.logger.warning(
            {
                "level": "warning",
                "message": "Unable to perform System Fixes.  May be first run or DB Issue.",
            }
        )
        r.delete("OSP_SYSTEM_FIXES_HANDLER")
else:
    app.logger.info(
        {
            "level": "info",
            "message": "Skipping System Fixes; they are already in Progress, or already done.",
        }
    )

if r.get("OSP_XMPP_INIT_HANDLER") is None:
    # Perform XMPP Sanity Check
    r.set("OSP_XMPP_INIT_HANDLER", globalvars.processUUID, ex=60)
    app.logger.info({"level": "info", "message": "Performing XMPP Sanity Checks"})
    from functions import xmpp

    try:
        # The XMPP sanity check can sometimes fail because an invalid transaction has not been rolled back.
        # Since db.session.rollback() just silently passes if there's nothing to roll back, we can put this here.
        db.session.rollback()
        results = xmpp.sanityCheck()
    except Exception as e:
        db.session.rollback()   # Use db.session.rollback() here as well, in case of a hanging invalid transaction.
        app.logger.error(
            {"level": "error", "message": "XMPP Sanity Check Failed - " + str(e)}
        )
        r.delete("OSP_XMPP_INIT_HANDLER")
else:
    app.logger.info(
        {
            "level": "info",
            "message": "Process Skipping XMPP Sanity Check - Already in Progress or Recently Run",
        }
    )

# Checking OSP-Edge Redirection Conf File
app.logger.info({"level": "info", "message": "Initializing OSP-Edge Redirection File"})
try:
    system.checkOSPEdgeConf()
except:
    app.logger.warning(
        {
            "level": "warning",
            "message": "Unable to initialize OSP Edge Conf.  May be first run or DB Issue.",
        }
    )


# Initialize oAuth
app.logger.info({"level": "info", "message": "Initializing OAuth Info"})
from classes.shared import oauth
from functions.oauth import fetch_token

oauth.init_app(app, fetch_token=fetch_token)

try:
    # Register oAuth Providers
    for provider in settings.oAuthProvider.query.all():
        try:
            oauth.register(
                name=provider.name,
                client_id=provider.client_id,
                client_secret=provider.client_secret,
                access_token_url=provider.access_token_url,
                access_token_params=provider.access_token_params
                if (
                    provider.access_token_params != ""
                    and provider.access_token_params is not None
                )
                else None,
                authorize_url=provider.authorize_url,
                authorize_params=provider.authorize_params
                if (
                    provider.authorize_params != ""
                    and provider.authorize_params is not None
                )
                else None,
                api_base_url=provider.api_base_url,
                client_kwargs=json.loads(provider.client_kwargs)
                if (provider.client_kwargs != "" and provider.client_kwargs is not None)
                else None,
            )

        except Exception as e:
            app.logger.error(
                {
                    "level": "error",
                    "message": "Failed Loading oAuth Provider-"
                    + provider.name
                    + ":"
                    + str(e),
                }
            )
except:
    app.logger.error({"level": "error", "message": "Failed Loading oAuth Providers"})

app.logger.info({"level": "info", "message": "Initializing Flask-Mail"})
# Initialize Flask-Mail
from classes.shared import email

email.init_app(app)
email.app = app
try:
    sysSettings = cachedDbCalls.getSystemSettings()
except:
    app.logger.error({"level": "error", "message": "cachedDbCalls.getSystemSettings() encountered an error, likely due to first time db generation."})

app.config["SERVER_NAME"] = None
try:
    app.config[
        "SECURITY_FORGOT_PASSWORD_TEMPLATE"
    ] = "security/forgot_password.html"
    app.config["SECURITY_LOGIN_USER_TEMPLATE"] = "security/login_user.html"
    app.config["SECURITY_REGISTER_USER_TEMPLATE"] = "security/register_user.html"
    app.config[
        "SECURITY_SEND_CONFIRMATION_TEMPLATE"
    ] = "security/send_confirmation.html"
    app.config["SECURITY_RESET_PASSWORD_TEMPLATE"] = "security/reset_password.html"
    app.config["SECURITY_EMAIL_SUBJECT_PASSWORD_RESET"] = (
        sysSettings.siteName + " - Password Reset Request"
    )
    app.config["SECURITY_EMAIL_SUBJECT_REGISTER"] = (
        sysSettings.siteName + " - Welcome!"
    )
    app.config["SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE"] = (
        sysSettings.siteName + " - Password Reset Notification"
    )
    app.config["SECURITY_EMAIL_SUBJECT_CONFIRM"] = (
        sysSettings.siteName + " - Email Confirmation Request"
    )
except:
    pass

app.logger.info({"level": "info", "message": "Importing Topic Data into Global Cache"})
# Initialize the Topic Cache
try:
    topicQuery = topics.topics.query.all()
    for topic in topicQuery:
        globalvars.topicCache[topic.id] = topic.name
except Exception as e:
    app.logger.info(
        {
            "level": "error",
            "message": "Importing Topic Data into Global Cache Failed: " + str(e),
        }
    )

# Initialize First Theme Overrides
app.logger.info({"level": "info", "message": "Initializing OSP Themes"})
try:
    system.initializeThemes()
except:
    app.logger.error({"level": "error", "message": "Unable to Set Override Themes"})

# Initialize Celery
app.logger.info({"level": "info", "message": "Initializing Celery"})
from classes.shared import celery

celery.conf.broker_url = app.config["broker_url"]
celery.conf.result_backend = app.config["result_backend"]
celery.conf.update(app.config)


class ContextTask(celery.Task):
    """Make celery tasks work with Flask app context"""

    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask

# Import Celery Beat Scheduled Tasks
from functions.scheduled_tasks import scheduler

app.logger.info({"level": "info", "message": "Initializing SocketIO Handlers"})
# ----------------------------------------------------------------------------#
# SocketIO Handler Import
# ----------------------------------------------------------------------------#
from functions.socketio import connections
from functions.socketio import video
from functions.socketio import stream
from functions.socketio import vote
from functions.socketio import invites
from functions.socketio import webhooks
from functions.socketio import edge
from functions.socketio import subscription
from functions.socketio import thumbnail
from functions.socketio import syst
from functions.socketio import xmpp
from functions.socketio import restream
from functions.socketio import rtmp
from functions.socketio import pictures
from functions.socketio import notifications_socketio

app.logger.info({"level": "info", "message": "Initializing Flask Blueprints"})
# ----------------------------------------------------------------------------#
# Blueprint Filter Imports
# ----------------------------------------------------------------------------#
from blueprints.errorhandler import errorhandler_bp
from blueprints.apiv1 import api_v1
from blueprints.root import root_bp
from blueprints.streamers import streamers_bp
from blueprints.profile import profile_bp
from blueprints.channels import channels_bp
from blueprints.topics import topics_bp
from blueprints.play import play_bp
from blueprints.liveview import liveview_bp
from blueprints.clip import clip_bp
from blueprints.upload import upload_bp
from blueprints.settings.settings import settings_bp
from blueprints.oauth import oauth_bp
from blueprints.m3u8 import m3u8_bp

# Register all Blueprints
app.register_blueprint(errorhandler_bp)
app.register_blueprint(api_v1)
app.register_blueprint(root_bp)
app.register_blueprint(channels_bp)
app.register_blueprint(play_bp)
app.register_blueprint(clip_bp)
app.register_blueprint(streamers_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(topics_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(liveview_bp)
app.register_blueprint(oauth_bp)
app.register_blueprint(m3u8_bp)

app.logger.info({"level": "info", "message": "Initializing Template Filters"})
# ----------------------------------------------------------------------------#
# Template Filter Imports
# ----------------------------------------------------------------------------#
from functions import templateFilters

# Initialize Jinja2 Template Filters
templateFilters.init(app)

app.logger.info({"level": "info", "message": "Setting Jinja2 Global Env Functions"})
# ----------------------------------------------------------------------------#
# Jinja 2 Gloabl Environment Functions
# ----------------------------------------------------------------------------#
app.jinja_env.globals.update(
    check_isValidChannelViewer=securityFunc.check_isValidChannelViewer
)
app.jinja_env.globals.update(check_isCommentUpvoted=votes.check_isCommentUpvoted)
app.jinja_env.globals.update(getPanel=templateFilters.getPanel)
app.jinja_env.globals.update(getLiveStream=templateFilters.getLiveStream)
app.jinja_env.globals.update(getPanelStreamList=templateFilters.getPanelStreamList)
app.jinja_env.globals.update(getPanelVideoList=templateFilters.getPanelVideoList)
app.jinja_env.globals.update(getPanelClipList=templateFilters.getPanelClipList)
app.jinja_env.globals.update(getPanelChannelList=templateFilters.getPanelChannelList)

app.logger.info({"level": "info", "message": "Setting Flask Context Processors"})
# ----------------------------------------------------------------------------#
# Context Processors
# ----------------------------------------------------------------------------#
@app.context_processor
def inject_notifications():
    notificationList = []
    messagesListCount = 0
    if current_user.is_authenticated:
        userNotificationQuery = notifications.userNotification.query.filter_by(
            userID=current_user.id
        ).all()
        for entry in userNotificationQuery:
            if entry.read is False:
                notificationList.append(entry)
        notificationList.sort(key=lambda x: x.timestamp, reverse=True)
        messagesListCount = notifications.userMessage.query.filter_by(
            toUserID=current_user.id, read=False
        ).count()
    return dict(notifications=notificationList, messageCount=messagesListCount)


@app.context_processor
def inject_recaptchaEnabled():
    recaptchaEnabled = globalvars.recaptchaEnabled
    return dict(recaptchaEnabled=recaptchaEnabled)


@app.context_processor
def inject_oAuthProviders():

    SystemOAuthProviders = cachedDbCalls.getOAuthProviders()
    return dict(SystemOAuthProviders=SystemOAuthProviders)


@app.context_processor
def inject_sysSettings():

    sysSettings = cachedDbCalls.getSystemSettings()
    allowRegistration = config.allowRegistration
    restartRequired = globalvars.restartRequired
    return dict(
        sysSettings=sysSettings,
        allowRegistration=allowRegistration,
        restartRequired=restartRequired,
    )


@app.context_processor
def inject_ownedChannels():
    if current_user.is_authenticated:
        if current_user.has_role("Streamer"):
            ownedChannels = (
                Channel.Channel.query.filter_by(owningUser=current_user.id)
                .with_entities(
                    Channel.Channel.id,
                    Channel.Channel.channelLoc,
                    Channel.Channel.channelName,
                )
                .all()
            )

            return dict(ownedChannels=ownedChannels)
        else:
            return dict(ownedChannels=[])
    else:
        return dict(ownedChannels=[])


@app.context_processor
def inject_topics():
    topicQuery = cachedDbCalls.getAllTopics()
    return dict(uploadTopics=topicQuery)


@app.context_processor
def inject_static_pages():
    return dict(static_pages=cachedDbCalls.getStaticPages())


app.logger.info({"level": "info", "message": "Initializing Flask Signal Handlers"})
# ----------------------------------------------------------------------------#
# Flask Signal Handlers.
# ----------------------------------------------------------------------------#
@user_registered.connect_via(app)
def user_registered_sighandler(
    app, user, confirm_token, confirmation_token=None, form_data=None
):
    defaultRoleQuery = Sec.Role.query.filter_by(default=True).all()
    for role in defaultRoleQuery:
        user_datastore.add_role_to_user(user, role.name)
    user.authType = 0
    user.xmppToken = str(os.urandom(32).hex())
    user.uuid = str(uuid.uuid4())
    message_tasks.send_webhook.delay("ZZZ", 20, user=user.username)
    app.logger.info(
        {
            "level": "info",
            "message": "New User Registered - "
            + str(user.username)
            + " - "
            + str(user.current_login_ip),
        }
    )
    system.newLog(1, "A New User has Registered - Username:" + str(user.username))
    if config.requireEmailRegistration:
        flash(
            "An email has been sent to the email provided. Please check your email and verify your account to activate."
        )
    db.session.commit()


# ----------------------------------------------------------------------------#
# Additional Handlers.
# ----------------------------------------------------------------------------#
app.logger.info({"level": "info", "message": "Initializing First Request Check"})


@app.before_request
def do_before_request():
    # Check all IP Requests for banned IP Addresses
    if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
        requestIP = request.environ["REMOTE_ADDR"]
    else:
        requestIP = request.environ["HTTP_X_FORWARDED_FOR"]

    if requestIP != "127.0.0.1":
        try:
            banQuery = banList.ipList.query.filter_by(ipAddress=requestIP).first()
            if banQuery != None:
                return str({"error": "banned", "reason": banQuery.reason})

            # Apply Guest UUID in Session and Handle Object
            if current_user.is_authenticated is False:
                if "guestUUID" not in session:
                    session["guestUUID"] = str(uuid.uuid4())
                GuestQuery = Sec.Guest.query.filter_by(
                    UUID=session["guestUUID"]
                ).first()
                if GuestQuery is not None:
                    GuestQuery.last_active_at = datetime.datetime.utcnow()
                    GuestQuery.last_active_ip = requestIP
                    db.session.commit()
                else:
                    # Check if a previous access from an IP Address was Used
                    GuestQuery = Sec.Guest.query.filter_by(
                        last_active_ip=requestIP
                    ).first()
                    if GuestQuery is not None:
                        GuestQuery.last_active_at = datetime.datetime.utcnow()
                        GuestQuery.UUID = session["guestUUID"]
                        db.session.commit()
                    else:
                        if len(requestIP) <= 100:
                            NewGuest = Sec.Guest(session["guestUUID"], requestIP)
                            db.session.add(NewGuest)
                            db.session.commit()
                        else:
                            NewGuest = Sec.Guest(session["guestUUID"], requestIP[0:100])
                            db.session.add(NewGuest)
                            db.session.commit()
        except:
            pass


app.logger.info({"level": "info", "message": "Initializing DB Teardown App Context"})


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


app.logger.info({"level": "info", "message": "Finalizing App Initialization"})
# ----------------------------------------------------------------------------#
# Finalize App Init
# ----------------------------------------------------------------------------#
try:
    system.newLog(
        "0", "OSP Started Up Successfully - version: " + str(globalvars.version)
    )
    app.logger.info(
        {
            "level": "info",
            "message": "OSP Core Node Started Successfully-" + str(globalvars.version),
        }
    )
except:
    pass

if __name__ == "__main__":
    app.jinja_env.auto_reload = False
    app.config["TEMPLATES_AUTO_RELOAD"] = False
    socketio.run(app, Debug=config.debugMode)
