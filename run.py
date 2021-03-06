from tornado.ncss import Server
import engine.template as template
import db.api as api
import re


login_info = {}
users = {"bruce":{"user_id":1, "password":"tonotbe"},
         "alex":{"user_id":2, "password":"gags"},
         "deanna":{"user_id":3, "password":"traitor"},
         "aaron":{"user_id":4, "password":"mafiatalk"},
         "greta":{"user_id":5, "password":"securecookie"} }
username_regex = re.compile(r"^[a-zA-Z0-9\-_]{3,20}$")
password_regex = re.compile(r"^[ -~]{1,128}$")
# Define a function which returns the HTML for a page.
#def index(response):
   # user_id = response.get_secure_cookie("user_id")
   # if user_id == None:
   #    response.write("Hello World")
   # else:
   #    response.write("Hello, " + str(user_id))

# A function for another page, which shows something else.

def not_mine(userid, questid):
    return userid != api.Question.find(questid).creator_id


def is_disabled(userid, questid):
    all_votes = api.Vote.find_all(voter_id=userid, qid=questid)
    if any(userid == vote.voter_id for vote in all_votes):
        return "disabled"
    else:
        return " "

def is_checked(userid, questid, vote):
    user_vote = api.Vote.find_all(qid=questid, voter_id=userid)
    if len(user_vote) > 0:
        print('vote cast. input', vote, 'user', user_vote[0].vote)
        if str(user_vote[0].vote) == str(vote):
            print("yussss")
            return True
        else:
            return False
    else:
        print("not checked")
        return False


def page_not_found(response):
    response.redirect("/404")

def _404(response):
    current_user = get_user_from_response(response)
    response.write(template.render_page("404.html", {"questions" : api.Question.find_all(), "current_user": current_user}))
    
def about(response):
    current_user = get_user_from_response(response)
    response.write(template.render_page("about.html", {"questions" : api.Question.find_all(), "current_user": current_user}))

def view_question(response):
    current_user = get_user_from_response(response)
    if current_user is None:
        # to do: redirect to new user index page (splash.html... I think)
        response.redirect("/login")
    else:
        context = {"questions" : api.Question.find_all_home_specific(), "count_votes": count_votes, "current_user": current_user, "message":None, 'is_checked': is_checked, 'is_disabled' : is_disabled, 'not_mine': not_mine}
        response.write(template.render_page("q_view.html", context))

def create_question(response):
    current_user = get_user_from_response(response)
    response.write(template.render_page("q_create.html", {"message": None, "current_user": current_user, "statement0" : '', "statement1" : '', "statement2" : '' , "name" : ''}))

def insert_new_question(response):
    #recieves data from sent form and redirects to viewing new question
    if any(response.get_field("statement_" + number) is None for number in ("one", "two", "three")):
        response.redirect('/')
        return # replace this with an else later, I'm kinda lazy -Michael
    current_user = get_user_from_response(response)
    name = response.get_field("name").strip()
    statement0 = response.get_field("statement_one").strip()
    statement1 = response.get_field("statement_two").strip()
    statement2 = response.get_field("statement_three").strip()

    fields = [statement0, statement1, statement2]
    
    if not any(statement == "" for statement in (fields)):
        if len(statement0) < 128 and  len(statement1) < 128 and len(statement2) < 128:
            if name != "":
                if statement0 != statement1 and statement1 != statement2 and statement0 != statement2:
                    lie = response.get_field("lie")
                    user_id = get_user_from_response(response).uid #the id of the user
                    name = response.get_field("name").strip() #the name of the question
                    api.Question.create(statement0, statement1, statement2, lie, user_id, name)
                    response.redirect("/")
                else:
                    response.write(template.render_page("q_create.html", {"message" : 'Please enter 3 different statements', "current_user": current_user, "statement0" : statement0, "statement1" : statement1, "statement2" : statement2, "name" : name }))
            else:
                response.write(template.render_page("q_create.html", {"message" : 'Please enter question name', "current_user": current_user, "statement0" : statement0, "statement1" : statement1, "statement2" : statement2, "name" : name }))
        else:
            response.write(template.render_page("q_create.html",  {"message" : 'Character limit exceeded 128 characters' , "current_user": current_user, "statement0" : statement0, "statement1" : statement1, "statement2" : statement2, "name" : name }))
    else:
        response.write(template.render_page("q_create.html", {"message" : 'Please enter 3 non-empty statements' , "current_user": current_user, "statement0" : statement0, "statement1" : statement1, "statement2" : statement2 , "name" : name}))
        

