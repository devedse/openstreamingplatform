from sqlalchemy import and_
from sqlalchemy.sql.expression import func
import datetime
from typing import Union

from classes import settings
from classes import Channel
from classes import RecordedVideo
from classes import Stream
from classes import subscriptions
from classes import Sec
from classes import topics
from classes import comments
from classes import panel
from classes import upvotes
from classes import views
from classes.shared import db
from classes.shared import Dict2Class
from classes.shared import cache

# System Settings Related DB Calls


@cache.memoize(timeout=600)
def getSystemSettings():
    """Get cached system settings from DB and returns if exists

    Returns:
        sysSettings: System Settings
    """
    return settings.settings.query.first()


@cache.memoize(timeout=1200)
def getOAuthProviders() -> list:
    """Get Cached List of oAuth Providers and their settings

    Returns:
        settings.oAuthProvider: List of oAuth Providers
    """
    SystemOAuthProviders = settings.oAuthProvider.query.all()
    return SystemOAuthProviders


@cache.memoize(timeout=300)
def getChannelLiveViewsByDate(channelId: str) -> list:
    """Get Cached List of DB Live Views for a given channel

    Args:
        channelId (str): UUID Channel identifier

    Returns:
        views.views: Live View Count Instances, grouped by Date
    """
    liveViewCountQuery = (
        db.session.query(
            func.date(views.views.date), func.count(views.views.id)
        )
        .filter(views.views.viewType == 0)
        .filter(views.views.itemID == channelId)
        .filter(
            views.views.date
            > (datetime.datetime.utcnow() - datetime.timedelta(days=30))
        )
        .group_by(func.date(views.views.date))
        .all()
    )
    return liveViewCountQuery

@cache.memoize(timeout=600)
def getVideoViewsByDate(videoId: int) -> list:
    """Get Cached DB Video View Count Per Video by Date

    Args:
        videoId (int): Video ID Number

    Returns:
        views.views: Video Count Instances, grouped by Date
    """
    videoViewCountQuery = (
        db.session.query(
            func.date(views.views.date), func.count(views.views.id)
        )
        .filter(views.views.viewType==1)
        .filter(views.views.itemID==videoId)
        .filter(views.views.date > (datetime.datetime.utcnow() - datetime.timedelta(days=30)))
        .group_by(func.date(views.views.date))
        .all()
    )
    return videoViewCountQuery

# Stream Related DB Calls
@cache.memoize(timeout=60)
def searchStreams(term: str) -> list:
    """Search for a DB cached stream with a given term

    Args:
        term (str): Search Term

    Returns:
        list: Stream List
    """
    if term is not None:
        StreamNameQuery = (
            Stream.Stream.query.filter(
                Stream.Stream.active == True,
                Stream.Stream.streamName.like("%" + term + "%"),
            )
            .join(Channel.Channel, Channel.Channel.id == Stream.Stream.linkedChannel)
            .with_entities(
                Stream.Stream.id,
                Stream.Stream.streamName,
                Channel.Channel.channelLoc,
                Stream.Stream.uuid,
                Stream.Stream.linkedChannel,
                Stream.Stream.topic,
                Stream.Stream.currentViewers,
                Stream.Stream.totalViewers,
                Stream.Stream.active,
                Stream.Stream.rtmpServer,
            )
            .all()
        )

        resultsArray = StreamNameQuery
        resultsArray = list(set(resultsArray))
        return resultsArray
    else:
        return []


# Channel Related DB Calls
@cache.memoize(timeout=60)
def getAllChannels() -> list:
    """Get all Cached DB Channels and return

    Returns:
        Channel.Channel: All Channels
    """
    return Channel.Channel.query.with_entities(
        Channel.Channel.id,
        Channel.Channel.owningUser,
        Channel.Channel.channelName,
        Channel.Channel.channelLoc,
        Channel.Channel.topic,
        Channel.Channel.views,
        Channel.Channel.currentViewers,
        Channel.Channel.record,
        Channel.Channel.chatEnabled,
        Channel.Channel.chatBG,
        Channel.Channel.chatTextColor,
        Channel.Channel.chatAnimation,
        Channel.Channel.imageLocation,
        Channel.Channel.offlineImageLocation,
        Channel.Channel.channelBannerLocation,
        Channel.Channel.description,
        Channel.Channel.allowComments,
        Channel.Channel.protected,
        Channel.Channel.channelMuted,
        Channel.Channel.showChatJoinLeaveNotification,
        Channel.Channel.defaultStreamName,
        Channel.Channel.autoPublish,
        Channel.Channel.vanityURL,
        Channel.Channel.private,
        Channel.Channel.streamKey,
        Channel.Channel.xmppToken,
        Channel.Channel.chatFormat,
        Channel.Channel.chatHistory,
        Channel.Channel.allowGuestNickChange,
        Channel.Channel.showHome,
        Channel.Channel.maxVideoRetention,
        Channel.Channel.maxClipRetention,
        Channel.Channel.hubEnabled,
        Channel.Channel.hubNSFW
    ).all()


