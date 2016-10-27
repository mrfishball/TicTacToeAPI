"""utils.py - File for collecting general utility functions."""

import logging
from google.appengine.ext import ndb
import endpoints

def get_by_urlsafe(urlsafe, model):
    """Returns an ndb.Model entity that the urlsafe key points to. Checks
        that the type of entity returned is of the correct kind. Raises an
        error if the key String is malformed or the entity is of the incorrect
        kind
    Args:
        urlsafe: A urlsafe key string
        model: The expected entity kind
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError:"""
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except TypeError:
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity

def pretty_date(time=False):
    """Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc"""

    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return 'Just now'
        if second_diff < 60:
            return str(second_diff) + ' seconds ago'
        if second_diff < 120:
            return 'A minute ago'
        if second_diff < 3600:
            return str(second_diff / 60) + ' minutes ago'
        if second_diff < 7200:
            return 'An hour ago'
        if second_diff < 86400:
            return str(second_diff / 3600) + ' hours ago'
    if day_diff == 1:
        return 'Yesterday'
    if day_diff < 7:
        return str(day_diff) + ' days ago'
    if day_diff < 31:
        return str(day_diff / 7) + ' weeks ago'
    if day_diff < 365:
        return str(day_diff / 30) + ' months ago'
    return str(day_diff / 365) + ' years ago'

def check_winner(moves):
    """Check against all possible win patterns to see if player has won or not"""
    win_patterns = [[1,2,3], [4,5,6], [7,8,9], [1,4,7], [2,5,8], [3,6,9], [1,5,9], [3,5,7]]
    sorted_moves = moves.sort()
    if len(moves) >= 3:
        for pattern in win_patterns:
            if set(pattern) < set(sorted_moves):
                return True
        return False
    else:
        return False