def login(response):
    current_user = get_user_from_response(response)
    if current_user is None:
        username = response.get_field("username")
        password = response.get_field("password")
        if username is None or password is None:
            response.write(template.render_page("login.html", {"message": None, "current_user": current_user}))
        else:
            if api.User.find(username) is not None:
                user = api.User.find(username)
                if api.User.hash_password(password) == user.password:
                    print("Login successful.")
                    response.set_secure_cookie("user_id", str(user.uid))
                    response.redirect("/")
                else:
                    print("Login failed. Incorrect username or password.")
                    response.write(template.render_page("login.html", {"message": "Username or password incorrect.", "current_user": current_user}))
            else:
                response.write(template.render_page("login.html", {"message": "Username or password incorrect.", "current_user": current_user}))
    else:
        response.write(template.render_page("q_view.html", {"questions" : api.Question.find_all(), "count_votes": count_votes, "current_user": current_user, "message":'You are already logged in!'}))
        

        '''login_info["username"] = username
        login_info["password"] = password
        if login_info["username"] in users and login_info["password"] == users[login_info["username"]]["password"]:
            print("Login successful.")
            response.set_secure_cookie("user_id", str(users[login_info["username"]]["user_id"]))
            response.redirect("/")'''
        
    
    
def logout(response):
    response.clear_cookie("user_id")
    #response.write("You have logged out.")
    response.redirect("/")

# Input: Response object
# Output: Current User object from response or None
# tl;dr: put this in any function:
# current_user = get_user_from_response(response)
def get_user_from_response(response):
    user_id = response.get_secure_cookie("user_id")
    if user_id is None:
        return None
    else:
        return api.User.find(uid=int(user_id))

def register(response):
    current_user = get_user_from_response(response)
    if current_user is None:
        username = response.get_field("username")
        password = response.get_field("password")
        confirm_password = response.get_field("confirm_password")
        
        if username is None or password is None or confirm_password is None:
            response.write(template.render_page("register.html", {'message': None, "current_user": current_user}))
        elif ' ' in username or ' ' in password or ' ' in confirm_password:
            response.write(template.render_page("register.html", {'message': 'No spaces allowed!', "current_user": current_user}))
        elif  username == '' or password == '' or confirm_password == '':
            response.write(template.render_page("register.html", {'message': 'Username or password was empty or had a space!', "current_user": current_user}))
        elif api.User.find(username):
            response.write(template.render_page("register.html", {'message': 'Username is taken already!', "current_user": current_user}))
        elif password != confirm_password:
            response.write(template.render_page("register.html", {'message': 'Passwords do not match!', "current_user": current_user}))
        elif re.match(username_regex, username) is None:
            response.write(template.render_page("register.html", {'message': 'Usernames must be between 3 to 16 characters in length and must have alphanumeric characters, dashes or underscores.', "current_user": current_user}))
        elif re.match(password_regex, password) is None:
            response.write(template.render_page("register.html", {'message': 'Passwords must be between 1 to 128 characters in length and must have printable ASCII characters.', "current_user": current_user}))
        else:
            user = api.User.create(username, api.User.hash_password(password).decode("ascii"))
            response.set_secure_cookie("user_id", str(user.uid))
            response.redirect("/")
    else:
        response.write(template.render_page("q_view.html", {"questions" : api.Question.find_all(), "count_votes": count_votes, "current_user": current_user, "message":'You are already logged in!'}))


# check whether the selection is the lie
def vote(response):
    user_input = response.get_field("user_input")
    question_id = int(response.get_field("id")) if response.get_field('id') is not None else response.redirect('/')
    question = api.Question.find(question_id)
    current_user = get_user_from_response(response)
          
    if current_user.uid == question.creator_id:
        response.write(template.render_page("q_view.html", {"questions" : api.Question.find_all(), "count_votes": count_votes, "current_user": current_user, "message":'You cannot vote on the question. (You are the author)'}))
    elif current_user is not None and len(api.Vote.find_all(qid = question_id, voter_id = current_user.uid)) == 0:
        vote = api.Vote.create(question_id, int(user_input), current_user.uid)
