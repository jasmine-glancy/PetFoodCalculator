"""A program that calls the Nutrition API from FatSecret to provide amounts
of human food to give to dogs and cats without unbalancing their diet"""

# Using Blueprint 
import json
import find_info as fi
from flask import Blueprint, flash, render_template, session, \
    url_for, redirect, request
from fractions import Fraction
import time
import os 
import re
import requests

# Define the Blueprint
human_foods = Blueprint("human_foods", __name__)

NUTRITION_API_URL = "https://platform.fatsecret.com/rest/server.api"
NUTRITION_CLIENT_ID = os.environ.get("NUTRITION_CLIENT_ID")
NUTRITION_API_SECRET = os.environ.get("NUTRITION_SECRET")
TOKEN_URL = "https://oauth.fatsecret.com/connect/token"

cached_token = None
token_expiration = 0

def get_oauth_token():
    """Generates OAuth token"""
    
    global cached_token, token_expiration

    # Check if the token is still valid
    if cached_token and time.time() < token_expiration:
        return cached_token

    if not NUTRITION_CLIENT_ID or not NUTRITION_API_SECRET:
        raise Exception("Client ID or Client Secret not set in environment variables")
    
    response = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": NUTRITION_CLIENT_ID,
        "client_secret": NUTRITION_API_SECRET,
        "scope": "basic"
    }, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })
    response_data = response.json()
    
    if "access_token" in response_data:
        cached_token = response_data["access_token"]
        # Set the token expiration time (assuming the token is valid for 1 hour)
        token_expiration = time.time() + response_data.get("expires_in", 3600)
        
        print(cached_token)
        return cached_token
    else:
        raise Exception(f"Failed to obtain access token: {response_data}")
   


@human_foods.route("/search_human_foods/<int:pet_id>", methods=["GET", "POST"])
def search_human_foods(pet_id):
    """Looks up a list of corresponding human foods in
    the Fatscreen food database"""

    found_foods_json = request.args.get("found_foods", "[]")
    found_foods = json.loads(found_foods_json)


    if request.method == "POST":
        form_type = request.form.get("form_type")
        print(f"Form type: {form_type}")  

        if form_type == "search":
            # Handle the search form submission
            food_name = request.form.get("food_name")
            print(food_name)
            
            params = {
                "method":"foods.search",
                "search_expression":food_name,
                "format":"json"
            }
            
            token = get_oauth_token()
            
            headers = {
                "Content-Type":"application/json",
                "Authorization": f"Bearer {token}"
            }
            
            
            # Call the string against API 
            api_response = requests.get(NUTRITION_API_URL, params=params, headers=headers)
            
            if api_response.status_code == 200:
                # If the string matches anything in the  API, call a list
                data = api_response.json()
                print(data)
                found_foods = []
                
                foods_list = data.get("foods", {}).get("food", [])

                
                for item in foods_list:
                    
                    print(item)
                    description = item.get("food_description", None)
                    food_name = item.get("food_name", None)
                    food_type = item.get("food_type", None)
                    food_id = item.get("food_id", None)
                    
                    if food_type == "Brand":
                        brand_name = item.get("brand_name", None)
                    else:
                        brand_name = "Generic"
                        
                    serving_size = description.split("|")[0]
                    serving_size_unit_full = serving_size.split("-")[0].strip()
                    
                    print(f"Serving size unit full: '{serving_size_unit_full}'")

                    # Use regular expression to find the serving size number and unit
                    match = re.search(r'Per\s+([\d/.]+)\s*([a-zA-Z]+)', serving_size_unit_full)
                    
                    if match:
                        serving_size_unit_number = match.group(1)
                        serving_size_unit = match.group(2)
                        
                        # Convert fraction to decimal if necessary
                        try:
                            serving_size_unit_number = float(Fraction(serving_size_unit_number))
                        except ValueError:
                            serving_size_unit_number = "Unknown"
                    else:
                        serving_size_unit_number = "Unknown"
                        serving_size_unit = "Unknown"
                        
                    # Debugging: Print the extracted number and unit
                    print(f"Extracted serving size number: '{serving_size_unit_number}'")
                    print(f"Extracted serving size unit: '{serving_size_unit}'")

                    calories = serving_size.split("-")[1].split(":")[1]
                    calorie_number = calories.split("kcal")[0]
                    
                    print(brand_name, food_name, description, serving_size, serving_size_unit_full, serving_size_unit_number, calories, calorie_number)
                    
                    # Build a new dictionary to iterate over
                    food_info = {
                        "description": description,
                        "food_name": food_name,
                        "food_type": food_type,
                        "brand_name": brand_name,
                        "serving_size_number": float(serving_size_unit_number),
                        "serving_size_unit": serving_size_unit,
                        "serving_size_string": serving_size_unit_full,
                        "num_calories": int(calorie_number),
                        "calorie_string": calories,
                        "food_id": food_id
                    }
                        
                    found_foods.append(food_info)
                        
                print(f"Found foods: {found_foods}")
                
                # Serialize found_foods to JSON
                found_foods_json = json.dumps(found_foods)
                
                
                return redirect(url_for("human_foods.search_human_foods", found_foods=found_foods_json, pet_id=pet_id))
            else:
                # Otherwise, provide an error message
                flash("Food not found. Please try again!")
                
                return redirect(url_for("human_foods.search_human_foods", pet_id=pet_id))
        elif form_type == "select":
            
            # Handle the form submission for selecting a food item
            selected_food = {
                "food_name": request.form.get("food_name"),
                "food_type": request.form.get("food_type"),
                "brand_name": request.form.get("brand_name"),
                "serving_size_number": request.form.get("serving_size_number"),
                "serving_size_unit": request.form.get("serving_size_unit"),
                "serving_size_string": request.form.get("serving_size_string"),
                "num_calories": request.form.get("num_calories"),
                "calorie_string": request.form.get("calorie_string"),
                "food_id": request.form.get("food_id")
            }
            
            # Process the selected food item as needed
            print(f"Selected food: {selected_food}")
            
            # Serialize selected_food to JSON
            selected_food_json = json.dumps(selected_food)
            
            # Redirect to the calculate_treat_amounts route with the selected food details
            return redirect(url_for("human_foods.calculate_treat_amounts", selected_food=selected_food_json, pet_id=pet_id))
                
    return render_template("query_human_food.html", found_foods=found_foods, pet_id=pet_id)

