import requests
from flask import Blueprint, request, url_for, render_template, redirect, current_app, send_from_directory, abort, flash

from globals import globalvars

root_bp = Blueprint('root', __name__)

@root_bp.route('/playbackAuth', methods=['POST'])
def playback_auth_handler():
    stream = request.form['name']
    clientIP = request.form['addr']
    username = request.form['username']
    secureHash = request.form['hash']

    r = requests.post(globalvars.apiVersion + '/apiv1/rtmp/playbackauth', data={'name': stream, 'addr': clientIP, 'username': username, 'hash': secureHash})
    if r.status_code == 200:
        return 'OK'
    else:
        return abort(400)
