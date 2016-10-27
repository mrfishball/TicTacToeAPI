"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import datetime
from google.appengine.ext import ndb
from forms import UserForm, GameForm, ScoreForm
from utils import pretty_date, check_winner

"""Enumeration for the status of a game."""
class GameState:
    Active, Completed= range(2)

class GameResult:
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

    def player_by_name(cls, name):
        return Player.query(Player.name = name).get()

    """Adds to the to total number of game won"""
    def add_won(self):
        self.won += 1
        self.put()

    def add_played(self):
    """Adds to the total number of game played"""
        self.played += 1
        self.put()

class Game(ndb.Model):
    """Game object"""
    host = KeyProperty(kind="Player", required=True)
    host_moves = PickleProperty(default=[], required=True)
    oppoent = KeyProperty(kind="Player", required=True)
    oppoent_moves = PickleProperty(default=[], required=True)
    next_turn = KeyProperty(kind="Player", required=True)
    setup = ndb.PickleProperty(required=True)
    status = ndb.IntegerProperty(default=GameState.Active, required=True)
    history = ndb.PickleProperty(default=[], required=True)
    start_date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def new_game(cls, host, oppoent):
        """Creates and returns a new game
        Oppoent will go first, host goes last"""
        game = Game(host = host,
                    oppoent = oppoent,
                    next_turn = oppoent)

        setup = range(1, 10)
        game.setup = setup
        game.put()
        return game

    def make_move(self, move, player_name):
        """Check if the player who's making the move is the player of current turn. Raise
        an error if not. If yes, check if the move is valid then remove the choice from the setup and
        add the move, player's name who made the move to history"""
        whose_move = self.next_turn.get().name
        if (whose_move == player_name):
            if 1 <= move <= 9:
                if move in self.board:
                    position = self.board.index(move)
                    selected = self.board[position]
                    self.history.append([whose_move, move])

                    """Alternate players for the next turn"""
                    if (whose_move == self.host.get().name):
                        self.host_moves.append(selected)
                        del selected
                        if check_winner(self.host_moves):
                            self.status = GameState.Completed
                            taskqueue.add(url="/tasks/send_congrats_mail", params={})
                        else:
                            self.turn = self.oppoent
                    else:
                        self.oppoent_moves.append(selected)
                        del selected
                        if check_winner(self.oppoent_moves):
                            self.status = GameState.Completed
                        else:
                            self.turn = self.host
                else: 
                    raise ValueError("This spot is taken! Please pick a different number.")
            else:
                raise ValueError("Invalid move! Please choose a number between 1 and 9: ")
        else:
            raise ValueError("It's not your turn! Please wait for your oppoent to make a move.")

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        status_list = ["Active", "Completed"]
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

    def end_game(self):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.status = GameState.Completed
        self.put()
        # Add the game to the score 'board'
        score = Score(host=self.host, won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining)
        score.put()

class Score(ndb.Model):
    game = ndb.KeyProperty(kind="Game", required=True)
    host = ndb.KeyProperty(kind="Player", required=True)
    host_result = ndb.IntegerProperty(required=True)
    oppoent = ndb.KeyProperty(kind="Player", required=True)
    oppoent_result = ndb.IntegerProperty(required=True)
    end_date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def to_form(self):
        status_list = ["Won", "Tied", "Lost", "Forfeit"]
        host_status = status_list[self.host_result]
        oppoent_status = status_list[self.oppoent_result]
        date_end = pretty_date(self.end_date)

        return ScoreForm(host_name = self.host.get().name,
            host_result = host_status,
            oppoent_name = self.oppoent.get().name,
            oppoent_result = oppoent_status,
            end_date = date_end,
            game = self.game.urlsafe()
            )
