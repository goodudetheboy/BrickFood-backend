import functions_framework, json, os
from openai import OpenAI


headers = {"Access-Control-Allow-Origin": "*"}

client = OpenAI(
    # api_key=os.environ.get("OPENAI_API_KEY"),
    api_key="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",
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
    """
    # body_data = request.get_data()
    # request_json = json.loads(body_data)

    # cuisine = request_json["cuisine"]
    # ingrs = request_json["ingrs"]

    f = open("menu.json")
    menu = json.load(f)["menu"]

    # system_prompt = (
    #     """
    #         Given below is a list of food and ingredients at a dining hall, where each station's name is listed in capital, followed by the ingredients available in each station. Given a type of cuisine from a country from the user, your task is to generate a way to use the ingredients currently at the dining hall to make a new dish inspired the given cuisine. Note that the user does not have ANY COOKING UTENSILS, and so they cannot cook their food. Generate and reply with only and only the recipe in the following JSON format:
    #         {
    #             "foodName": <name of the recipe>,
    #             "ingrs": <array of ingredients, in the form of object Ingr {
    #                 "name": <the name of the recipe>
    #                 "station": <the station from which to get the ingredients>
    #             }>,
    #             "recipe": <array of string, where each string is a recipe step, do not include station's name>
    #         }

    #         DO NOT INCLUDE THE STATION'S NAME IN THE INSTRUCTION. If you cannot make a reasonable recipe, please respond with "foodName": "none"
    #     I would like to eat Chinese-inspired food with meat today. What can I use from my dining hall?
    #     Here are the ingredients at the dining hall:
    # """
    #     + menu
    # )
    # response = client.chat.completions.create(
    #     model="gpt-4-turbo-preview",
    #     response_format={"type": "json_object"},
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": system_prompt,
    #         },
    #         {
    #             "role": "user",
    #             "content": "I would like to eat Chinese-inspired food today. What can I use from my dining hall?",
    #         },
    #     ],
    # )

    # generated_recipe = response.choices[0].message.content
    generated_recipe = """
{
    "foodName": "BBQ Chicken Lettuce Wraps",
    "ingrs": [
        {
            "name": "Lettuce",
            "station": "Build Your Own Salad"
        },
        {
            "name": "Pulled Chicken",
            "station": "LOW N SLOW BBQ"
        },
        {
            "name": "Peas and Carrots",
            "station": "SIDES"
        },
        {
            "name": "Cajun Corn",
            "station": "LOW N SLOW BBQ"
        }
    ],
    "recipe": [
        "Gather lettuce leaves to use as cups for the wraps.",
        "Fill each lettuce cup with a scoop of pulled chicken.",
        "Top the chicken with a mix of peas and carrots.",
        "Add a spoonful of Cajun corn for a spicy kick.",
        "Enjoy your wraps cold, as a refreshing and crunchy dish."
    ]
}"""
    image_prompt = (
        """
        Generate a presentable and realistic image of a dish based on the following recipe:
    """
        + generated_recipe
    )

    image_response = client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    generated_image = image_response.data[0].url

    json_recipe = json.loads(generated_recipe)
    json_recipe["imageUrl"] = generated_image

    return ({"response": json_recipe}, 200, headers)


find_recipe({})
