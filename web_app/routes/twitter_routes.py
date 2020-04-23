# web_app/routes/twitter_routes.py

from flask import Blueprint, render_template, jsonify

from web_app.models import User, Tweet, db, parse_records
from web_app.services.twitter_service import twitter_api
from web_app.services.basilica_service import basilica_api_client

twitter_routes = Blueprint("twitter_routes", __name__)

@twitter_routes.route("/users/<screen_name>/fetch") #/fetch?
def fetch_user_data(screen_name=None):
    print(screen_name)
    api = twitter_api()
    user = api.get_user(screen_name)
    statuses = api.user_timeline(screen_name, tweet_mode="extended", count=150)
    #return jsonify({"user": user._json, "tweets_count": len(statuses)})

# get existing user from the db or initialize a new one:
    db_user = User.query.get(user.id) or User(id=user.id)
    db_user.screen_name = user.screen_name
    db_user.name = user.name
    db_user.location = user.location
    db_user.followers_count = user.followers_count
    db.session.add(db_user)
    db.session.commit()
    #return "OK"
    #breakpoint()

    basilica_api = basilica_api_client()

    all_tweet_texts = [status.full_text for status in statuses]
    embeddings = list(basilica_api.embed_sentences(all_tweet_texts, model="twitter"))
    print("NUMBER OF EMBEDDINGS", len(embeddings))

    # TODO: explore using the zip() function maybe...
    counter = 0
    for status in statuses:
        print(status.full_text)
        print("----")
        #print(dir(status))
        # get existing tweet from the db or initialize a new one:
        db_tweet = Tweet.query.get(status.id) or Tweet(id=status.id)
        db_tweet.user_id = status.author.id # or db_user.id
        db_tweet.full_text = status.full_text
        #embedding = basilica_client.embed_sentence(status.full_text, model="twitter") # todo: prefer to make a single request to basilica with all the tweet texts, instead of a request per tweet
        embedding = embeddings[counter]
        print(len(embedding))
        db_tweet.embedding = embedding
        db.session.add(db_tweet)
        counter+=1
    db.session.commit()
    #breakpoint()
    return "OK"
    #return render_template("user.html", user=db_user, tweets=statuses) # tweets=db_tweets


@twitter_routes.route("/users")
def list_users_human_friendly():
    db_users = User.query.all()
    return render_template("users.html", users=db_users)

@twitter_routes.route("/users.json")
def list_users():
    db_users = User.query.all()
    users_response = parse_records(db_users)
    return jsonify(users_response)

@twitter_routes.route("/users/<screen_name>")
def get_user(screen_name=None):
    print(screen_name)
    db_user = User.query.filter(User.screen_name == screen_name).one()
    return render_template("user.html", user=db_user, tweets=db_user.tweets)