@cache.memoize(timeout=60)
def getChannel(channelID: int) -> Union[list, None]:
    """Returns Cached Data on a given Channel

    Args:
        channelID (int): Channel ID

    Returns:
        Union[list, None]: Channel Data, if exists
    """
    return Channel.Channel.query.with_entities(
        Channel.Channel.id,
        Channel.Channel.owningUser,
        Channel.Channel.channelName,
        Channel.Channel.channelLoc,
        Channel.Channel.topic,
        Channel.Channel.views,
        Channel.Channel.currentViewers,
        Channel.Channel.record,
        Channel.Channel.chatEnabled,
        Channel.Channel.chatBG,
        Channel.Channel.chatTextColor,
        Channel.Channel.chatAnimation,
        Channel.Channel.imageLocation,
        Channel.Channel.offlineImageLocation,
        Channel.Channel.channelBannerLocation,
        Channel.Channel.description,
        Channel.Channel.allowComments,
        Channel.Channel.protected,
        Channel.Channel.channelMuted,
        Channel.Channel.showChatJoinLeaveNotification,
        Channel.Channel.defaultStreamName,
        Channel.Channel.autoPublish,
        Channel.Channel.vanityURL,
        Channel.Channel.private,
        Channel.Channel.streamKey,
        Channel.Channel.xmppToken,
        Channel.Channel.chatFormat,
        Channel.Channel.chatHistory,
        Channel.Channel.allowGuestNickChange,
        Channel.Channel.showHome,
        Channel.Channel.maxVideoRetention,
        Channel.Channel.maxClipRetention,
        Channel.Channel.hubEnabled,
        Channel.Channel.hubNSFW
    ).filter_by(id=channelID).first()


@cache.memoize(timeout=600)
def getChannelByLoc(channelLoc: str) -> Union[list, None]:
    """Get Cached DB Channel based on Channel UUID

    Args:
        channelLoc (str): Channel UUID

    Returns:
        Union[list, None]: Channel if Exists
    """
    return Channel.Channel.query.with_entities(
        Channel.Channel.id,
        Channel.Channel.owningUser,
        Channel.Channel.channelName,
        Channel.Channel.channelLoc,
        Channel.Channel.topic,
        Channel.Channel.views,
        Channel.Channel.currentViewers,
        Channel.Channel.record,
        Channel.Channel.chatEnabled,
        Channel.Channel.chatBG,
        Channel.Channel.chatTextColor,
        Channel.Channel.chatAnimation,
        Channel.Channel.imageLocation,
        Channel.Channel.offlineImageLocation,
        Channel.Channel.channelBannerLocation,
        Channel.Channel.description,
        Channel.Channel.allowComments,
        Channel.Channel.protected,
        Channel.Channel.channelMuted,
        Channel.Channel.showChatJoinLeaveNotification,
        Channel.Channel.defaultStreamName,
        Channel.Channel.autoPublish,
        Channel.Channel.vanityURL,
        Channel.Channel.private,
        Channel.Channel.streamKey,
        Channel.Channel.xmppToken,
        Channel.Channel.chatFormat,
        Channel.Channel.chatHistory,
        Channel.Channel.allowGuestNickChange,
        Channel.Channel.showHome,
        Channel.Channel.maxVideoRetention,
        Channel.Channel.maxClipRetention,
        Channel.Channel.hubEnabled,
        Channel.Channel.hubNSFW
    ).filter_by(channelLoc=channelLoc).first()


@cache.memoize(timeout=600)
def getChannelByStreamKey(StreamKey: str) -> Union[list, None]:
    return Channel.Channel.query.with_entities(
        Channel.Channel.id,
        Channel.Channel.owningUser,
        Channel.Channel.channelName,
        Channel.Channel.channelLoc,
        Channel.Channel.topic,
        Channel.Channel.views,
        Channel.Channel.currentViewers,
        Channel.Channel.record,
        Channel.Channel.chatEnabled,
        Channel.Channel.chatBG,
        Channel.Channel.chatTextColor,
        Channel.Channel.chatAnimation,
        Channel.Channel.imageLocation,
        Channel.Channel.offlineImageLocation,
        Channel.Channel.channelBannerLocation,
        Channel.Channel.description,
        Channel.Channel.allowComments,
        Channel.Channel.protected,
        Channel.Channel.channelMuted,
        Channel.Channel.showChatJoinLeaveNotification,
        Channel.Channel.defaultStreamName,
        Channel.Channel.autoPublish,
        Channel.Channel.vanityURL,
        Channel.Channel.private,
        Channel.Channel.streamKey,
        Channel.Channel.xmppToken,
        Channel.Channel.chatFormat,
        Channel.Channel.chatHistory,
        Channel.Channel.allowGuestNickChange,
        Channel.Channel.showHome,
        Channel.Channel.maxVideoRetention,
        Channel.Channel.maxClipRetention,
        Channel.Channel.hubEnabled,
        Channel.Channel.hubNSFW
    ).filter_by(streamKey=StreamKey).first()


@cache.memoize(timeout=600)
def getChannelsByOwnerId(OwnerId: int) -> list:
    return Channel.Channel.query.with_entities(
        Channel.Channel.id,
        Channel.Channel.owningUser,
        Channel.Channel.channelName,
        Channel.Channel.channelLoc,
        Channel.Channel.topic,
        Channel.Channel.views,
        Channel.Channel.currentViewers,
        Channel.Channel.record,
        Channel.Channel.chatEnabled,
        Channel.Channel.chatBG,
        Channel.Channel.chatTextColor,
        Channel.Channel.chatAnimation,
        Channel.Channel.imageLocation,
        Channel.Channel.offlineImageLocation,
        Channel.Channel.channelBannerLocation,
        Channel.Channel.description,
        Channel.Channel.allowComments,
        Channel.Channel.protected,
        Channel.Channel.channelMuted,
        Channel.Channel.showChatJoinLeaveNotification,
        Channel.Channel.defaultStreamName,
        Channel.Channel.autoPublish,
        Channel.Channel.vanityURL,
        Channel.Channel.private,
        Channel.Channel.streamKey,
        Channel.Channel.xmppToken,
        Channel.Channel.chatFormat,
        Channel.Channel.chatHistory,
        Channel.Channel.allowGuestNickChange,
        Channel.Channel.showHome,
        Channel.Channel.maxVideoRetention,
        Channel.Channel.maxClipRetention,
        Channel.Channel.hubEnabled,
        Channel.Channel.hubNSFW
    ).filter_by(owningUser=OwnerId).all()


