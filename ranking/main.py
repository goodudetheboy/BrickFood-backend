import functions_framework, json, datetime
from dotenv import load_dotenv
from firestore import db
from google.cloud.firestore_v1.base_query import FieldFilter

load_dotenv()

headers = {"Access-Control-Allow-Origin": "*"}


@functions_framework.http
def ranking(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    #"""
    # start request
    print("Initializing connection to server")

    body_data = request.get_data()
    request_json = json.loads(body_data)

    action = request_json["action"]

    # checking provided actions
    if action == "like_recipe" or action == "unlike_recipe":
        # reaction to recipe, like and unlike
        recipe_id = request_json["recipeId"]
        print(f"Updating recipe {recipe_id} vote count with action {action}")
        response = react_recipe(request_json["recipeId"], action == "like_recipe")

        if response is False:
            print(f"Some error happened during updating react recipe using {action}")
            return ({"error": "Unable to update vote count"}, 400, headers)
        else:
            print(f"Succesfully updated recipe vote count using {action}")
            return (
                {"response": f"Succesfully updated vote count using {action}"},
                200,
                headers,
            )

    elif action == "view_todays_ranking":
        # compose and sort today's ranking
        print("Composing ranking in the day of the given timestamp")
        rankings = compose_recipes_ranking(int(request_json["timestamp"]))
        print("Ranking succesfully composed!")
        return ({"response": rankings}, 200, headers)
    else:
        return ({"error": "Invalid action provided."}, 400, headers)

    # return ({"response": ""}, 200, headers)


def react_recipe(recipe_id, is_like):
    # get data from database
    recipe_ref = db.collection("recipes").document(recipe_id)
    recipe_doc = recipe_ref.get()

    # check if exists
    if not recipe_doc.exists:
        return False

    # get actual data object
    recipe_data = recipe_doc.to_dict()

    # check if already exists
    if "voteCount" not in recipe_data:
        recipe_data["voteCount"] = 1 if is_like else 0
    else:
        recipe_data["voteCount"] += 1 if is_like else -1

    # update recip data on db
    recipe_ref.set(recipe_data)

    return True


def compose_recipes_ranking(timestamp):

    start_day, end_day = get_start_and_end_of_day(timestamp)
    print(start_day, end_day)
    recipes_ref = db.collection("recipes")

    recipes_ranking_docs = (
        recipes_ref.where(filter=FieldFilter("timestamp", ">=", start_day)).where(
            filter=FieldFilter("timestamp", "<=", end_day)
        )
    ).get()

    recipes_ranking = []

    for recipe_doc in recipes_ranking_docs:
        recipes_ranking.append(recipe_doc.to_dict())

    recipes_ranking = sorted(recipes_ranking, key=lambda d: -d["voteCount"])

    return recipes_ranking


def get_start_and_end_of_day(timestamp):
    """
    Get the start and end of the day in Python given a timestamp.

    Args:
      timestamp: A timestamp in seconds.

    Returns:
      A tuple containing the start and end of the day in datetime objects.
    """

    # Convert the timestamp to a datetime object.
    datetime_object = datetime.datetime.fromtimestamp(timestamp)

    # Get the start of the day.
    start_of_day = datetime_object.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get the end of the day.
    end_of_day = datetime_object.replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    # Return the start and end of the day.
    return int(start_of_day.timestamp()), int(end_of_day.timestamp())
