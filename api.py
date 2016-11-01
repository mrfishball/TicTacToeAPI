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
from forms import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    UserForms, ScoreForms
from utils import get_by_urlsafe, check_winner, check_full

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
NEW_PLAYER_REQUEST = endpoints.ResourceContainer(
    player_name=messages.StringField(1),
    email=messages.StringField(2))
PLAYER_REQUEST = endpoints.ResourceContainer(
    player_name=messages.StringField(1))
FORFEIT_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),
    player_name=messages.StringField(2))


@endpoints.api(name='Tic-Tac-Toe', version='v1')
class TicTacToeApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=NEW_PLAYER_REQUEST,
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
            raise endpoints.BadRequestException(
                "Please enter a valid email address!")

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
            games = Game.query(
                ndb.AND(Game.host == host.key),
                (Game.oppoent == oppoent.key)).filter(Game.status == 0)
            if games:
                raise endpoints.ConflictException(
                    'A game is currently in session!')
            try:
                game = Game.new_game(host.key, oppoent.key)
            except ValueError:
                raise endpoints.BadRequestException(
                    'An error has occurred! Please try again')
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
            raise endpoints.NotFoundException(
                'Game not found! Please try again or start a new game.')

    @endpoints.method(request_message=FORFEIT_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/{player_name}/forfeit',
                      name='forfeit_game',
                      http_method='PUT')
    def forfeit_game(self, request):
        """Forfeit a game. Send notification to the player of next turn
        that the oppoent has surrendered and that they have won the game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        player = Player.get_player_by_name(request.player_name)
        if game and player:
            game.end_game(player, True)
            taskqueue.add(url='/tasks/send_forfeit_email', params={
                'user_key': game.next_turn.urlsafe(),
                'game_key': game.key.urlsafe()})

            taskqueue.add(url='/tasks/send_congrats_email', params={
                'user_key': game.next_turn.urlsafe(),
                'game_key': game.key.urlsafe()})

            return StringMessage(message=(
                'You have forfeited the game {}.'
                .format(request.urlsafe_game_key)))
        else:
            raise NotFoundException(
                'Game / Player not found! Please try again later.')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        player = Player.get_player_by_name(request.player_name)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        if game.status == 1:
            raise endpoints.NotFoundException('Game not in session!')
        if game.check_player(player):
            if game.check_player_turn(player):
                if 1 <= move <= 9:
                    if move in game.setup:
                        move = request.move
                        game.history.append([player_name, move])
                        if game.is_host(player):
                            game.host_moves.append(move)
                            if check_winner(game.host_moves):
                                game.end_game(player)
                                taskqueue.add(url='/tasks/send_congrats_email', params={
                                    'user_key': game.host.urlsafe(),
                                    'game_key': game.key.urlsafe()})
                            else:
                                game.next_turn = game.oppoent

                        if game.is_oppoent(player):
                            game.oppoent_moves.append(move)
                            if check_winner(game.oppoent_moves):
                                game.end_game(player)
                                taskqueue.add(url='/tasks/send_congrats_email',
                                        params={'user_key': game.oppoent.urlsafe(),
                                                'game_key': game.key.urlsafe()})
                            else:
                                game.next_turn = game.host

                    else:
                        msg = 'Your oppoent has taken this spot. Please try again'
                else:
                    msg = 'Invalid move! Please choose a number (1-9).'
            else:
                raise endpoints.ConflictException('Please wait until your turn to make a move!')
        else:
            raise endpoints.NotFoundException('Player not current game session!')

        position = game.setup.index(move)
        del game.setup[position]
        game.put()

        if check_full(game.setup):
            game.end_game()
            msg = 'It\'s a tie! Thank you for playing!'
            taskqueue.add(url='/tasks/send_finish_email',
                          params={'user_key': game.next_turn.urlsafe(),
                                  'game_key': game.key.urlsafe()})
            taskqueue.add(url='/tasks/send_finish_email',
                          params={'user_key': player.urlsafe(),
                                  'game_key': game.key.urlsafe()})
        else:
            # If game is still ongoing, send remainder email to player
            taskqueue.add(url='/tasks/send_congrats_email',
                          params={'user_key': game.next_turn.urlsafe(),
                                  'game_key': game.key.urlsafe()})
        return game.to_form(msg)

    @endpoints.method(response_message=UserForms,
                      path='rankings',
                      name='get_player_rankings',
                      http_method='GET')
    def get_player_rankings(self, request):
        """Return a list of players ranked"""
        players.query(Player.played > 0).fetch()
        players = sorted(players, key=lambda x: x.get_win_rate, reverse=True)
        return UserForms(items=[player.to_form() for player in players])

    @endpoints.method(request_message=PLAYER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/player/{player_name}',
                      name='get_player_scores',
                      http_method='GET')
    def get_player_scores(self, request):
        """Returns all of an individual Player's scores"""
        player = Player.get_player_by_name(request.player_name)
        if not player:
            raise endpoints.NotFoundException(
                    'A Player with that name does not exist!')
        scores = Score.query(
            ndb.OR(Score.host == player.key),
            (Score.oppoent == player.key)).fetch()
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return game history."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        return StringMessage(message=str(game.history))

api = endpoints.api_server([TicTacToeApi])