@cache.memoize(timeout=30)
def serializeChannelByLocationID(channelLoc: str) -> dict:
    channel: Channel.Channel = getChannelByLoc(channelLoc)
    if channel != None:
        return serializeChannel(channel.id)
    else:
        return {}


@cache.memoize(timeout=30)
def serializeChannel(channelID: int) -> dict:
    channelData = getChannel(channelID)
    if channelData != None:
        return {
            "id": channelData.id,
            "channelEndpointID": channelData.channelLoc,
            "owningUser": channelData.owningUser,
            "owningUsername": getUser(channelData.owningUser).username,
            "owningUserImage": getUserPhotoLocation(channelData.owningUser),
            "channelName": channelData.channelName,
            "description": channelData.description,
            "channelImage": "/images/" + str(channelData.imageLocation),
            "offlineImageLocation": "/images/" + str(channelData.offlineImageLocation),
            "channelBannerLocation": "/images/" + str(channelData.channelBannerLocation),
            "topic": channelData.topic,
            "views": channelData.views,
            "currentViews": channelData.currentViewers,
            "recordingEnabled": channelData.record,
            "chatEnabled": channelData.chatEnabled,
            "stream": [obj.id for obj in getChannelStreamIds(channelData.id)],
            "recordedVideoIDs": [obj.id for obj in getChannelVideos(channelData.id)],
            "upvotes": getChannelUpvotes(channelData.id),
            "protected": channelData.protected,
            "allowGuestNickChange": channelData.allowGuestNickChange,
            "vanityURL": channelData.vanityURL,
            "showHome": channelData.showHome,
            "maxVideoRetention": channelData.maxVideoRetention,
            "maxClipRetention": channelData.maxClipRetention,
            "subscriptions": getChannelSubCount(channelID),
            "hubEnabled": channelData.hubEnabled,
            "hubNSFW": channelData.hubNSFW,
            "tags": [getChannelTagName(obj.id) for obj in getChannelTagIds(channelData.id)],
        }
    else:
        return {}


@cache.memoize(timeout=30)
def serializeChannels(hubCheck: bool = False) -> list:
    if hubCheck is True:
        ChannelQuery = (
            Channel.Channel.query.filter_by(private=False, hubEnabled=True)
            .with_entities(Channel.Channel.id)
            .all()
        )
    else:
        ChannelQuery = (
            Channel.Channel.query.filter_by(private=False)
            .with_entities(Channel.Channel.id)
            .all()
        )
    returnData = []
    for channel in ChannelQuery:
        returnData.append(serializeChannel(channel.id))
    return returnData

@cache.memoize(timeout=30)
def getLiveChannels(hubCheck: bool = False) -> list:
    streamQuery = Stream.Stream.query.filter_by(active=True, complete=False).with_entities(Stream.Stream.id, Stream.Stream.linkedChannel).all()
    liveChannelIds = []
    for stream in streamQuery:
        if stream.linkedChannel not in liveChannelIds:
            liveChannelIds.append(stream.linkedChannel)
    liveChannelReturn = []
    for liveChannelId in liveChannelIds:
        serializedData = serializeChannel(liveChannelId)
        if hubCheck is True:
            if serializedData['hubEnabled'] is True:
                liveChannelReturn.append(serializedData)
        else:
            liveChannelReturn.append(serializeChannel(liveChannelId))
    return liveChannelReturn

@cache.memoize(timeout=60)
def getHubChannels() -> list:
    return serializeChannels(hubCheck=True)


@cache.memoize(timeout=30)
def getChannelSubCount(channelID: int) -> int:
    return subscriptions.channelSubs.query.filter_by(
        channelID=channelID
    ).count()


@cache.memoize(timeout=60)
def getChannelUpvotes(channelID):
    UpvoteQuery = upvotes.channelUpvotes.query.filter_by(channelID=channelID).count()
    return UpvoteQuery


@cache.memoize(timeout=5)
def getChannelStreamIds(channelID: int) -> list:
    return (
        Stream.Stream.query.filter_by(active=True, linkedChannel=channelID)
        .with_entities(Stream.Stream.id)
        .all()
    )


@cache.memoize(timeout=5)
def isChannelLive(channelID: int) -> bool:
    StreamQuery = Stream.Stream.query.filter_by(
        active=True, linkedChannel=channelID
    ).first()
    if StreamQuery is not None:
        return True
    else:
        return False


@cache.memoize(timeout=30)
def getChannelTagIds(channelID: int) -> list:
    return (
        Channel.channel_tags.query.filter_by(channelID=channelID)
        .with_entities(Channel.channel_tags.id)
        .all()
    )

@cache.memoize(timeout=240)
def getChannelTagName(tagId: int):
    return (
        Channel.channel_tags.query.filter_by(id=tagId)
        .with_entities(Channel.channel_tags.name)
        .scalar()
    )


@cache.memoize(timeout=10)
def getChannelVideos(channelID: int) -> list:
    VideoQuery = (
        RecordedVideo.RecordedVideo.query.filter_by(channelID=channelID)
        .with_entities(
            RecordedVideo.RecordedVideo.id,
            RecordedVideo.RecordedVideo.channelName,
            RecordedVideo.RecordedVideo.gifLocation,
            RecordedVideo.RecordedVideo.thumbnailLocation,
            RecordedVideo.RecordedVideo.videoLocation,
            RecordedVideo.RecordedVideo.topic,
            RecordedVideo.RecordedVideo.videoDate,
            RecordedVideo.RecordedVideo.length,
            RecordedVideo.RecordedVideo.description,
            RecordedVideo.RecordedVideo.allowComments,
            RecordedVideo.RecordedVideo.views,
            RecordedVideo.RecordedVideo.published,
            RecordedVideo.RecordedVideo.channelID,
            RecordedVideo.RecordedVideo.owningUser,
        )
        .all()
    )
    return VideoQuery


