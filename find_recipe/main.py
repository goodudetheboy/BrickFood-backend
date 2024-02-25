import functions_framework, json, os, time
from openai import OpenAI
from dotenv import load_dotenv
from firestore import db

load_dotenv()

headers = {"Access-Control-Allow-Origin": "*"}

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


@functions_framework.http
def find_recipe(request):
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
    request_json["timestamp"] = int(time.time())

    cuisine = request_json["cuisine"]
    ingrs = request_json["ingrs"]

    # load menu
    print("Loading menu info from dining hall")
    f = open("menu.json")
    menu = json.load(f)["menu"]
    print("Menu from dining hall loaded!")

    # prepare prompts and make request for recipe
    print("Sending request for recipe to gpt-4")
    recipe_json_format = """
        {
            "foodName": <name of the recipe>,
            "ingrs": <array of ingredients, in the form of object Ingr {
                "name": <the name of the recipe>
                "station": <the station from which to get the ingredients>
            }>,
            "recipe": <array of string, where each string is a recipe step, do not include station's name>
        }
    """
    system_prompt = f"""
        Given below is a list of food and ingredients at a dining hall, where each station's name is listed in capital, followed by the ingredients available in each station. Given a type of cuisine from a country from the user, your task is to generate a way to use the ingredients currently at the dining hall to make a new dish inspired the given cuisine. Note that the user does not have ANY COOKING UTENSILS, and so they cannot cook their food. The user will also have a list of preferred ingredients. To the best of your abilities, taking account of the preferred lists, generate and reply with only and only the recipe in the following JSON format:
        {recipe_json_format}
        DO NOT INCLUDE THE STATION'S NAME IN THE INSTRUCTION. If you cannot make a reasonable recipe, please respond with "foodName": "none"
        The user would like to eat {cuisine}-inspired food today. Here are the type of ingredients they want to be included in the recipe {ingrs}. What can they use from the dining hall?
        Here are the ingredients at the dining hall: {menu}
    """
    # send request to gpt-4
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"I would like to eat {cuisine}-inspired food today. What can I use from my dining hall?",
            },
        ],
    )

    # recipe generated, prepping for image generation
    print("Response received from gpt-4!")
    generated_recipe = response.choices[0].message.content
    json_recipe = json.loads(generated_recipe)
    json_recipe["timestamp"] = int(time.time())

    # check if gpt-4 were able to make something
    if json_recipe["foodName"] != "none":
        # prepare image prompt
        print("Valid recipe generated, generating image")
        image_prompt = f"""
            Generate a presentable and realistic image of a dish to be put on a menu based on the following recipe: {generated_recipe}
        """
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        # successfully generated
        print("Image generated!")
        generated_image = image_response.data[0].url
        json_recipe["imageUrl"] = generated_image

    print("Adding result to database")
    # add to recipes database
    recipe_ref = db.collection("recipes").document()
    recipe_id = recipe_ref.id
    recipe_ref.set(json_recipe)
    # set id of returning recipe
    json_recipe["id"] = recipe_id

    # add to recipe requests database
    request_ref = db.collection("recipe_requests").document()
    # link recipe to recipe request
    request_json["recipeId"] = recipe_id
    request_ref.set(request_json)

    print("Result added to database")

    return ({"response": json_recipe}, 200, headers)
