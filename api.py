# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's players."""


import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache, mail
from google.appengine.api import taskqueue

from models import Player, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
PLAYER_REQUEST = endpoints.ResourceContainer(player_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='Tic-Tac-Toe', version='v1')
class TicTacToeApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=PLAYER_REQUEST,
                      response_message=StringMessage,
                      path='player',
                      name='create_player',
                      http_method='POST')
    def create_player(self, request):
        """Create a Player. Requires a unique playername"""
        if Player.get_player_by_name(request.player_name):
            raise endpoints.ConflictException(
                    'A Player with that name already exists!')
        
        if mail.is_email_valid(request.email):
          if Player.get_player_by_email(request.email):
            raise endpoints.ConfictException(
                    'A Player with that email already exists!')
          else:
            player = Player(name=request.player_name, email=request.email)
            player.put()
            return StringMessage(message='Player {} created!'.format(
                    request.player_name))
        else:
          raise endpoints.BadRequestException("Please enter a valid email address!")


    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        host = Player.get_player_by_name(request.host_name)
        oppoent = Player.get_player_by_name(request.oppoent_name)

        if host and oppoent:
          games = Game.query(ndb.AND(Game.host == host.key),
            (Game.oppoent == oppoent.key)).filter(Game.status == 0)
          if games:
            raise endpoints.ConfictException('A game is currently in session! Please finish it before starting a new game.')
          try:
              game = Game.new_game(host.key, oppoent.key)
          except ValueError:
              raise endpoints.BadRequestException('An error has occurred!')
        else:
          raise endpoints.NotFoundException(
                    'A minimum of 2 players is required!')
        return game.to_form('Good luck!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Ready to make a move?')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        game.attempts_remaining -= 1
        if request.guess == game.target:
            game.end_game(True)
            return game.to_form('You win!')

        if request.guess < game.target:
            msg = 'Too low!'
        else:
            msg = 'Too high!'

        if game.attempts_remaining < 1:
            game.end_game(False)
            return game.to_form(msg + ' Game over!')
        else:
            game.put()
            return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=PLAYER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/player/{player_name}',
                      name='get_player_scores',
                      http_method='GET')
    def get_player_scores(self, request):
        """Returns all of an individual Player's scores"""
        player = Player.query(Player.name == request.player_name).get()
        if not player:
            raise endpoints.NotFoundException(
                    'A Player with that name does not exist!')
        scores = Score.query(Score.player == player.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

api = endpoints.api_server([TicTacToeApi])