@cache.memoize(timeout=1200)
def getChannelLocationFromID(channelID: int) -> Union[str, None]:
    ChannelQuery = (
        Channel.Channel.query.filter_by(id=channelID)
        .with_entities(Channel.Channel.id, Channel.Channel.channelLoc)
        .first()
    )
    if ChannelQuery is not None:
        return ChannelQuery.channelLoc
    else:
        return None


@cache.memoize(timeout=1200)
def getChannelIDFromLocation(channelLocation: str) -> Union[int, None]:
    ChannelQuery = (
        Channel.Channel.query.filter_by(channelLoc=channelLocation)
        .with_entities(Channel.Channel.id, Channel.Channel.channelLoc)
        .first()
    )
    if ChannelQuery is not None:
        return ChannelQuery.id
    else:
        return None


@cache.memoize(timeout=120)
def searchChannels(term: str) -> list:
    if term is not None:
        ChannelNameQuery = (
            Channel.Channel.query.filter(
                Channel.Channel.channelName.like("%" + term + "%")
            )
            .with_entities(
                Channel.Channel.id,
                Channel.Channel.channelName,
                Channel.Channel.channelLoc,
                Channel.Channel.private,
                Channel.Channel.imageLocation,
                Channel.Channel.owningUser,
                Channel.Channel.topic,
                Channel.Channel.views,
                Channel.Channel.currentViewers,
                Channel.Channel.record,
                Channel.Channel.chatEnabled,
                Channel.Channel.chatBG,
                Channel.Channel.chatTextColor,
                Channel.Channel.chatAnimation,
                Channel.Channel.offlineImageLocation,
                Channel.Channel.channelBannerLocation,
                Channel.Channel.description,
                Channel.Channel.allowComments,
                Channel.Channel.protected,
                Channel.Channel.channelMuted,
                Channel.Channel.showChatJoinLeaveNotification,
                Channel.Channel.defaultStreamName,
                Channel.Channel.autoPublish,
                Channel.Channel.vanityURL,
            )
            .all()
        )
        ChannelDescriptionQuery = (
            Channel.Channel.query.filter(
                Channel.Channel.description.like("%" + term + "%")
            )
            .with_entities(
                Channel.Channel.id,
                Channel.Channel.channelName,
                Channel.Channel.channelLoc,
                Channel.Channel.private,
                Channel.Channel.imageLocation,
                Channel.Channel.owningUser,
                Channel.Channel.topic,
                Channel.Channel.views,
                Channel.Channel.currentViewers,
                Channel.Channel.record,
                Channel.Channel.chatEnabled,
                Channel.Channel.chatBG,
                Channel.Channel.chatTextColor,
                Channel.Channel.chatAnimation,
                Channel.Channel.offlineImageLocation,
                Channel.Channel.channelBannerLocation,
                Channel.Channel.description,
                Channel.Channel.allowComments,
                Channel.Channel.protected,
                Channel.Channel.channelMuted,
                Channel.Channel.showChatJoinLeaveNotification,
                Channel.Channel.defaultStreamName,
                Channel.Channel.autoPublish,
                Channel.Channel.vanityURL,
            )
            .all()
        )
        ChannelTagQuery = (
            Channel.channel_tags.query.filter(
                Channel.channel_tags.name.like("%" + term + "%")
            )
            .with_entities(
                Channel.channel_tags.id,
                Channel.channel_tags.name,
                Channel.channel_tags.channelID,
            )
            .all()
        )

        ChannelTagEntryQuery = []
        for channel in ChannelTagQuery:
            ChannelTagEntryQuery = (
                Channel.Channel.query.filter_by(id=channel.channelID)
                .with_entities(
                    Channel.Channel.id,
                    Channel.Channel.channelName,
                    Channel.Channel.channelLoc,
                    Channel.Channel.private,
                    Channel.Channel.imageLocation,
                    Channel.Channel.owningUser,
                    Channel.Channel.topic,
                    Channel.Channel.views,
                    Channel.Channel.currentViewers,
                    Channel.Channel.record,
                    Channel.Channel.chatEnabled,
                    Channel.Channel.chatBG,
                    Channel.Channel.chatTextColor,
                    Channel.Channel.chatAnimation,
                    Channel.Channel.offlineImageLocation,
                    Channel.Channel.channelBannerLocation,
                    Channel.Channel.description,
                    Channel.Channel.allowComments,
                    Channel.Channel.protected,
                    Channel.Channel.channelMuted,
                    Channel.Channel.showChatJoinLeaveNotification,
                    Channel.Channel.defaultStreamName,
                    Channel.Channel.autoPublish,
                    Channel.Channel.vanityURL,
                )
                .all()
            )

        resultsArray = ChannelNameQuery + ChannelDescriptionQuery
        resultsArray = list(set(resultsArray))
        for entry in ChannelTagEntryQuery:
            if entry not in resultsArray:
                resultsArray.append(entry)

        return resultsArray
    else:
        return []


def invalidateChannelCache(channelId: int) -> bool:
    channelQuery = getChannel(channelId)
    if channelQuery is not None:
        lastCachedKey = channelQuery.streamKey
        channelLoc = getChannelLocationFromID(channelId)

        cache.delete_memoized(getChannel, channelId)
        cache.delete_memoized(getChannelByLoc, channelLoc)
        cache.delete_memoized(getChannelByStreamKey, lastCachedKey)

        return True
    return False

def invalidateGCMCache(user_uuid: str) -> bool:
    if Sec.User.query.filter_by(
        uuid=user_uuid
    ).with_entities(Sec.User.id).first() is None:
        return False
    
    cache.delete_memoized(IsUserGCMByUUID, user_uuid)

    return True

