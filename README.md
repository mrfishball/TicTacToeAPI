#A Tic-Tac-Toe API (Google App Engine, Google Endpoints, Python)

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
 
##Game Description:
Tic-Tac-Toe is a paper-and-pencil game for two players, X and O, who take turns marking the spaces in a 3×3 grid. The player who succeeds in placing three of their marks in a horizontal, vertical, or diagonal row wins the game.
Each game begins with a list of numbers (1-9) inclusively. The first, second and third row of a 3 x 3 matrix are represented by
a group of numbers 1 to 3, 4 to 6 and 7 to 9 respectively.

1, 2, 3

4, 5, 6

7, 8, 9

Many different Tic-Tac-Toe games can be played by any 2 players at any
given time. (No same 2 players can have more than 1 active game.)
Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity definitions including helper methods.
 - forms.py: Message definitions.
 - utils.py: Helper functions for retrieving ndb.Models by urlsafe Key string, win condition checker and remaining move checker.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. player_name and email provided must be unique. Will 
    raise a ConflictException if a player with that player_name or email already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, min, max, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. player_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Raisea ConflictException if an active game for the same 2 players(host and oppoent)
    is found.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.

 - **forfeit_game**
    - Path: 'game/{urlsafe_game_key}/forfeit'
    - Method: GET
    - Parameters: urlsafe_game_key, player_name
    - Returns: StringMessage.
    - Description: Mark the game as Completed. The player who forfeits will lose the game while the other player will
    automatically win the game. Email notfications will be sent as well

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, player's name and move
    - Returns: GameForm with new game state.
    - Description: With game, player and player's turn validated, a move will be accepted and an updated state of the game will be returned. A move is a number from 1 - 9 on the setup, corresponding to one of the possible positions on the setup. If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_player_rankings**
    - Path: 'rankings'
    - Method: GET
    - Parameters: none
    - Returns: UserForms.
    - Description: Returns a list of players in the database with at least one gameplay ordered by win rate (number of game won x 100 / number of game played).
    
 - **get_player_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: player_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: Gets the history of a game (Players' moves).

##Models Included:
 - **Player**
    - Stores unique player_name and email address. Optional fields (default to 0) such as number of games played and won.
    
 - **Game**
    - Stores unique game states. Associated with Player model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Player model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, setup,
    status, host, oppoent, date, next_turn).
 - **NewGameForm**
    - Used to create a new game (host_name, oppoent_name)
 - **MakeMoveForm**
    - Inbound make move form (player_name, move).
 - **ScoreForm**
    - Representation of a completed game's Score (urlsafe_key, host_name, host_result, oppoent_name, oppoent_result, date).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **UserForm**
    - Representation of a Player (urlsafe_key, host_name, host_result, oppoent_name, oppoent_result, date).
 - **UserForms**
    - Multiple UserForm container.
 - **StringMessage**
    - General purpose String container.