#        print(vote.vote)
#        print(question.lie)
#        if vote.vote == question.lie:
#            current_user.add_points()
        response.redirect('/question/' + str(question_id))
        print(vote.vote)
        print(question.lie)
        if vote.vote == question.lie:
            question_correct_votes = len(api.Vote.find_all(qid = question.qid, vote = question.lie))
            points_to_add = 20 - min(question_correct_votes, 10)
            print(points_to_add)
            current_user.add_points(points_to_add)
        #response.write(template.render_page("q_view.html", {"questions" : api.Question.find_all(), "count_votes": count_votes, "current_user": current_user, "message":'You have already voted!'}))
    else:
        response.write(template.render_page("q_view.html", {"questions" : api.Question.find_all(), "count_votes": count_votes, "current_user": current_user, "message":'You have already voted!'}))
        

def count_votes(question_id):
    count_statement0 = len(api.Vote.find_all(question_id, vote=0))
    count_statement1 = len(api.Vote.find_all(question_id, vote=1))
    count_statement2 = len(api.Vote.find_all(question_id, vote=2))
    votes = [count_statement0, count_statement1, count_statement2]

    total = sum(votes)
    return total


def question_handler(response, question_id):
    # the regex ensures that the question_id can't be negative
    current_user = get_user_from_response(response)
    question_id = int(question_id)
    question = api.Question.find(question_id)
    if question is None:
        response.write(template.render_page("q_view.html", {"questions" : api.Question.find_all(), "count_votes": count_votes, "current_user": current_user, "message":'Invalid Question ID!'}))
        return
    question_author = question.get_creator()
    
    #only display the voting results if the user has voted
    current_user = get_user_from_response(response)
    context =  {'pageName' : 'View Post',"question" : question, "current_user": current_user, "count_votes": count_votes, "author": question_author, 'disabled': ''}
    if current_user is not None:
        if len(api.Vote.find_all(qid = question_id, voter_id = current_user.uid)) > 0:
            #count the votes for the statements and store
            count_statement0 = len(api.Vote.find_all(question_id, vote=0))
            count_statement1 = len(api.Vote.find_all(question_id, vote=1))
            count_statement2 = len(api.Vote.find_all(question_id, vote=2))
            votes = [count_statement0, count_statement1, count_statement2]

            total = sum(votes)
            
            score0 = str(round((votes[0] / total)*100))
            score1 = str(round((votes[1] / total)*100))
            score2 = str(round((votes[2] / total)*100))

            context["voted"] = True
            current_vote = api.Vote.find_all(qid = question_id, voter_id = current_user.uid)[0]
            context["vote"] = current_vote
            context["scores"] = [score0,score1,score2]
        else:
            #user is logged in but has not voted
            context["voted"] = False
        print(context)
        response.write(template.render_page("q_individual.html", context ))
                          
    else:
        #user is not logged in
        response.redirect('/login')

def profile_handler(response, user_name): 
    current_user = get_user_from_response(response)
    user_name = str(user_name)
    user_profile = api.User.find(user_name)
    if user_profile is not None:
        print(user_name)
        print(user_profile)
        response.write(template.render_page('profile.html', {
            'username' : user_profile.username, 
            "questions" : api.Question.find_all(user_profile.uid), 
            "current_user": current_user, 
            "points": user_profile.points}))
    else:
        response.redirect('/404')


def statistics_handler(response):
    current_user = get_user_from_response(response)
    response.write(template.render_page('statistics.html', {
        "number_of_votes": len(api.Vote.find_all()),
        "number_of_correct_votes": api.Vote.number_of_correct_votes(),
        "number_of_questions": len(api.Question.find_all()),
        "current_user": current_user}))

def scoreboard_handler(response):
    current_user = get_user_from_response(response)
    top_users = api.User.find_best(10)
    response.write(template.render_page('scoreboard.html', {
        "top_users": top_users,
        "current_user": current_user}))
    

# Make a server object so we can attach URLs to functions.
server = Server()

# This says that localhost:8888/ should display the result of the
# "index" function.
#server.register("/", index)
server.register("/", view_question)
server.register("/about", about)
server.register("/question/create", create_question)
server.register("/question/insert", insert_new_question)
server.register("/login", login)
server.register("/logout", logout)
server.register("/register", register)
server.register("/question/answer",vote)
server.register(r"/question/(\d+)", question_handler)
server.register(r'/profile/(\w+)', profile_handler)
server.register("/stats", statistics_handler)
server.register("/scoreboard", scoreboard_handler)
server.register("/404", _404)
server.register(r"/.+", page_not_found) 
# Start the server. Gotta do this.
server.run()