def invalidateVideoCache(videoId: int) -> bool:
    cachedVideo = getVideo(videoId)
    if cachedVideo is not None:
        cache.delete_memoized(getVideo, videoId)
        cache.delete_memoized(getAllVideoByOwnerId, cachedVideo.owningUser)
        cache.delete_memoized(getChannelVideos, cachedVideo.channelID)

        return True
    return False


@cache.memoize(timeout=5)
def getChanneActiveStreams(channelID: int) -> list:
    return (
        Stream.Stream.query.filter_by(
            linkedChannel=channelID, active=True, complete=False
        )
        .with_entities(
            Stream.Stream.id,
            Stream.Stream.topic,
            Stream.Stream.streamName,
            Stream.Stream.startTimestamp,
            Stream.Stream.uuid,
            Stream.Stream.currentViewers,
            Stream.Stream.totalViewers,
        )
        .all()
    )


@cache.memoize(timeout=10)
def getAllStreams() -> list:
    return (
        Stream.Stream.query.filter_by(active=True, complete=False)
        .join(Channel.Channel, and_(Channel.Channel.id == Stream.Stream.linkedChannel, Channel.Channel.private == False, Channel.Channel.protected == False))
        .with_entities(
            Stream.Stream.id,
            Stream.Stream.topic,
            Stream.Stream.streamName,
            Stream.Stream.startTimestamp,
            Stream.Stream.uuid,
            Stream.Stream.currentViewers,
            Stream.Stream.totalViewers,
            Channel.Channel.channelLoc,
            Channel.Channel.owningUser,
        )
        .all()
    )


# Recorded Video Related DB Calls
@cache.memoize(timeout=60)
def getAllVideo_View(channelID: int) -> list:
    return (
        RecordedVideo.RecordedVideo.query.filter_by(
            channelID=channelID, pending=False, published=True
        )
        .with_entities(
            RecordedVideo.RecordedVideo.id,
            RecordedVideo.RecordedVideo.uuid,
            RecordedVideo.RecordedVideo.videoDate,
            RecordedVideo.RecordedVideo.owningUser,
            RecordedVideo.RecordedVideo.channelName,
            RecordedVideo.RecordedVideo.channelID,
            RecordedVideo.RecordedVideo.description,
            RecordedVideo.RecordedVideo.topic,
            RecordedVideo.RecordedVideo.views,
            RecordedVideo.RecordedVideo.length,
            RecordedVideo.RecordedVideo.videoLocation,
            RecordedVideo.RecordedVideo.thumbnailLocation,
            RecordedVideo.RecordedVideo.gifLocation,
            RecordedVideo.RecordedVideo.pending,
            RecordedVideo.RecordedVideo.allowComments,
            RecordedVideo.RecordedVideo.published,
            RecordedVideo.RecordedVideo.originalStreamID,
        )
        .all()
    )


@cache.memoize(timeout=60)
def getVideo(videoID: int) -> list:
    return (
        RecordedVideo.RecordedVideo.query.filter_by(id=videoID)
        .with_entities(
            RecordedVideo.RecordedVideo.id,
            RecordedVideo.RecordedVideo.uuid,
            RecordedVideo.RecordedVideo.videoDate,
            RecordedVideo.RecordedVideo.owningUser,
            RecordedVideo.RecordedVideo.channelName,
            RecordedVideo.RecordedVideo.channelID,
            RecordedVideo.RecordedVideo.description,
            RecordedVideo.RecordedVideo.topic,
            RecordedVideo.RecordedVideo.views,
            RecordedVideo.RecordedVideo.length,
            RecordedVideo.RecordedVideo.videoLocation,
            RecordedVideo.RecordedVideo.thumbnailLocation,
            RecordedVideo.RecordedVideo.gifLocation,
            RecordedVideo.RecordedVideo.pending,
            RecordedVideo.RecordedVideo.allowComments,
            RecordedVideo.RecordedVideo.published,
            RecordedVideo.RecordedVideo.originalStreamID,
        )
        .first()
    )


@cache.memoize(timeout=60)
def getAllVideoByOwnerId(ownerId: int) -> list:
    return (
        RecordedVideo.RecordedVideo.query.filter_by(
            owningUser=ownerId, pending=False, published=True
        )
        .with_entities(
            RecordedVideo.RecordedVideo.id,
            RecordedVideo.RecordedVideo.uuid,
            RecordedVideo.RecordedVideo.videoDate,
            RecordedVideo.RecordedVideo.owningUser,
            RecordedVideo.RecordedVideo.channelName,
            RecordedVideo.RecordedVideo.channelID,
            RecordedVideo.RecordedVideo.description,
            RecordedVideo.RecordedVideo.topic,
            RecordedVideo.RecordedVideo.views,
            RecordedVideo.RecordedVideo.length,
            RecordedVideo.RecordedVideo.videoLocation,
            RecordedVideo.RecordedVideo.thumbnailLocation,
            RecordedVideo.RecordedVideo.gifLocation,
            RecordedVideo.RecordedVideo.pending,
            RecordedVideo.RecordedVideo.allowComments,
            RecordedVideo.RecordedVideo.published,
            RecordedVideo.RecordedVideo.originalStreamID,
        )
        .all()
    )


@cache.memoize(timeout=60)
def getAllVideo() -> list:
    return (
        RecordedVideo.RecordedVideo.query.filter_by(pending=False, published=True)
        .join(
            Channel.Channel,
            and_(
                Channel.Channel.id == RecordedVideo.RecordedVideo.channelID,
                Channel.Channel.protected == False,
                Channel.Channel.private == False
            ),
        )
        .with_entities(
            RecordedVideo.RecordedVideo.id,
            RecordedVideo.RecordedVideo.uuid,
            RecordedVideo.RecordedVideo.videoDate,
            RecordedVideo.RecordedVideo.owningUser,
            RecordedVideo.RecordedVideo.channelName,
            RecordedVideo.RecordedVideo.channelID,
            RecordedVideo.RecordedVideo.description,
            RecordedVideo.RecordedVideo.topic,
            RecordedVideo.RecordedVideo.views,
            RecordedVideo.RecordedVideo.length,
            RecordedVideo.RecordedVideo.videoLocation,
            RecordedVideo.RecordedVideo.thumbnailLocation,
            RecordedVideo.RecordedVideo.gifLocation,
            RecordedVideo.RecordedVideo.pending,
            RecordedVideo.RecordedVideo.allowComments,
            RecordedVideo.RecordedVideo.published,
            RecordedVideo.RecordedVideo.originalStreamID,
        )
        .all()
    )

