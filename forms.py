from protorpc import messages

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    setup = messages.StringField(2, required=True)
    status = messages.StringField(3, required=True)
    host_name = messages.StringField(4, required=True)
    oppoent_name = messages.StringField(5, required=True)
    next_turn = messages.StringField(6, required=True)
    start_date = messages.StringField(7, required=True)

class GameForms(message.Message):
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    host_name = messages.StringField(1, required=True)
    oppoent_name = message.StringField(2, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    player_name= messages.StringField(1, required=True)
    move = messages.IntegerField(2, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    host_name = messages.StringField(1, required=True)
    oppoent_name = messages.StringField(2, required=True)
    host_result = messages.StringField(3, required=True)
    oppoent_result = messages.StringField(4, required=True)
    end_date = messages.StringField(5, required=True)
    game = messages.StringField(6, required=True)



class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)

class UserForm(messages.Message):
    """User Form"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2, required=True)
    won = messages.IntegerField(3, required=True)
    played = messages.IntegerField(4, required=True)


class UserForms(messages.Message):
    """Container for multiple User Forms"""
    items = messages.MessageField(UserForm, 1, repeated=True)