@human_foods.route("/calculate_treat_amounts", methods=["GET", "POST"])
def calculate_treat_amounts():
    """Finds the max amount of the chosen human food 
    the pet can have"""
    
    try:
        pet_id = request.args.get("pet_id")
        find_info = fi.FindInfo(session["user_id"], pet_id) 
        print(f"pet ID: {pet_id}")
    except Exception as e:
        print(f"Couldn't find ID, Exception: {e}")
        return "Error: Couldn't find ID", 400
    
    selected_food_json = request.args.get("selected_food", "{}")
    selected_food = json.loads(selected_food_json)

    if request.method == "POST":
        form_type = request.form.get("form_type")
        
        if form_type == "select":
            
            # Store the selected food in the session
            session["selected_food"] = selected_food
            
            # Process the selected food item as needed
            print(f"Selected food: {selected_food}, food name: {selected_food['food_name']}")
            
        # Call max treat amount per day from pet_food_calculator.db
        max_treat_kcal = find_info.find_max_treat_amounts(pet_id)
        print(max_treat_kcal)

        pet_data = find_info.pet_data_dictionary(session["user_id"], pet_id)
        
        return render_template("calculate_human_food_amts.html", max_treat_kcal=max_treat_kcal, pet_data=pet_data, selected_food=selected_food)

    # Call default values if not a POST request
    max_treat_kcal = find_info.find_max_treat_amounts(pet_id)
    pet_data = find_info.pet_data_dictionary(session["user_id"], pet_id)
    
    # Process the selected food item as needed
    print(f"Selected food: {selected_food}, food name: {selected_food['food_name']}")
    
    total_calories = float(selected_food["num_calories"])
    serving_size = float(selected_food["serving_size_number"])
    
    print(serving_size, type(serving_size))
    print(max_treat_kcal, type(max_treat_kcal))
    
    # Calculate calories per unit
    calories_per_unit = total_calories / serving_size
    
    # Calculate amount of units for the max treat amount
    treat_amounts = round((max_treat_kcal / calories_per_unit), 2)
    
    serving_units = selected_food["serving_size_unit"]
    
    print(f"Treat amounts: {treat_amounts} {serving_units}")
    
    return render_template("calculate_human_food_amts.html",
                           max_treat_kcal=max_treat_kcal,
                           pet_data=pet_data,
                           selected_food=selected_food,
                           treat_amounts=treat_amounts,
                           serving_units=serving_units,
                           pet_id=pet_id)
    


        # TODO: Display human food treat amounts on the final report
        # # Database table? ID corresponding to a FK to USDA Treat Amounts table
        # # Limit to one option for now
        