# Recorded Video Related DB Calls
@cache.memoize(timeout=60)
def getTopicsVideo_View(TopicID: int) -> list:
    return (
        RecordedVideo.RecordedVideo.query.filter_by(
            topic=TopicID, pending=False, published=True
        )
        .with_entities(
            RecordedVideo.RecordedVideo.id,
            RecordedVideo.RecordedVideo.uuid,
            RecordedVideo.RecordedVideo.videoDate,
            RecordedVideo.RecordedVideo.owningUser,
            RecordedVideo.RecordedVideo.channelName,
            RecordedVideo.RecordedVideo.channelID,
            RecordedVideo.RecordedVideo.description,
            RecordedVideo.RecordedVideo.topic,
            RecordedVideo.RecordedVideo.views,
            RecordedVideo.RecordedVideo.length,
            RecordedVideo.RecordedVideo.videoLocation,
            RecordedVideo.RecordedVideo.thumbnailLocation,
            RecordedVideo.RecordedVideo.gifLocation,
            RecordedVideo.RecordedVideo.pending,
            RecordedVideo.RecordedVideo.allowComments,
            RecordedVideo.RecordedVideo.published,
            RecordedVideo.RecordedVideo.originalStreamID,
        )
        .all()
    )


cache.memoize(timeout=60)
def getVideoDict(videoID: int) -> dict:
    videoReturn = getVideo(videoID)
    if videoReturn != None:
        return {
                "id": videoReturn.id,
                "uuid": videoReturn.uuid,
                "channelID": videoReturn.channelID,
                "owningUser": videoReturn.owningUser,
                "videoDate": str(videoReturn.videoDate),
                "videoName": videoReturn.channelName,
                "description": videoReturn.description,
                "topic": videoReturn.topic,
                "views": videoReturn.views,
                "length": videoReturn.length,
                "upvotes": getVideoUpvotes(videoReturn.id),
                "videoLocation": "/videos/" + videoReturn.videoLocation,
                "thumbnailLocation": "/videos/" + videoReturn.thumbnailLocation,
                "gifLocation": "/videos/" + videoReturn.gifLocation,
                "ClipIDs": [obj.id for obj in getClipsForVideo(videoReturn.id)],
                "tags": [obj.id for obj in getVideoTags(videoReturn.id)],
        }
    else:
        return {}

@cache.memoize(timeout=30)
def getVideoUpvotes(videoID: int) -> int:
    return upvotes.videoUpvotes.query.filter_by(videoID=videoID).count()

@cache.memoize(timeout=30)
def getVideoTags(videoID: int) -> list:
    return RecordedVideo.video_tags.query.filter_by(videoID=videoID).with_entities(RecordedVideo.video_tags.id, RecordedVideo.video_tags.name).all()


@cache.memoize(timeout=60)
def getVideoCommentCount(videoID: int) -> int:
    videoCommentsQuery = comments.videoComments.query.filter_by(videoID=videoID).count()
    return videoCommentsQuery


