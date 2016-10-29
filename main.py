#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import GuessANumberApi

from models import Player, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email who has
        games in progress. Email body includes a count of active games and their
        urlsafe keys
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        players = Player.query(player.email != None)
        for player in players:
            games = Game.query(ndb.OR(Game.host == user.key,
                                      Game.oppoent == user.key)).filter(Game.status == 0)
            if games.count() > 0:
                subject = 'This is a reminder!'
                body = 'Hi {}, you have {} games in progress. Their keys are: {}.'.format(player.name,
                           games.count(),
                           '\n'.join(game.key.urlsafe() for game in games))
                logging.debug(body)
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.
                               format(app_id),
                               player.email,
                               subject,
                               body)

class SendMoveEmail(webapp2.RequestHandler):
    def post(self):
        """Send an email to a User that it is their turn"""
        player = get_by_urlsafe(self.request.get('player_key'), Player)
        game = get_by_urlsafe(self.request.get('game_key'), Game)
        subject = 'A Tic-Tac-Toe Game - It\'s your turn!'
        body = 'Hi {}, You\' oppoent has made a move!. Now it\'s your turn to play.'\
        ' The game key is: {}'.format(player.name, game.key.urlsafe())
        logging.debug(body)
        mail.send_mail('noreply@{}.appspotmail.com'.
                       format(app_id),
                       player.email,
                       subject,
                       body)

class SendForfeitEmail(webapp2.RequestHandler):
    def post(self):
        """Send an email to a User that it is their turn"""
        player = get_by_urlsafe(self.request.get('player_key'), Player)
        game = get_by_urlsafe(self.request.get('game_key'), Game)
        subject = 'A Tic-Tac-Toe Game - It\'s your turn!'
        body = 'Hi {}, Your oppoent has surrendered!.'\
        ' The game key is: {}'.format(player.name, game.key.urlsafe())
        logging.debug(body)
        mail.send_mail('noreply@{}.appspotmail.com'.
                       format(app_id),
                       player.email,
                       subject,
                       body)

class SendCongratsEmail(webapp2.RequestHandler):
    def post(self):
        """Send email to the winning player comparing their score to average."""
        player = get_by_urlsafe(self.request.get('player_key'), Player)
        game = get_by_urlsafe(self.request.get('game_key'), Game)
        subject = 'Congratulations'
        body = 'Congratulations {}, for completing the game  {}. '\
               'You have won {} game(s). Your win rate is {}%. '\
               'Keep it up!'.format(player.name, game.key.urlsafe(),
                                    player.won, player.get_win_rate())
        logging.debug(body)
        mail.send_mail('noreply@{}.appspotmail.com'.
                       format(app_id),
                       player.email,
                       subject, body)

class SendFinishEmail(webapp2.RequestHandler):
    def post(self):
        """Send email to the winning player comparing their score to average."""
        player = get_by_urlsafe(self.request.get('player_key'), Player)
        game = get_by_urlsafe(self.request.get('game_key'), Game)
        subject = 'It\'s a tie!'
        body = 'The game {} has tied!'\
                'Thank you for playing!'.format(game.key.urlsafe())
        logging.debug(body)
        mail.send_mail('noreply@{}.appspotmail.com'.
                       format(app_id),
                       player.email,
                       subject, body)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/send_move_email', SendMoveEmail),
    ('/tasks/send_congrats_mail', SendCongratsEmail),
    ('/task/send_forfeit_email', SendForfeitEmail),
    ('/task/send_finish_email', SendFinishEmail)
], debug=True)
