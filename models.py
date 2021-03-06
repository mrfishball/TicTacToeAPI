"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import datetime
from google.appengine.ext import ndb
from forms import UserForm, GameForm, ScoreForm
from utils import pretty_date


class GameState:
    """Enumeration for the status of a game."""
    Active, Completed= range(2)

class GameResult:
     """Enumeration for the status of a game of individual player."""
    Won, Tied, Lost, Forfeit = range(4)

class Player(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    won = ndb.IntegerProperty(default=0)
    played = ndb.IntegerProperty(default=0)

    @staticmethod
    """Get the win rate of the player"""
    def get_win_rate(self):
        if self.played > 0:
            return (float(self.won) / float(self.played)) * 100
        else:
            return 0

    @classmethod
    def to_form(self):
        return UserForm(name = self.name,
            email = self.email,
            won = self.won,
            played = self.played)

    def get_player_by_name(cls, name):
        return Player.query(Player.name = name).get()

    def get_player_by_email(cls, email):
        return Player.query(Player.email = email).get()

    def add_won(self):
    """Adds to the to total number of game won"""
        self.won += 1
        self.put()

    def add_played(self):
    """Adds to the total number of game played"""
        self.played += 1
        self.put()

class Game(ndb.Model):
    """Game object"""
    host = KeyProperty(kind='Player', required=True)
    host_moves = PickleProperty(default=[], required=True)
    oppoent = KeyProperty(kind='Player', required=True)
    oppoent_moves = PickleProperty(default=[], required=True)
    next_turn = KeyProperty(kind='Player', required=True)
    setup = ndb.PickleProperty(required=True)
    status = ndb.IntegerProperty(default=GameState.Active, required=True)
    history = ndb.PickleProperty(default=[], required=True)
    start_date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def new_game(cls, host, oppoent):
        """Creates and returns a new game
        Oppoent will go first, host goes last"""
        game = Game(host = host,
                    oppoent = oppoent)

        setup = range(1, 10)
        game.setup = setup
        game.next_turn = self.oppoent
        game.put()
        return game

    def check_player(self, player):
        """Check if the player is in the game"""
        return player == self.host.key or player == self.oppoent.key

    def check_player_turn(self, player):
        return player == self.next_turn.key

    def is_host(self, player):
        return player == self.host.key

    def is_oppoent(self, player):
        return player == self.oppoent.key

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        status_list = ['Active', 'Completed']
        status = status_list[self.status]
        date_start = pretty_date(self.start_date)
        form = GameForm(urlsafe_key = self.key.urlsafe(),
            setup = str(self.setup),
            host_name = self.host,
            oppoent_name = self.oppoent,
            turn = self.turn.get().name,
            status = status,
            start_date = date_start)
        return form

    def end_game(self, player=None, forfeit=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.status = GameState.Completed
        self.put()
        if player:
            if not forfeit:
                if self.is_host(player):
                    score = Score(game = self.key, host=self.host, host_result = GameResult.Won,
                    oppoent = self.oppoent, oppoent_result = GameResult.Lost)
                else self.is_oppoent(player):
                    score = Score(game = self.key, host=self.host, host_result = GameResult.Lost,
                    oppoent = self.oppoent, oppoent_result = GameResult.Won)
            else:
                if self.is_host(player):
                    score = Score(game = self.key, host=self.host, host_result = GameResult.Lost,
                    oppoent = self.oppoent, oppoent_result = GameResult.Won)
                else self.is_oppoent(player):
                    score = Score(game = self.key, host=self.host, host_result = GameResult.Won,
                    oppoent = self.oppoent, oppoent_result = GameResult.Lost)
        else:
            score = Score(game = self.key, host=self.host, host_result = GameResult.Tied,
            oppoent = self.oppoent, oppoent_result = GameResult.Tied)
        score.put()

class Score(ndb.Model):
    """Score object"""
    game = ndb.KeyProperty(kind='Game', required=True)
    host = ndb.KeyProperty(kind='Player', required=True)
    host_result = ndb.IntegerProperty(required=True)
    oppoent = ndb.KeyProperty(kind='Player', required=True)
    oppoent_result = ndb.IntegerProperty(required=True)
    end_date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def to_form(self):
        status_list = ['Won', 'Tied', 'Lost', 'Forfeit']
        host_status = status_list[self.host_result]
        oppoent_status = status_list[self.oppoent_result]
        date_end = pretty_date(self.end_date)

        return ScoreForm(host_name = self.host.get().name,
            host_result = host_status,
            oppoent_name = self.oppoent.get().name,
            oppoent_result = oppoent_status,
            end_date = date_end,
            game = self.game.urlsafe())