@cache.memoize(timeout=120)
def searchVideos(term: str) -> list:
    if term is not None:

        VideoNameQuery = (
            RecordedVideo.RecordedVideo.query.filter(
                RecordedVideo.RecordedVideo.channelName.like("%" + term + "%"),
                RecordedVideo.RecordedVideo.published == True,
            )
            .with_entities(
                RecordedVideo.RecordedVideo.id,
                RecordedVideo.RecordedVideo.channelName,
                RecordedVideo.RecordedVideo.uuid,
                RecordedVideo.RecordedVideo.thumbnailLocation,
                RecordedVideo.RecordedVideo.owningUser,
                RecordedVideo.RecordedVideo.channelID,
                RecordedVideo.RecordedVideo.description,
                RecordedVideo.RecordedVideo.description,
                RecordedVideo.RecordedVideo.topic,
                RecordedVideo.RecordedVideo.views,
                RecordedVideo.RecordedVideo.length,
                RecordedVideo.RecordedVideo.videoLocation,
                RecordedVideo.RecordedVideo.gifLocation,
                RecordedVideo.RecordedVideo.pending,
                RecordedVideo.RecordedVideo.videoDate,
                RecordedVideo.RecordedVideo.allowComments,
                RecordedVideo.RecordedVideo.published,
                RecordedVideo.RecordedVideo.originalStreamID,
            )
            .all()
        )

        VideoDescriptionQuery = (
            RecordedVideo.RecordedVideo.query.filter(
                RecordedVideo.RecordedVideo.channelName.like("%" + term + "%"),
                RecordedVideo.RecordedVideo.published == True,
            )
            .with_entities(
                RecordedVideo.RecordedVideo.id,
                RecordedVideo.RecordedVideo.channelName,
                RecordedVideo.RecordedVideo.uuid,
                RecordedVideo.RecordedVideo.thumbnailLocation,
                RecordedVideo.RecordedVideo.owningUser,
                RecordedVideo.RecordedVideo.channelID,
                RecordedVideo.RecordedVideo.description,
                RecordedVideo.RecordedVideo.description,
                RecordedVideo.RecordedVideo.topic,
                RecordedVideo.RecordedVideo.views,
                RecordedVideo.RecordedVideo.length,
                RecordedVideo.RecordedVideo.videoLocation,
                RecordedVideo.RecordedVideo.gifLocation,
                RecordedVideo.RecordedVideo.pending,
                RecordedVideo.RecordedVideo.videoDate,
                RecordedVideo.RecordedVideo.allowComments,
                RecordedVideo.RecordedVideo.published,
                RecordedVideo.RecordedVideo.originalStreamID,
            )
            .all()
        )

        VideoTagQuery = RecordedVideo.video_tags.query.filter(
            RecordedVideo.video_tags.name.like("%" + term + "%")
        ).with_entities(
            RecordedVideo.video_tags.id,
            RecordedVideo.video_tags.name,
            RecordedVideo.video_tags.videoID,
        )

        VideoTagEntryQuery = []
        for vid in VideoTagQuery:
            VideoTagEntryQuery = (
                RecordedVideo.RecordedVideo.query.filter_by(
                    id=vid.videoID, published=True
                )
                .with_entities(
                    RecordedVideo.RecordedVideo.id,
                    RecordedVideo.RecordedVideo.channelName,
                    RecordedVideo.RecordedVideo.uuid,
                    RecordedVideo.RecordedVideo.thumbnailLocation,
                    RecordedVideo.RecordedVideo.owningUser,
                    RecordedVideo.RecordedVideo.channelID,
                    RecordedVideo.RecordedVideo.description,
                    RecordedVideo.RecordedVideo.description,
                    RecordedVideo.RecordedVideo.topic,
                    RecordedVideo.RecordedVideo.views,
                    RecordedVideo.RecordedVideo.length,
                    RecordedVideo.RecordedVideo.videoLocation,
                    RecordedVideo.RecordedVideo.gifLocation,
                    RecordedVideo.RecordedVideo.pending,
                    RecordedVideo.RecordedVideo.videoDate,
                    RecordedVideo.RecordedVideo.allowComments,
                    RecordedVideo.RecordedVideo.published,
                    RecordedVideo.RecordedVideo.originalStreamID,
                )
                .all()
            )

        resultsArray = VideoNameQuery + VideoDescriptionQuery
        resultsArray = list(set(resultsArray))
        for entry in VideoTagEntryQuery:
            if entry not in resultsArray:
                resultsArray.append(entry)

        return resultsArray
    else:
        return []


# Clip Related DB Calls
@cache.memoize(timeout=30)
def getClipChannelID(clipID: int) -> Union[int, None]:
    ClipQuery = RecordedVideo.Clips.query.filter_by(id=clipID).first()
    if ClipQuery is None:
        return None
    return ClipQuery.channelID

@cache.memoize(timeout=30)
def getClipsForVideo(videoID: int) -> list:
    return (
        RecordedVideo.Clips.query.filter_by(parentVideo=videoID)
        .with_entities(
            RecordedVideo.Clips.id,
            RecordedVideo.Clips.uuid,
            RecordedVideo.Clips.parentVideo,
            RecordedVideo.Clips.startTime,
            RecordedVideo.Clips.endTime,
            RecordedVideo.Clips.length,
            RecordedVideo.Clips.views,
            RecordedVideo.Clips.clipName,
            RecordedVideo.Clips.videoLocation,
            RecordedVideo.Clips.description,
            RecordedVideo.Clips.thumbnailLocation,
            RecordedVideo.Clips.gifLocation,
            RecordedVideo.Clips.published
        ).all()
    )

@cache.memoize(timeout=60)
def getAllClipsForChannel_View(channelID: int) -> list:
    return RecordedVideo.Clips.query.filter_by(
        channelID=channelID, published=True
    ).all()


@cache.memoize(timeout=60)
def getAllClipsForUser(userId: int) -> list:
    return RecordedVideo.Clips.query.filter(
        RecordedVideo.Clips.published == True,
        RecordedVideo.Clips.owningUser == userId,
    ).join(
        Channel.Channel, Channel.Channel.id == RecordedVideo.Clips.channelID
    ).join(
        Sec.User, Sec.User.id == RecordedVideo.Clips.owningUser
    ).with_entities(
        RecordedVideo.Clips.id,
        RecordedVideo.Clips.clipName,
        RecordedVideo.Clips.uuid,
        RecordedVideo.Clips.thumbnailLocation,
        RecordedVideo.Clips.owningUser,
        RecordedVideo.Clips.views,
        RecordedVideo.Clips.length,
        Channel.Channel.protected,
        RecordedVideo.Clips.channelID,
        Channel.Channel.channelName,
        RecordedVideo.Clips.topic,
        Sec.User.pictureLocation,
        Sec.User.bannerLocation,
        RecordedVideo.Clips.parentVideo,
        RecordedVideo.Clips.description,
        RecordedVideo.Clips.published,
    ).all()


@cache.memoize(timeout=120)
def searchClips(term: str) -> list:
    if term is None:
        return []

    containsTermLikeString = "%" + term + "%"
    
    return RecordedVideo.Clips.query.filter(
        (RecordedVideo.Clips.clipName.like(containsTermLikeString) | RecordedVideo.Clips.description.like(containsTermLikeString)),
        RecordedVideo.Clips.published == True,
    ).join(
        Channel.Channel,
        Channel.Channel.id == RecordedVideo.Clips.channelID,
    ).join(
        Sec.User, Sec.User.id == RecordedVideo.Clips.owningUser
    ).with_entities(
        RecordedVideo.Clips.id,
        RecordedVideo.Clips.clipName,
        RecordedVideo.Clips.uuid,
        RecordedVideo.Clips.thumbnailLocation,
        RecordedVideo.Clips.owningUser,
        RecordedVideo.Clips.views,
        RecordedVideo.Clips.length,
        Channel.Channel.protected,
        RecordedVideo.Clips.channelID,
        Channel.Channel.channelName,
        RecordedVideo.Clips.topic,
        Sec.User.pictureLocation,
        Sec.User.bannerLocation,
        RecordedVideo.Clips.parentVideo,
    ).all()


