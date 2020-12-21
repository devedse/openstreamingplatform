from flask import Blueprint, request, url_for, render_template, redirect, flash
from flask_security import current_user, login_required
from sqlalchemy.sql.expression import func
import hashlib

from classes.shared import db
from classes import settings
from classes import RecordedVideo
from classes import subscriptions
from classes import topics
from classes import views
from classes import Channel
from classes import Stream
from classes import Sec

from globals.globalvars import ejabberdServer

from functions import themes
from functions import securityFunc

liveview_bp = Blueprint('liveview', __name__, url_prefix='/view')

@liveview_bp.route('/<loc>/')
def view_page(loc):
    sysSettings = settings.settings.query.first()

    xmppserver = sysSettings.siteAddress
    if ejabberdServer != "127.0.0.1" and ejabberdServer != "localhost":
        xmppserver = ejabberdServer



    requestedChannel = Channel.Channel.query.filter_by(channelLoc=loc).first()
    if requestedChannel is not None:
        if requestedChannel.protected and sysSettings.protectionEnabled:
            if not securityFunc.check_isValidChannelViewer(requestedChannel.id):
                return render_template(themes.checkOverride('channelProtectionAuth.html'))

        # Pull ejabberd Chat Options for Room
        #from app import ejabberd
        #chatOptions = ejabberd.get_room_options(requestedChannel.channelLoc, 'conference.' + sysSettings.siteAddress)
        #for option in chatOptions:
        #    print(option)

        streamData = Stream.Stream.query.filter_by(streamKey=requestedChannel.streamKey).first()
        streamURL = ''
        edgeQuery = settings.edgeStreamer.query.filter_by(active=True).all()
        if edgeQuery == []:
            if sysSettings.adaptiveStreaming is True:
                streamURL = '/live-adapt/' + requestedChannel.channelLoc + '.m3u8'
            else:
                streamURL = '/live/' + requestedChannel.channelLoc + '/index.m3u8'
        else:
            # Handle Selecting the Node using Round Robin Logic
            if sysSettings.adaptiveStreaming is True:
                streamURL = '/edge-adapt/' + requestedChannel.channelLoc + '.m3u8'
            else:
                streamURL = '/edge/' + requestedChannel.channelLoc + '/index.m3u8'

        topicList = topics.topics.query.all()
        chatOnly = request.args.get("chatOnly")
        if chatOnly == "True" or chatOnly == "true":
            if requestedChannel.chatEnabled:
                hideBar = False
                hideBarReq = request.args.get("hideBar")
                if hideBarReq == "True" or hideBarReq == "true":
                    hideBar = True

                guestUser = None
                if 'guestUser' in request.args and current_user.is_authenticated is False:
                    guestUser = request.args.get("guestUser")

                    userQuery = Sec.User.query.filter_by(username=guestUser).first()
                    if userQuery is not None:
                        flash("Invalid User","error")
                        return(redirect(url_for("root.main_page")))

                return render_template(themes.checkOverride('chatpopout.html'), stream=streamData, streamURL=streamURL, sysSettings=sysSettings, channel=requestedChannel, hideBar=hideBar, guestUser=guestUser, xmppserver=xmppserver)
            else:
                flash("Chat is Not Enabled For This Stream","error")

        isEmbedded = request.args.get("embedded")

        requestedChannel = Channel.Channel.query.filter_by(channelLoc=loc).first()

        if isEmbedded is None or isEmbedded == "False" or isEmbedded == "false":

            secureHash = None
            rtmpURI = None

            endpoint = 'live'

            if requestedChannel.protected:
                if current_user.is_authenticated:
                    secureHash = None
                    if current_user.authType == 0:
                        secureHash = hashlib.sha256((current_user.username + requestedChannel.channelLoc + current_user.password).encode('utf-8')).hexdigest()
                    else:
                        secureHash = hashlib.sha256((current_user.username + requestedChannel.channelLoc + current_user.oAuthID).encode('utf-8')).hexdigest()
                    username = current_user.username
                    rtmpURI = 'rtmp://' + sysSettings.siteAddress + ":1935/" + endpoint + "/" + requestedChannel.channelLoc + "?username=" + username + "&hash=" + secureHash
            else:
                rtmpURI = 'rtmp://' + sysSettings.siteAddress + ":1935/" + endpoint + "/" + requestedChannel.channelLoc

            clipsList = []
            for vid in requestedChannel.recordedVideo:
                for clip in vid.clips:
                    if clip.published is True:
                        clipsList.append(clip)
            clipsList.sort(key=lambda x: x.views, reverse=True)

            subState = False
            if current_user.is_authenticated:
                chanSubQuery = subscriptions.channelSubs.query.filter_by(channelID=requestedChannel.id, userID=current_user.id).first()
                if chanSubQuery is not None:
                    subState = True

            return render_template(themes.checkOverride('channelplayer.html'), stream=streamData, streamURL=streamURL, topics=topicList, channel=requestedChannel, clipsList=clipsList,
                                   subState=subState, secureHash=secureHash, rtmpURI=rtmpURI, xmppserver=xmppserver)
        else:
            isAutoPlay = request.args.get("autoplay")
            if isAutoPlay is None:
                isAutoPlay = False
            elif isAutoPlay.lower() == 'true':
                isAutoPlay = True
            else:
                isAutoPlay = False

            countViewers = request.args.get("countViewers")
            if countViewers is None:
                countViewers = True
            elif countViewers.lower() == 'false':
                countViewers = False
            else:
                countViewers = False
            return render_template(themes.checkOverride('channelplayer_embed.html'), channel=requestedChannel, stream=streamData, streamURL=streamURL, topics=topicList, isAutoPlay=isAutoPlay, countViewers=countViewers, xmppserver=xmppserver)

    else:
        flash("No Live Stream at URL","error")
        return redirect(url_for("root.main_page"))