# Topic Related DB Calls
@cache.memoize(timeout=120)
def getAllTopics() -> list:
    topicQuery = topics.topics.query.all()
    return topicQuery


@cache.memoize(timeout=120)
def searchTopics(term: str) -> list:
    if term is not None:
        topicNameQuery = (
            topics.topics.query.filter(topics.topics.name.like("%" + term + "%"))
            .with_entities(topics.topics.id, topics.topics.name)
            .all()
        )
        resultsArray = topicNameQuery
        resultsArray = list(set(resultsArray))
        return resultsArray
    else:
        return []


# User Related DB Calls
@cache.memoize(timeout=300)
def getUserPhotoLocation(userID: int) -> str:
    UserQuery = (
        Sec.User.query.filter_by(id=userID)
        .with_entities(Sec.User.id, Sec.User.pictureLocation)
        .first()
    )
    if UserQuery is not None:
        if UserQuery.pictureLocation is None or UserQuery.pictureLocation == "":
            return "/static/img/user2.png"
        return UserQuery.pictureLocation
    else:
        return "/static/img/user2.png"

@cache.memoize(timeout=300)
def getUserBannerLocation(userID: int) -> str:
    UserQuery = (
        Sec.User.query.filter_by(id=userID)
        .with_entities(Sec.User.id, Sec.User.bannerLocation)
        .first()
    )
    if UserQuery is not None:
        if UserQuery.bannerLocation is None or UserQuery.bannerLocation == "":
            return "/static/img/user-banner-placeholder.jpg"
        return UserQuery.bannerLocation
    else:
        return "/static/img/user-banner-placeholder.jpg"

@cache.memoize(timeout=30)
def getUser(userID: int):
    returnData = {}
    UserQuery = Sec.User.query.filter_by(id=userID).with_entities(Sec.User.id, Sec.User.uuid, Sec.User.username, Sec.User.biography, Sec.User.pictureLocation, Sec.User.bannerLocation).first()
    if UserQuery is not None:
        OwnedChannels = getChannelsByOwnerId(UserQuery.id)
        returnData = {
            "id": str(UserQuery.id),
            "uuid": UserQuery.uuid,
            "username": UserQuery.username,
            "biography": UserQuery.biography,
            "pictureLocation": "/images/" + str(UserQuery.pictureLocation),
            "bannerLocation": "/images/" + str(UserQuery.bannerLocation),
            "channels": OwnedChannels,
            "page": "/profile/" + str(UserQuery.username) + "/"
        }
        return Dict2Class(returnData)
    else:
        return Dict2Class({})

@cache.memoize(timeout=30)
def getUserByUsernameDict(username: str) -> dict:
    returnData = {}
    UserQuery = Sec.User.query.filter_by(username=username).with_entities(Sec.User.id, Sec.User.uuid, Sec.User.username, Sec.User.biography, Sec.User.pictureLocation, Sec.User.bannerLocation).first()
    if UserQuery is not None:
        OwnedChannels = getChannelsByOwnerId(UserQuery.id)
        channelsReturn = []
        for channel in OwnedChannels:
            channelsReturn.append(channel.channelLoc)
        returnData = {
            "id": str(UserQuery.id),
            "uuid": UserQuery.uuid,
            "username": UserQuery.username,
            "biography": UserQuery.biography,
            "pictureLocation": "/images/" + str(UserQuery.pictureLocation),
            "bannerLocation": "/images/" + str(UserQuery.bannerLocation),
            "channels": channelsReturn,
            "page": "/profile/" + str(UserQuery.username) + "/"
        }
    return returnData

@cache.memoize(timeout=600)
def IsUserGCMByUUID(user_uuid: str) -> bool:
    return Sec.Role.query.filter_by(
        name="GlobalChatMod"
    ).one().users.filter_by(
        uuid=user_uuid
    ).with_entities(Sec.User.id).first() is not None

@cache.memoize(timeout=60)
def getUsers() -> list:
    return Sec.User.query.filter_by(active=True).with_entities(Sec.User.id, Sec.User.username, Sec.User.uuid).all()

@cache.memoize(timeout=120)
def searchUsers(term: str) -> list:
    if term is not None:
        userNameQuery = (
            Sec.User.query.filter(
                Sec.User.username.like("%" + term + "%"), Sec.User.active == True
            )
            .with_entities(
                Sec.User.id, Sec.User.username, Sec.User.uuid, Sec.User.pictureLocation, Sec.User.bannerLocation
            )
            .all()
        )
        userDescriptionQuery = (
            Sec.User.query.filter(
                Sec.User.biography.like("%" + term + "%"), Sec.User.active == True
            )
            .with_entities(
                Sec.User.id, Sec.User.username, Sec.User.uuid, Sec.User.pictureLocation, Sec.User.bannerLocation
            )
            .all()
        )
        resultsArray = userNameQuery + userDescriptionQuery
        resultsArray = list(set(resultsArray))
        return resultsArray
    else:
        return []


@cache.memoize(timeout=30)
def getGlobalPanel(panelId: int):
    return panel.globalPanel.query.filter_by(id=panelId).first()


@cache.memoize(timeout=30)
def getUserPanel(panelId: int):
    return panel.userPanel.query.filter_by(id=panelId).first()


@cache.memoize(timeout=30)
def getChannelPanel(panelId: int):
    return panel.channelPanel.query.filter_by(id=panelId).first()


@cache.memoize(timeout=1200)
def getStaticPages() -> list:
    return settings.static_page.query.all()


@cache.memoize(timeout=1200)
def getStaticPage(pageName: str) -> list:
    return settings.static_page.query.filter_by(name=pageName).first()
