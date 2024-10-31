"""Welcome to the Pet Food Calculator!"""

from calculate_food import CalculateFood
from cs50 import SQL
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_bootstrap import Bootstrap
from forms import NewSignalment, GetWeight, ReproStatus, LoginForm, RegisterForm, WorkForm, FoodForm
from find_info import FindInfo
from helpers import clear_variable_list, login_required
import os
from nutrition_api import human_foods
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Add in Bootstrap
Bootstrap(app)

# Load environmental variables

app.config['SECRET_KEY'] = os.environ.get('KEY')


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///pet_food_calculator.db")

# Register the blueprint for human foods
app.register_blueprint(human_foods)

@app.route("/")
def home():
    """Includes welcome and disclaimers along with login/register buttons"""
    
    user_id = session.get("user_id")
    if user_id:
        user = db.execute(
            "SELECT username FROM users WHERE id = :user_id",
            user_id=session["user_id"]
        )
        
        username = user[0]["username"]
        
        return render_template("index.html", user=username)
    return render_template("index.html")


@app.route("/calculate_new_pet")
def new_pet_calc():
    """Redirects to the start of the form, while clearing session variables"""
    session["previous_route"] = "new_pet"
    
    # Clear variables (except user ID)
    clear_variable_list()
    
    return redirect(url_for('pet_info'))


@app.route("/recalculate_for_pet")
def recalculate_pet():
    """Redirects to the start of the form, while clearing session variables"""
    session["previous_route"] = "recalculate"
    
    # Clear variables (except user ID)
    clear_variable_list()
    
    return redirect(url_for('finished_reports'))

            
@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs an existing user in"""
    form = LoginForm()
    
    # Checks if the user's data is validated 
    if form.validate_on_submit():

        # Check username and hashed password against the database
        user_lookup = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        
        if user_lookup == None:
            flash("Username not found.")
            return redirect(url_for('login'))
        
        # Ensure username exists and password is correct
        elif not check_password_hash(user_lookup[0]["password"], 
                                   request.form.get("password")):
            flash("Invalid password.")
            return redirect(url_for('login'))
        
        else:
            flash(f"Logged in as {request.form.get("username")}!")
            
            # Remember which user has logged in
            session["user_id"] = user_lookup[0]["id"]
    
        return render_template("index.html")
        
    
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registers a new user"""

    form = RegisterForm()
    
    if form.validate_on_submit():
        # Check user against info in the database
        find_user = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        
        # Check if username exists already in the database
        if len(find_user) != 0:
            flash("That username already taken.")
        # Check if the user's password matches the password verification
        elif request.form.get("password") != request.form.get("confirm_password"):
            flash("Passwords must match.")
        else:
            # If all checks pass, hash password
            hashed_password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
            
            # Insert new info into database
            db.execute("INSERT INTO users (username, password) VALUES(?, ?)", request.form.get("username"), hashed_password)
                
            user = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
            
            # Remember which user has logged in
            session["user_id"] = user[0]["id"]
            
            logged_in = True
            
            # Redirect to home
            return render_template("index.html", logged_in=logged_in)
    
    return render_template("register.html", form=form)


@app.route("/logout")
def logout():
    """Logs user out"""
    
    # Clears the user_id
    session.clear()
    
    # Redirect to home
    return redirect("/")


@app.route("/get-signalment/", methods=["GET", "POST"])
@login_required
def pet_info():
    """Gets the pet's signalment, i.e. name, age, sex/reproductive status, breed, species"""
    
    id = None
    try:
        pet_id = request.args.get("pet_id")
        
        fi = FindInfo(session["user_id"], pet_id) 
        print(f"pet ID: {pet_id}")
    except Exception as e:
        print(f"Couldn't find ID, Exception: {e}")
    else:
        print(f"user_id: {session['user_id']}, pet_id: {id}") 

        
    form = NewSignalment()
    
    if request.method == "POST":
        fi = FindInfo(session["user_id"], pet_id) 
        species = form.pet_species.data
        pet_name = form.pet_name.data.title()
        id = fi.find_pet_id(session["user_id"], pet_name, species) 
        session["pet_id"] = id 
        
        print(id)
        # Show an error message if the user doesn't choose a species
        if species == "default":
            flash("Please choose a species from the dropdown.")
            return redirect(url_for("pet_info", pet_id=id))

        if id != None:    
                
            print(f"user_id: {session['user_id']}, pet_id: {id}")  
            
            # See if the pet is already added
            find_existing_pet = fi.find_existing_pet(session["user_id"], id)
            print(find_existing_pet)
                
            if find_existing_pet:
                # If existing pet is found, update the data
                print("Existing pet found")
                try:
                    db.execute(
                        "UPDATE pets SET name = :updated_name, species = :updated_species \
                            WHERE pet_id = :pet_id AND owner_id = :user_id",
                        updated_name=pet_name, updated_species=species, pet_id=id, user_id=session["user_id"]
                        )
                except Exception as e:
                    flash(f"Unable to update data, Exception: {e}")
                    return redirect(url_for("pet_info", pet_id=id))
                else:
                    session["species"] = species
                    session["pet_name"] = pet_name
                    session["pet_id"] = id 
                    pet_id = id
                        
            else:
                # If no pet is found (i.e. new pet in the database), create new session variables and store pet
                
                print("New pet")
                try:
                    # Insert new pet data
                    db.execute(
                        "INSERT INTO pets (owner_id, name, species) VALUES (?, ?, ?)",
                        session["user_id"], pet_name, species
                    )
                        
                    print("Looking up new pet's ID")      
                                          
                    # Query the new pet's id 
                    pet_data = db.execute(
                        "SELECT pet_id, name FROM pets \
                            WHERE owner_id = :user_id AND name = :pet_name",
                            user_id=session["user_id"], pet_name=pet_name
                        )
                        
                    print(pet_data[0]["pet_id"], pet_data[0]["name"])
                    new_pet_id = pet_data[0]["pet_id"]
                        
                except Exception as e:
                    flash(f"Unable to insert and query new signalment data, Exception: {e}")
                    return redirect(url_for("pet_info", pet_id=id))
                else:
                    pet_id = new_pet_id
                    session["pet_id"] = pet_id
                        
                    # Update the pet_data dictionary with the new pet's id
                    pet_data[0]["pet_id"] = pet_id
                    fi = FindInfo(session["user_id"], pet_id) 

        # Store session variables
        session["species"] = species
        session["pet_name"] = pet_name
             
        fi = FindInfo(session["user_id"], pet_id)       
            
        print(pet_id, species, pet_name)        
            
        if pet_id is not None:
            return redirect(url_for('pet_info_continued', pet_id=pet_id))
        else:
            flash("Pet ID is not available. Please try again.")
            return redirect(url_for("pet_info", pet_id=id))
        
    return render_template("get_signalment.html", form=form)


@app.route("/get-signalment-pt-2/<int:pet_id>", methods=["GET", "POST"])
@login_required
def pet_info_continued(pet_id):
    """Gets the rest of pet's signalment, 
    i.e. name, age, sex/reproductive status, breed, species"""
    
    form = NewSignalment()
    
    try:
        print(f"pet ID: {pet_id}")
        fi = FindInfo(session["user_id"], pet_id) 
        # Use login check from find_info to verify species
        species = fi.login_check_for_species()
    except Exception as e:
        flash(f"Couldn't find ID, Exception: {e}")
        return redirect(url_for('pet_info_continued', pet_id=pet_id)) 
    else:
        # AKC Breeds by Size csv courtesy of MeganSorenson of Github 
        # # # https://github.com/MeganSorenson/American-Kennel-Club-Breeds-by-Size-Dataset/blob/main/AmericanKennelClubBreedsBySize.xlsx
        
        # Access breed data via database
        pet_breed = []
        if species == "Canine":
            canine_breed_list = db.execute(
                "SELECT Breed FROM dog_breeds ORDER BY Breed"
            )
            
            if canine_breed_list != None:
                pet_breed += canine_breed_list
                
        if species == "Feline":
            feline_breed_list = db.execute(
                "SELECT Breed FROM cat_breeds ORDER BY Breed"
            )
            if feline_breed_list != None:
                pet_breed += feline_breed_list
            
        
        if request.method == "POST":
            pet_sex = form.pet_sex.data
            pet_age_years = form.pet_age.data
            pet_age_months = form.pet_age_months.data 
            pet_breed = request.form.get("pet_breed")


            # Show an error message if the user doesn't choose a breed or sex
            if pet_breed == None and pet_sex == "default":
                flash("Please choose a breed and your pet's reproductive status from the dropdown menus.")
                return redirect(url_for('pet_info_continued', pet_id=pet_id))
            elif pet_breed == None and pet_sex != "default":
                flash("Please choose a breed from the dropdown menus.")
                return redirect(url_for('pet_info_continued', pet_id=pet_id))
            elif pet_breed != None and pet_sex == "default":
                flash("Please choose your pet's reproductive status from the dropdown menus.")
                return redirect(url_for('pet_info_continued', pet_id=pet_id))    
            elif pet_age_years < 0 or pet_age_months < 0:
                flash("Please enter 0 or a number greater than zero.")
                return redirect(url_for('pet_info_continued', pet_id=pet_id))    
            else:
                pet_sex = int(pet_sex)
                print(pet_age_years, pet_age_months)
                if pet_age_months > 12:
                    # If more than 12 months is input, add number to years
                    pet_age_years += pet_age_months / 12
                    
                    # Get the integer part of pet_age_years
                    pet_age_years_int = int(pet_age_years)  
                    
                    # Get the decimal part of pet_age_years
                    pet_age_years_decimal = pet_age_years - pet_age_years_int  

                    # Convert the decimal part of pet_age_years back to months
                    pet_age_months = round(pet_age_years_decimal * 12)

                    # Update pet_age_years to only include the integer part
                    pet_age_years = pet_age_years_int
                    
                print(pet_age_years, pet_age_months)
                    
                # Create new session variables
                session["pet_sex"] = pet_sex
                session["pet_age_years"] = pet_age_years
                session["pet_age_months"] = pet_age_months
                session["pet_breed"] = pet_breed
                
                # Convert months to years for easier logic reading
                partial_years = float(pet_age_months / 12)
                pet_age = pet_age_years + partial_years    
                
                print(pet_age)
                print(pet_sex, type(pet_sex))   
                
                # Set flags to see if a pet is between pediatric and sexually mature ages
                is_pediatric = "n"
                not_pediatric_not_mature = False
                sexually_mature = False
                # Search for pet breed code in breed database
                if species == "Canine":
                    breed_id_result = db.execute(
                        "SELECT BreedID FROM dog_breeds WHERE Breed = ?", pet_breed
                    )
                    
                    breed_id = breed_id_result[0]["BreedID"]
                
                    print(f"breed_id: {breed_id}")
                    
                    # Find breed size category
                    breed_size_results = db.execute(
                        "SELECT SizeCategory FROM dog_breeds WHERE BreedID = ?;", breed_id
                    )
                    
                    breed_size = breed_size_results[0]["SizeCategory"]
                    
                    print(breed_size)
                    
                    if breed_size == "X-Small" or breed_size == "Small" or breed_size == "Medium":
                        if pet_age < 0.33:
                            # Puppies under 4 months old have a DER modifier of * 3.0 factor_id 13
                            print("DER Modifier * 3.0")
                            der_factor_id = 13
                            is_pediatric = "y"
                        elif pet_age >= 0.33 and pet_age <= 0.66:
                            # Toy/small/medium breed puppies between 4 and 8 months of age have a DER modifier of * 2.5
                            print("DER Modifier * 2.5")
                            der_factor_id = 15
                            is_pediatric = "y"
                        elif pet_age > 0.66 and pet_age <= 1:
                            # Toy/small/medium breed puppies between 8 and 12 months of age have a DER modifier of * 1.8-2.0
                            print("DER Modifier * 1.8-2.0")
                            der_factor_id = 18
                            is_pediatric = "y"
                        elif pet_age > 1 and pet_age < 2:
                            # Toy/small/medium breed dogs that aren't pediatric but aren't sexually matue
                            not_pediatric_not_mature = True
                        else:
                            # Pets over 2 years old
                            sexually_mature = True
                                
                    elif breed_size == "Large":
                        if pet_age < 0.33:
                            # Large breed puppies under 4 months old have a DER modifier of * 3.0 factor_id 13
                            print("DER Modifier * 3.0")
                            der_factor_id = 13
                            is_pediatric = "y"
                        elif pet_age > 0.33 and pet_age <= 0.91:
                            # Large breed puppies between 4 and 11 months old have a DER modifier of * 2.5
                            print("DER Modifier * 2.5")
                            der_factor_id = 16
                            is_pediatric = "y"
                        elif pet_age > 0.91 and pet_age <= 1.5:
                            # Large breed puppies between 11 and 18 months old have a DER modifier of * 1.8-2.0
                            print("DER Modifier * 1.8-2.0")
                            der_factor_id = 18
                            is_pediatric = "y"
                        elif pet_age > 1.5 and pet_age < 2:
                            # Large breed dogs that aren't pediatric but aren't sexually matue
                            not_pediatric_not_mature = True
                        else:
                            # Pets over 2 years old
                            sexually_mature = True
                            
                    elif breed_size == "X-Large":
                        if pet_age < 0.33:
                            # X-Large breed puppies under 6 months old have a DER modifier of * 3.0 factor_id 13
                            der_factor_id = 13
                            print("DER Modifier * 3.0")
                            is_pediatric = "y"
                        if pet_age > 0.5 and pet_age <= 1:
                            # X-Large breed puppies between 6 and 12 months old have a DER modifier of * 2.5
                            print("DER Modifier * 2.5")
                            der_factor_id = 17
                            is_pediatric = "y"
                        elif pet_age > 1 and pet_age <= 1.5:
                            # X-Large breed puppies between 12 and 18 months old have a DER modifier of * 1.8-2.0
                            print("DER Modifier * 1.8-2.0")
                            der_factor_id = 20
                            is_pediatric = "y"
                        elif pet_age > 1.5 and pet_age < 2:
                            # X-Large breed dogs that aren't pediatric but aren't sexually matue
                            not_pediatric_not_mature = True
                        else:
                            # Pets over 2 years old
                            sexually_mature = True
                            
                            
                    # List for condensed conditionals suggested by CoPilot
                    if not_pediatric_not_mature or sexually_mature:
                        if pet_sex == 2 or pet_sex == 4:
                            # Non-pediatric, sexually immature and older dogs that are neutered or spayed
                            print("DER Modifier * 1.4-1.6")
                            der_factor_id = 1
                            
                        elif pet_sex == 1 or pet_sex == 3:
                            # Non-pediatric, sexually immature or intact male dogs
                            print("DER Modifier * 1.6-1.8")
                            der_factor_id = 2
                            
                                 
                    print(breed_size)
                    

                    print(session["user_id"])
                    print(session["pet_name"])
                    print(breed_id, der_factor_id, pet_age_years, pet_age_months, pet_breed, pet_sex)
                    
                    try:
                        db.execute(
                            "UPDATE pets SET canine_breed_id = :breed_id, canine_der_factor_id = :der_factor_id, \
                                age_in_years = :y, age_in_months = :m, breed = :breed, sex = :sex, is_pediatric = :pediatric_status \
                                    WHERE pet_id = :pet_id AND owner_id = :user_id",
                                breed_id=breed_id, der_factor_id=der_factor_id, y=pet_age_years, m=pet_age_months, breed=pet_breed, \
                                sex=pet_sex, pediatric_status=is_pediatric, pet_id=pet_id, user_id=session["user_id"]
                            )

                            
                    except Exception as e:
                        flash(f"Unable to update data. Exception: {e}")
                        return redirect(url_for("pet_info_continued", form=form, pet_id=pet_id))

                            
                if species == "Feline":
                    breed_id_result = db.execute(
                        "SELECT BreedID FROM cat_breeds WHERE Breed = ?", pet_breed
                    )    
                    
                    breed_id = breed_id_result[0]["BreedID"]
                    print(breed_id)
                    

                    # DER factors suggested by https://todaysveterinarynurse.com/wp-content/uploads/sites/3/2018/07/TVN-2018-03_Puppy_Kitten_Nutrition.pdf
                    # and https://www.veterinary-practice.com/article/feeding-for-optimal-growth
                    if pet_age <= 0.33 or pet_age > 0.5 and pet_age <= 0.83:
                        # Kittens under 4 months old or between 7 and 10 months old have a DER modifier of * 2.0
                        print("DER Modifier * 2.0")
                        der_factor_id = 13
                        is_pediatric = "y"
                    elif pet_age > 0.33 and pet_age <= 0.5:
                        #Kittens between 5 and 6 months old have a DER modifier of * 2.5
                        print("DER Modifier * 2.5")
                        der_factor_id = 14
                        is_pediatric = "y"
                    elif pet_age > 0.83 and pet_age <= 1:
                        # Kittens between 10 and 12 months old have a DER modifier of * 1.8-2.0
                        print("DER Modifier * 1.8-2.0")
                        der_factor_id = 15
                        is_pediatric = "y"
                    elif pet_age > 1 and pet_age < 2:
                        # Kittens that aren't pediatric but aren't sexually matue
                        not_pediatric_not_mature = True
                    elif pet_age >= 2 and pet_age < 7:
                        # Pets over 2 years old
                        sexually_mature = True
                    elif pet_age >= 7 and pet_age <= 11:
                        # Cats between 7 and 11 years of age have a DER modifier of * 1.1-1.4
                        print("DER Modifier * 1.1-1.4")
                        der_factor_id = 4
                    elif pet_age >= 11:
                        # Cats older than 11 years have a DER modifier of * 1.1-1.6
                        print("DER Modifier * 1.1-1.6")
                        der_factor_id = 5
                        
                    if not_pediatric_not_mature or sexually_mature:
                        if pet_sex == 2 or pet_sex == 4:
                            # Non-pediatric, sexually immature and older cats that are neutered or spayed
                            print("DER Modifier * 1.2-1.4")
                            der_factor_id = 1
                            
                        elif pet_sex == 1 or pet_sex == 3:
                            # Non-pediatric, sexually immature or intact male cats
                            print("DER Modifier * 1.4-1.6")
                            der_factor_id = 2


                    print (der_factor_id)
                        
                    try:
                        db.execute(
                            "UPDATE pets SET feline_breed_id = :breed_id, feline_der_factor_id = :der_factor_id, \
                                age_in_years = :y, age_in_months = :m, breed = :breed, sex = :sex, is_pediatric = :pediatric_status \
                                    WHERE pet_id = :pet_id AND owner_id = :user_id",
                                breed_id=breed_id, der_factor_id=der_factor_id, y=pet_age_years, m=pet_age_months, breed=pet_breed, \
                                    sex=pet_sex, pediatric_status=is_pediatric, pet_id=pet_id, user_id=session["user_id"]
                            )
                            
                    except Exception as e:
                        flash(f"Unable to update part 2 of signalment data, Exception: {e}")
                        return redirect(url_for("pet_info_continued", form=form, pet_id=pet_id))
                        
                # Store new info as session variables
                session["der_factor_id"] = der_factor_id
                session["breed_id"] = breed_id
                session["is_pediatric"] = is_pediatric
                    
                
                if pet_age >= 2 and pet_sex == 1:
                    # If the pet is a mature intact female, redirect to pregnancy questions
                    return redirect(url_for('repro_status', pet_id=pet_id))
                else:
                    # redirect to pet body condition score questions
                    return redirect(url_for('pet_condition', pet_id=pet_id))
        return render_template("get_signalment_part_2.html", form=form, pet_breed=pet_breed, species=species, pet_id=pet_id)


@app.route("/pregnancy_status/<int:pet_id>", methods=["GET", "POST"])
@login_required
def repro_status(pet_id):
    """Gets information about the pet's pregnancy status"""
    repro = ReproStatus()
    
    try:
        print(f"pet ID: {pet_id}")
        fi = FindInfo(session["user_id"], pet_id) 
        
        
        # Use login check from find_info to verify species
        species = fi.login_check_for_species()
    except Exception as e:
        flash(f"Couldn't find ID, Exception: {e}")
        return redirect(url_for('repro_status', pet_id=pet_id)) 
     
    if request.method == "POST":
        pregnancy_status = repro.pregnancy_status.data
        
        # Store new info as session variables
        session["pregnancy_status"] = pregnancy_status
        
        print(pregnancy_status)
        
        try:
            db.execute(
                "UPDATE pets SET is_pregnant = :is_pregnant WHERE pet_id = :pet_id AND owner_id = :user_id",
                is_pregnant=pregnancy_status, pet_id=pet_id, user_id=session["user_id"]
            )
        except Exception as e:
            flash(f"Unable to insert pregnancy data, Exception: {e}")
            return redirect(url_for("repro_status", pet_id=pet_id))
            
            
        if pregnancy_status == "y":
            
            if species == "Canine":
                # If pet is pregnant and canine, ask how many weeks along she is
                return redirect(url_for('gestation_duration', pet_id=pet_id))
            else: 
                # If pet is pregnant and feline, DER factor is * 1.6-2.0
                der_factor_id = 7
                
                print (der_factor_id)
                    
                try:
                    db.execute(
                        "UPDATE pets SET feline_der_factor_id = :der_factor_id WHERE pet_id = :pet_id AND owner_id = :user_id",
                            der_factor_id=der_factor_id, pet_id=pet_id, user_id=session["user_id"]
                        )
                        
                except Exception as e:
                    flash(f"Unable to update feline DER factor id for gestation data, Exception: {e}")
                        
                    return redirect(url_for("repro_status", repro=repro, pet_id=pet_id))

            # Update session variable
            session["der_factor_id"] = der_factor_id
            return redirect(url_for('pet_condition', species=species, pet_id=pet_id))
        else:
            # If pet is not pregnant, ask if she is currently nursing a litter
            return redirect(url_for('lactation_status', pet_id=pet_id))
    
    return render_template("get_reproductive_status.html", repro=repro, pet_id=pet_id)


@app.route("/gestation_duration/<int:pet_id>", methods=["GET", "POST"])
@login_required
def gestation_duration(pet_id):
    """Asks for how long the pet has been pregnant for if they are canine 
    and assigns DER factor"""
    
    repro = ReproStatus()
    
    # Use login check from find_info to verify species
    fi = FindInfo(session["user_id"], pet_id) 
    species = fi.login_check_for_species()
    
    if request.method == "POST":
        number_weeks_pregnant = repro.weeks_gestation.data
        

        # Use check from find_info to verify DER factor id     
        der_factor_id = fi.der_factor()
        # print(der_factor_id)    
        
        if number_weeks_pregnant <= "6":
            # If pet is pregnant, canine, and within the first 42 days of pregnancy, DER modifier is *~1.8
            
            if der_factor_id != 5:
                der_factor_id = 5
            
        else:
            # If pet is pregnant, canine, and within the last 21 days of pregnancy, DER modifier is *3
            
            if der_factor_id != 6:
                der_factor_id = 6
            
        print(der_factor_id)


        try:
            db.execute(
                "UPDATE pets SET weeks_gestating = :weeks_gestating, canine_der_factor_id = :der_factor_id WHERE pet_id = :pet_id AND owner_id = :user_id",
                weeks_gestating=number_weeks_pregnant, der_factor_id=der_factor_id, pet_id=pet_id, user_id=session["user_id"]
            )
        except Exception as e:
            flash(f"Unable to update data for gestation length, Exception: {e}")
            return redirect(url_for("gestation_duration", pet_id=pet_id))
        
        # Store new info as session variables
        session["number_weeks_pregnant"] = number_weeks_pregnant
        
        # Update DER factor ID variable
        session["der_factor_id"] = der_factor_id
        
        return redirect(url_for('pet_condition', pet_id=pet_id))
    
    return render_template("gestation_duration.html", repro=repro, pet_id=pet_id)


@app.route("/litter_size/<int:pet_id>", methods=["GET", "POST"])
@login_required
def litter_size(pet_id):
    """Asks for the litter size of pets that have one, then assigns DER modifier"""
    
    repro = ReproStatus()
    
    # Use login check from find_info to verify species
    fi = FindInfo(session["user_id"], pet_id) 
    species = fi.login_check_for_species()
    
    if request.method == "POST":
        litter_size = repro.litter_size.data
        
        # Stores litter size data in the session
        session["litter_size"] = litter_size
        
        try:
            db.execute(
                "UPDATE pets SET litter_size = :size WHERE pet_id = :pet_id AND owner_id = :user_id",
                size=litter_size, pet_id=pet_id, user_id=session["user_id"]
            )
        except Exception as e:
            flash(f"Unable to update litter size, Exception: {e}")
            return redirect(url_for("litter_size", pet_id=pet_id))
        
        # Use find_info to check DER factor ID  
        der_factor_id = fi.der_factor()

          
        if species == "Feline":
            # If the pet is a nursing feline, ask for weeks of lactation
            return redirect(url_for('lactation_duration', pet_id=pet_id))
        elif species == "Canine":
            # If pet is a nursing canine, DER modifier changes based on litter size
            if litter_size == 1:
                # 1 puppy: * 3.0
                der_factor_id = 7
            elif litter_size == 2:
                # 2 puppies: 3.5
                der_factor_id = 8
            elif litter_size == 3 or litter_size == 4:
                # 3-4 puppies: 4.0
                der_factor_id = 9
            elif litter_size == 5 or litter_size == 6:
                # 5-6 puppies: 5.0
                der_factor_id = 10
            elif litter_size == 7 or litter_size == 8:
                # 7-8 puppies: 5.5
                der_factor_id = 11
            elif litter_size >= 9:
                # 9+ puppies >= 6.0
                der_factor_id = 12
                
            try:
                db.execute(
                    "UPDATE pets SET canine_der_factor_id = :der_factor_id WHERE pet_id = :pet_id AND owner_id = :user_id",
                    der_factor_id=der_factor_id, pet_id=pet_id, user_id=session["user_id"]
                )
            except Exception as e:
                flash(f"Unable to update canine DER factor ID for litter size, Exception: {e}")
                return redirect(url_for("litter_size", pet_id=pet_id))
            
        # Update DER factor ID variable
        session["der_factor_id"] = der_factor_id  
            
        return redirect(url_for('pet_condition', pet_id=pet_id))
    
    return render_template("get_litter_size.html", repro=repro, pet_id=pet_id)


@app.route("/lactation_status/<int:pet_id>", methods=["GET", "POST"])
@login_required
def lactation_status(pet_id):
    """Asks if the pet is currently nursing"""
    
    repro = ReproStatus()
    
    # Use login check from find_info to verify species
    fi = FindInfo(session["user_id"], pet_id) 
    species = fi.login_check_for_species()
    
    if request.method == "POST":
        lactation_status = repro.nursing_status.data
        
        # Stores lactation status variable in session
        session["lactation_status"] = lactation_status
        
        print(lactation_status)
        
        # Add pet to the database if the user is logged in
        try:
            db.execute(
                "UPDATE pets SET is_nursing = :lactation_status WHERE pet_id = :pet_id AND owner_id = :user_id",
                lactation_status=lactation_status, pet_id=pet_id, user_id=session["user_id"]
            )
        except Exception as e:
            flash(f"Unable to update lactation status data, Exception: {e}")
            return redirect(url_for("lactation_status", pet_id=pet_id))
                
          

        if lactation_status == "y":
            # If pet is lactating, ask for litter size
            return redirect(url_for('litter_size', pet_id=pet_id))
            
        else:
            # If pet is not lactating, next page is get_weight
            return redirect(url_for('pet_condition', pet_id=pet_id))
    
    return render_template("get_lactation_status.html", repro=repro, pet_id=pet_id)
    

@app.route("/lactation_duration/<int:pet_id>", methods=["GET", "POST"])
@login_required
def lactation_duration(pet_id):
    """Asks how many weeks a pregnant queen has been nursing and adds DER modifier"""
    
    repro = ReproStatus()
    
    # Use login check from find_info to verify species
    fi = FindInfo(session["user_id"], pet_id) 
    species = fi.login_check_for_species()
    
    if request.method == "POST":
        duration_of_nursing = int(repro.weeks_nursing.data)
         
        if duration_of_nursing <= 2:
            # If the queen has been nursing for 2 weeks or less, DER modifier is RER + 30% per kitten
            der_factor_id = 8
        
        elif duration_of_nursing == 3:
            # If the queen has been nursing for 3 weeks, DER modifier is RER + 45% per kitten
            der_factor_id = 9 
        
        elif duration_of_nursing == 4:
            # If the queen has been nursing for 4 weeks, DER modifier is RER + 55% per kitten
            der_factor_id = 10 
        
        elif duration_of_nursing == 5:
            # If the queen has been nursing for 5 weeks, DER modifier is RER + 65% per kitten
            der_factor_id = 11 
        
        elif duration_of_nursing == 6:
            # If the queen has been nursing for 6 weeks, DER modifier is RER + 90% per kitten
            der_factor_id = 12 
            
        try:
            db.execute(
                "UPDATE pets SET weeks_nursing = :duration_of_nursing, feline_der_factor_id = :der_factor_id WHERE pet_id = :pet_id AND owner_id = :user_id",
                    duration_of_nursing=duration_of_nursing, der_factor_id=der_factor_id, pet_id=pet_id, user_id=session["user_id"]
                )
        except Exception as e:
            flash(f"Unable to update nursing timeframe data, Exception: {e}")
            return redirect(url_for('lactation_duration', pet_id=pet_id))
        
        # Stores nursing duration variable in session
        session["duration_of_nursing"] = duration_of_nursing
        
        # Update session variable
        session["der_factor_id"] = der_factor_id
        
        return redirect(url_for('pet_condition', pet_id=pet_id))
    
    return render_template("lactation_duration.html", repro=repro, pet_id=pet_id)


@app.route("/get-weight/<int:pet_id>", methods=["GET", "POST"])
@login_required
def pet_condition(pet_id):
    """Gets the pet's weight and body condition score"""
    
    form = GetWeight() 

    fi = FindInfo(session["user_id"], pet_id) 
    species = fi.login_check_for_species()
    
        
    print(f"user_id: {session['user_id']}, pet_id: {id}")     
    # Use login check from find_info to verify species
    species = fi.login_check_for_species()
    
    if request.method == "POST":
        bcs = int(form.pet_bcs.data)
        weight = float(form.pet_weight.data)
        units = form.pet_units.data
        
        if units == "lbs":
            # Convert weight to kilograms 
            converted_weight = round((weight / 2.2), 2)
            converted_weight_units = "kgs"
        elif units == "kgs":
            # Convert weight to lbs
            converted_weight = round((weight * 2.2), 2)
            converted_weight_units = "lbs"

        
        # print(bcs)
        # print(type(bcs))
        # print(weight)
        # print(type(weight))
        # print(units)
        # print(type(units))
        
        # Use find_info to verify DER factor ID
        der_factor_id = fi.der_factor()
        # check_litter_size()
        
            
        print(f"Weight: {weight}{units}")
        
            
        if bcs != 5:
            # Calculate ideal weight
            weight_proportion = round((100 / (((bcs - 5) * 10) + 100)), 3)
            # print(f"weight_proportion: {weight_proportion}")
            

            if units == "lbs":
                est_ideal_weight_lbs = round((weight_proportion * weight), 2)
                print(est_ideal_weight_lbs)
                
                # Calculate ideal weight in kgs
                est_ideal_weight_kgs = round((est_ideal_weight_lbs / 2.2), 2)
                print(est_ideal_weight_kgs)
                
            elif units == "kgs":
                est_ideal_weight_kgs = round((weight_proportion * weight), 2)
                print(est_ideal_weight_kgs)
                
                # Calculate ideal weight in lbs
                est_ideal_weight_lbs = round((est_ideal_weight_kgs * 2.2), 2)
                print(est_ideal_weight_lbs)

        else:
            # If pet has 5/9 on the BCS scale, set estimated ideal weight as current weight
            if units == "lbs":
                est_ideal_weight_lbs = weight
                est_ideal_weight_kgs = round((est_ideal_weight_lbs / 2.2), 2)
            elif units == "kgs":
                est_ideal_weight_kgs = weight
                est_ideal_weight_lbs = round((est_ideal_weight_kgs * 2.2), 2)
        
        # Store new info as session variables
        session["bcs"] = bcs
        session["weight"] = weight
        session["units"] = units
        session["converted_weight"] = converted_weight
        session["converted_weight_units"] = converted_weight_units
        session["ideal_weight_kgs"] = est_ideal_weight_kgs
        session["ideal_weight_lbs"] = est_ideal_weight_lbs
        
        bcs_to_body_fat = {1: "< 5", 2: "5", 3: "10", 4: "15", 5: "20",
                        6: "25", 7: "30", 8: "35", 9: ">=40"
                        }
        
        # Find body fat percentage
        percent_body_fat = bcs_to_body_fat[bcs]
        print(percent_body_fat)
        print(f"Estimated ideal weight: {est_ideal_weight_kgs} kgs, {est_ideal_weight_lbs} lbs")

        # Check for pregnancy status and nursing status
        pregnancy_status = fi.check_if_pregnant()
        is_nursing = fi.check_if_nursing()
        is_pediatric = fi.check_if_pediatric()
        
        if species == "Canine":
            
            if pregnancy_status != "y" and is_nursing != "y" and is_pediatric != "y":
                # Only update DER factor id if pet isn't nursing or pregnant
                if bcs <= 4:
                    # Change DER factor id to weight gain 
                    der_factor_id = 24
                elif bcs == 6:
                    # Change DER factor to weight loss
                    der_factor_id = 4 
                elif bcs > 6:
                    # Change DER factor to obese prone
                    der_factor_id = 3
                
        
            # Check if pet breed is predisposed to obesity
            obese_prone_breed = fi.check_obesity_risk()
                
            print(obese_prone_breed)
            if obese_prone_breed == "y" and pregnancy_status != "y" and is_nursing != "y" and is_pediatric != "y":
                der_factor_id = 3
                
            try:
                print(session["pet_name"])
                print(session["user_id"])

                db.execute(
                    "UPDATE pets SET canine_der_factor_id = :der_factor_id, bcs = :body_condition_score, \
                        ideal_weight_lbs = :ideal_weight_lbs, ideal_weight_kgs = :ideal_weight_kgs, weight = :weight, \
                            units = :units, converted_weight = :converted_weight, converted_weight_units = :converted_weight_units, \
                                body_fat_percentage = :percent_body_fat WHERE pet_id = :pet_id AND owner_id = :user_id",
                    der_factor_id=der_factor_id, body_condition_score=bcs, ideal_weight_lbs=est_ideal_weight_lbs, 
                    ideal_weight_kgs=est_ideal_weight_kgs, weight=weight, units=units, converted_weight=converted_weight, 
                    converted_weight_units=converted_weight_units, percent_body_fat=percent_body_fat, pet_id=pet_id, 
                    user_id=session["user_id"]
                )
                        
            except Exception as e:
                flash(f"Unable to update canine BCS data, Exception: {e}")
                return render_template("get_weight_and_bcs.html", form=form)
                    
                
            # Update DER factor ID variable
            session["der_factor_id"] = der_factor_id  
            
            # Gets a dog's activity level if applicable 
            return redirect(url_for('activity', pet_id=pet_id))  
        
        elif species == "Feline":
            
            if pregnancy_status != "y" and is_nursing != "y" and is_pediatric != "y":
                if bcs <= 4:
                    # Change DER factor id to weight gain 
                    der_factor_id = 16
                elif bcs == 6:
                    # Change DER factor to weight loss
                    der_factor_id = 6 
                elif bcs > 6:
                    # Change DER factor id to obese prone 
                    der_factor_id = 3
                
            # Check if pet breed is predisposed to obesity
            obese_prone_breed = fi.check_obesity_risk()
                
            print(obese_prone_breed)
            if obese_prone_breed == "y" and pregnancy_status != "y" and is_nursing != "y" and is_pediatric != "y":
                der_factor_id = 3
            
            try:
                print(session["pet_name"])
                print(session["user_id"])

                db.execute(
                    "UPDATE pets SET feline_der_factor_id = :der_factor_id, bcs = :body_condition_score, \
                        ideal_weight_kgs = :ideal_weight_kgs, ideal_weight_lbs = :est_ideal_weight_lbs, \
                            weight = :weight, units = :units, converted_weight = :converted_weight, \
                                converted_weight_units = :converted_weight_units, body_fat_percentage = :percent_body_fat \
                                    WHERE pet_id = :pet_id AND owner_id = :user_id",
                        der_factor_id=der_factor_id, body_condition_score=bcs, ideal_weight_kgs=est_ideal_weight_kgs, 
                        est_ideal_weight_lbs=est_ideal_weight_lbs, weight=weight, units=units, converted_weight=converted_weight, 
                        converted_weight_units=converted_weight_units, percent_body_fat=percent_body_fat, 
                        pet_id=pet_id, user_id=session["user_id"]
                )
                        
            except Exception as e:
                flash(f"Unable to update feline BCS data, Exception: {e}")
                return render_template("get_weight_and_bcs.html", form=form, species=species)


            # Update DER factor ID variable
            session["der_factor_id"] = der_factor_id  
                
            # Take cat owners to the pre-confirmation page
            return redirect(url_for('confirm_data', pet_id=pet_id))
    
    return render_template("get_weight_and_bcs.html", form=form, species=species, pet_id=pet_id)


@app.route("/activity/<int:pet_id>", methods=["GET", "POST"])
@login_required
def activity(pet_id):
    """Gets a pet's activity status/amount"""
    
    work = WorkForm()
    
    # Use login check from find_info to verify species
    fi = FindInfo(session["user_id"], pet_id) 
    species = fi.login_check_for_species()
    
    if request.method == "POST":
        light_work_minutes = work.light_work_minutes.data
        light_work_hours = work.light_work_hours.data
        heavy_work_minutes = work.heavy_work_minutes.data
        heavy_work_hours = work.heavy_work_hours.data
        
        print(f'heavy_work_hours: {heavy_work_hours}, light_work_hours: {light_work_hours}')

        # Convert time for easier logic tracking
        light_work_hours += (light_work_minutes / 60)
        heavy_work_hours += (heavy_work_minutes / 60)
        
        print(f'heavy_work_hours: {heavy_work_hours}, light_work_hours: {light_work_hours}')
            
        # Use find_info to verify DER factor ID, pregnancy status, and lactation status
        der_factor_id = fi.der_factor()
        pregnancy_status = fi.check_if_pregnant()
        is_nursing = fi.check_if_nursing()
        
        # Check if pet breed is predisposed to obesity
        obese_prone_breed = fi.check_obesity_risk()
        
        
        # Pets that aren't pregnant, aren't nursing, and are obese prone, condition suggested by CoPilot
        not_preg_or_nursing_non_obese = pregnancy_status != "y" and is_nursing != "y" and obese_prone_breed != "y"
        not_preg_or_nursing = pregnancy_status != "y" and is_nursing != "y"
        
        # Check if a pet is pediatric
        is_pediatric = fi.check_if_pediatric()
                
        # sources: https://wellbeloved.com/pages/cat-dog-activity-levels
        # https://perfectlyrawsome.com/raw-feeding-knowledgebase/activity-level-canine-calorie-calculations/
        if light_work_hours < 0.5 and heavy_work_hours <= 1:
            # Sedentary: 0-30 minutes of light activity daily
            activity_level = 1
            
            if not_preg_or_nursing_non_obese and is_pediatric == "n":
                der_factor_id = 3
        elif light_work_hours >= 0.5 and light_work_hours <= 1 and heavy_work_hours == 0 or \
            light_work_hours >= 0.5 and light_work_hours <= 1 and heavy_work_hours < 1:
            # Low activity: 30 minutes to 1 hour (i.e. walking on lead)
            activity_level = 2
            
            if not_preg_or_nursing_non_obese and is_pediatric == "n":
                der_factor_id = 21
        elif light_work_hours >= 1 and light_work_hours <= 2 and heavy_work_hours == 0 or \
            heavy_work_hours > 0 and heavy_work_hours < 3:
            # Moderate activity: 1-2 hours of low impact activity
            activity_level = 3
            
            if not_preg_or_nursing and is_pediatric == "n":
                # Modify DER factor ID even for obese prone breeds if the dog gets adequate activity
                der_factor_id = 22
                
        elif heavy_work_hours >= 1 and heavy_work_hours < 3 and light_work_hours == 0:
            # Moderate activity: 1-3 hours of high impact activity (i.e. running off-lead, playing ball, playing off-lead with other dogs)
            activity_level = 3
            
            if not_preg_or_nursing and is_pediatric == "n":
                # Modify DER factor ID even for obese prone breeds if the dog gets adequate activity
                der_factor_id = 22
        elif heavy_work_hours >= 3 and light_work_hours >= 1:
            # Working and performance: 3+ hours (i.e. working dog)
            activity_level = 4
            
            if not_preg_or_nursing and is_pediatric == "n":
                # Modify DER factor ID even for obese prone breeds if the dog gets adequate activity
                der_factor_id = 23
                    
        print(activity_level)
        
        try:
            print(session["pet_name"])
            print(session["user_id"])
            print(activity_level)
            db.execute(
                "UPDATE pets SET canine_der_factor_id = :der_factor_id, activity_level = :activity WHERE pet_id = :pet_id AND owner_id = :user_id",
                der_factor_id=der_factor_id, activity=activity_level, pet_id=pet_id, user_id=session["user_id"]
            )
                
        except Exception as e:
            flash(f"Unable to update activity data, Exception: {e}")
            return redirect(url_for("activity", pet_id=pet_id))
        
        else:    
            # Otherwise, create new session variables
            session["activity_level"] = activity_level
        
        # Update DER factor ID variable
        session["der_factor_id"] = der_factor_id  
        
        return redirect(url_for('confirm_data', pet_id=pet_id))
    
    return render_template("get_work_level.html", work=work, pet_id=pet_id)


@app.route("/confirm_data/<int:pet_id>", methods=["GET", "POST"])
@login_required
def confirm_data(pet_id):
    """Confirms pet's info before taking users to the food calculator"""
    
    # Find data from from find info.py
    fi = FindInfo(session["user_id"], pet_id) 
    pet_data = fi.pet_data_dictionary(session["user_id"], pet_id)
    print(pet_data)
    user_id = session["user_id"]
        
    return render_template("confirm_pet_info.html", pet_data=pet_data, user_id=user_id, pet_id=pet_id)
    
    
@app.route("/current_food", methods=["GET", "POST"])
@login_required
def current_food():
    """Asks the user for information on their current food"""
    
    current_food = FoodForm()
    pet_id = request.args.get('pet_id', type=int)

    print(pet_id)
    if request.method == "POST":
        current_food_kcal = current_food.current_food_kcal.data
        current_food_form = current_food.current_food_form.data
        meals_per_day = current_food.meals_per_day.data
        
        # Ensure user enters at least one meal
        if meals_per_day < 1:
            flash("Please enter a number equal to or greater than 1.")
            return redirect(url_for("current_food", pet_id=pet_id))
        
        print(current_food_kcal)
        print(meals_per_day)
        print(current_food_form)

        if current_food_form == "default":
            flash("Please choose from the current food form dropdown.")
            return redirect(url_for("current_food", pet_id=pet_id))
        else:
            current_food_form = int(current_food_form)
            
            try:
                print(session["pet_name"])
                print(session["user_id"])
                    
                db.execute(
                    "UPDATE pets SET meals_per_day = :meals, current_food_kcal = :current_kcal, current_food_form = :current_food_form WHERE pet_id = :pet_id AND owner_id = :user_id",
                    meals=meals_per_day, current_kcal=current_food_kcal, current_food_form=current_food_form, pet_id=pet_id, user_id=session["user_id"]
                )
                    
            except Exception as e:
                flash(f"Unable to update data, Exception: {e}")
                return redirect(url_for("current_food", pet_id=pet_id))
                        
            
            # Otherwise, create new session variables
            session["meals_per_day"] = meals_per_day
            session["current_food_kcal"] = current_food_kcal
            session["current_food_form"] = int(current_food_form)
                

            # If user doesn't want a transition, calculate RER
            return redirect(url_for('rer', pet_id=pet_id))
        
    return render_template("current_food.html", current_food=current_food, pet_id=pet_id)
    
    

@app.route("/rer/<int:pet_id>", methods=["GET", "POST"])
@login_required
def rer(pet_id):
    """Calculates the minimum number of calories a pet needs at rest per day"""

    # Use find_info to find DER start and end range
    fi = FindInfo(session["user_id"])
    
    # Use login check from helpers.py to verify reproductive status
    sex = fi.find_repro_status()
    
    # Import food calculator
    cf = CalculateFood(session["user_id"], pet_id)
    rer = cf.calculate_rer()
    
    pet_data = fi.pet_data_dictionary(session["user_id"], pet_id)

    # Use DER factor id to lookup DER information by species
    if pet_data[0]["species"] == "Canine":
        der_low_end = float(fi.find_der_low_end(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"]))
        der_high_end = float(fi.find_der_high_end(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"]))
    elif pet_data[0]["species"] == "Feline":
        der_low_end = float(fi.find_der_low_end(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"]))
        der_high_end = float(fi.find_der_high_end(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"]))
        
    
    object_pronoun = fi.find_pronouns(pet_data[0]["sex"])["object_pronoun"]
    possessive_pronoun = fi.find_pronouns(pet_data[0]["sex"])["possessive_pronoun"]
    print(rer)

    print(f"Object pronoun {object_pronoun}", f"Possessive Pronoun: {possessive_pronoun}")

    # Store as a session variable
    session["object_pronoun"] = object_pronoun
    session["possessive_pronoun"] = possessive_pronoun
    
    # Find pet's current weight so the user can know what formula was used to find their pet's RER
    pet_data = fi.pet_data_dictionary(session["user_id"], pet_id)
    
    print(pet_data)
    # Check life stage factors
    obese_prone = fi.check_obesity_risk()
    is_pediatric = fi.check_if_pediatric()
    is_nursing = fi.check_if_nursing()
    is_pregnant = fi.check_if_pregnant()
    
    if obese_prone == "y" or is_pediatric == "y" \
        or is_nursing == "y" or is_pregnant == "y":
        # If pet is an obese prone breed, set max treat kcal/day at 8% of RER
        treat_kcals = int(rer * 0.08)
    else:
        # Calculate treat kcals per day (10% of RER)
        treat_kcals = int(rer * 0.1)
        
    print(f"Treat kcal:{treat_kcals}")
    
    session["rec_treat_kcal_per_day"] = treat_kcals
    
    try:
                    
        print(session["pet_name"])
        print(session["user_id"])
                
                            
        db.execute(
            "UPDATE pets SET rer = :rer, rec_treat_kcal_per_day = :treat_kcals WHERE pet_id = :pet_id AND owner_id = :user_id",
            rer=rer, pet_id=pet_id, user_id=session["user_id"], treat_kcals=treat_kcals
        )
        print("data updated")
    except Exception as e:
        flash(f"Unable to update data, Exception: {e}")
        return redirect(url_for("rer", pet_id=pet_id))
    
    if pet_data[0]["species"] == "Canine":
    
        der_low_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"])["DER_low_end"]))
        der_high_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"])["DER_high_end"]))
    
    elif pet_data[0]["species"] == "Feline":
        der_low_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"])["DER_low_end"]))
        der_high_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"])["DER_high_end"]))
        
    print (f"Low end: {der_low_end} type: {type(der_low_end)} High end: {der_high_end} type: {type(der_high_end)} ")
    if request.method == "POST":    
        return redirect(url_for('der'))
    
    return render_template("rer.html",
                           rer=rer,
                           name=session["pet_name"],
                           object_pronoun=object_pronoun,
                           possessive_pronoun=possessive_pronoun,
                           weight=pet_data[0]["weight"],
                           converted_weight=pet_data[0]["converted_weight"],
                           units=pet_data[0]["units"],
                           sex=sex,
                           der_low_end=der_low_end,
                           der_high_end=der_high_end,
                           converted_weight_units=pet_data[0]["converted_weight_units"],
                           pet_id=pet_id)
    
    
@app.route("/der/<int:pet_id>", methods=["GET", "POST"])
@login_required
def der(pet_id):
    """Calculates the daily energy rate and total food amount of the current diet to feed"""
    
    # Import food calculator
    cf = CalculateFood(session["user_id"], pet_id)
    
    # Call session variable for pronouns
    object_pronoun = session["object_pronoun"]
    possessive_pronoun = session["possessive_pronoun"]

    print(possessive_pronoun, object_pronoun)
    
    
    # Use find_info to verify species, sex, and litter size if applicable
    fi = FindInfo(session["user_id"], pet_id) 
    species = fi.login_check_for_species()
    sex = fi.find_repro_status()
    litter_size = fi.check_litter_size()
    
    try:
        pet_data = fi.pet_data_dictionary(session["user_id"], pet_id)
            
        if pet_data:  
            name = pet_data[0]["name"]
            rer = pet_data[0]["rer"]
            meals_per_day = pet_data[0]["meals_per_day"]
            current_food_kcal = pet_data[0]["current_food_kcal"]
            is_nursing = pet_data[0]["is_nursing"]
            litter_size = pet_data[0]["litter_size"]
            weeks_nursing = pet_data[0]["weeks_nursing"]
                
            print(weeks_nursing)
                
        print(name, rer, meals_per_day, current_food_kcal, is_nursing, litter_size)

                
    except Exception as e:
        flash(f"Unable to find pet data for DER calculation, Exception: {e}")    
        return render_template("der.html",
                        rer=rer,
                        name=name,
                        sex=sex,
                        object_pronoun=object_pronoun,
                        possessive_pronoun=possessive_pronoun)
      
    # Use find_info to verify DER factor ID and food form
    current_food_form = fi.find_food_form()
    der_factor_id = fi.der_factor()
    
    print(der_factor_id)
    print(rer, der_factor_id, meals_per_day, current_food_kcal, current_food_form)
    
    if pet_data[0]["species"] == "Canine":
        der = cf.calculcate_der(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"])["DER"]
        der_low_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"])["DER_low_end"]))
        der_high_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"])["DER_high_end"]))
        der_modifier = cf.calculcate_der(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"])["DER_modifier"]
    elif pet_data[0]["species"] == "Feline":
        der = cf.calculcate_der(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"])["DER"]
        der_low_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"])["DER_low_end"]))
        der_high_end = int(float(cf.calculcate_der(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"])["DER_high_end"]))
        der_modifier = cf.calculcate_der(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"])["DER_modifier"]

    
    # Convert all to int for easier reading
    der, der_low_end, der_high_end = int(float(der)), int(float(der_low_end)), int(float(der_high_end))

    print(f"Low End: {der_low_end} High {der_high_end}")
    # Calculate the required calories per day
    total_calorie_amount_per_day = round(der / current_food_kcal, 2)
    
    # Breaks the food amount in to whole and partial amounts to convert to volumetric easier    
    daily_whole_cans_or_cups, daily_partial_amount = str(total_calorie_amount_per_day).split(".")[0], str(total_calorie_amount_per_day).split(".")[1]
    print(total_calorie_amount_per_day)
        
    print(f"per day whole: {daily_whole_cans_or_cups}, partial: {daily_partial_amount}")
    
    print(daily_whole_cans_or_cups)
    print(type(daily_whole_cans_or_cups))
        
    daily_partial_volumetric = cf.convert_decimal_to_volumetric(daily_partial_amount)

    if daily_partial_volumetric == "1":
        # If partial volume is more than 0.86 cups, convert whole cup/can volume amount to integer

        daily_whole_cans_or_cups = int(daily_whole_cans_or_cups)
            
        # Then add to whole volume
        daily_whole_cans_or_cups += 1
        daily_partial_volumetric = "0"
        
    food_form = ""
    if current_food_form == 1:
        food_form = "cup"
    elif current_food_form == 2:
        food_form = "can"
    elif current_food_form == 3:
        food_form = "pouch"
    
    # Shortened conditional variables suggested by CoPilot
    whole_cans_or_cups = int(daily_whole_cans_or_cups)
    is_pouch = current_food_form == 3
    is_half_tablespoon = daily_partial_volumetric == "1/2 tablespoon"
    food_form_plural = f"{food_form}{'es' if is_pouch else 's'}"

    
    if whole_cans_or_cups == 1:
        if is_half_tablespoon and daily_partial_volumetric != "0":
            daily_amount_to_feed = f"{whole_cans_or_cups} {food_form} and {daily_partial_volumetric} per day"
        elif not is_half_tablespoon and daily_partial_volumetric != "0":
            daily_amount_to_feed = f"{whole_cans_or_cups} and {daily_partial_volumetric} {food_form} per day"
        else:
            daily_amount_to_feed = f"{whole_cans_or_cups} {food_form} per day"
    elif whole_cans_or_cups >= 1:
        if is_half_tablespoon and daily_partial_volumetric != "0":
            daily_amount_to_feed = f"{whole_cans_or_cups} {food_form_plural} and {daily_partial_volumetric} per day"
        elif not is_half_tablespoon and daily_partial_volumetric != "0":
            daily_amount_to_feed = f"{whole_cans_or_cups} and {daily_partial_volumetric} {food_form_plural} per day"
        else:
            daily_amount_to_feed = f"{whole_cans_or_cups} {food_form_plural} per day"
    elif whole_cans_or_cups == 0 and daily_partial_volumetric != "0":
        if is_half_tablespoon:
            daily_amount_to_feed = f"{daily_partial_volumetric} per day"
        else:
            daily_amount_to_feed = f"{daily_partial_volumetric} {food_form_plural} per day"
    else:
        # Under 1 whole can or cup amount
        daily_amount_to_feed = f"{daily_partial_volumetric} per day"

    
    # Suggested by CoPilot      
    if daily_amount_to_feed.startswith("0 and "):
        daily_amount_to_feed = total_amount_per_meal.replace("0 and ", "")
    elif daily_amount_to_feed.endswith(" and 0"):
        daily_amount_to_feed = total_amount_per_meal.replace(" and 0", "")
        
    # Calculate the required calories per meal
    total_amount_per_meal = total_calorie_amount_per_day / meals_per_day
    
    print(total_amount_per_meal)
    if meals_per_day > 1:
        # Break down volume per meal if meals per day is more than 1

        # Breaks the food amount in to whole and partial amounts to convert to volumetric easier
        meal_whole_cans_or_cups, meal_partial_amount = str(total_amount_per_meal).split(".")[0], str(total_amount_per_meal).split(".")[1]
        # print(food_amount_per_day)
        
        print(f"whole cups per meal: {meal_whole_cans_or_cups}, partial cups per meal: {meal_partial_amount}")
        
        print(meal_whole_cans_or_cups)
        print(type(meal_whole_cans_or_cups))
        
        # Calculate total volumetric amounts per meal
        meal_partial_volumetric = cf.convert_decimal_to_volumetric(meal_partial_amount)

        print(f"meal_partial_volumetric: {meal_partial_volumetric}")
        if meal_partial_volumetric == "1":
            # If partial volume is more than 0.86 cups, convert whole cup/can volume amount to integer

            meal_whole_cans_or_cups = int(meal_whole_cans_or_cups)
            
            # Then add to whole volume and reset partial volume value
            meal_whole_cans_or_cups += 1
            meal_partial_volumetric = "0"
            
        # Amount recommended depends on volumetric conversion and food form
            
        if whole_cans_or_cups == 1:
            if is_half_tablespoon and meal_partial_volumetric != "0":
                total_amount_per_meal = f"{meal_whole_cans_or_cups} {food_form} and {meal_partial_volumetric}"
            elif not is_half_tablespoon and meal_partial_volumetric != "0":
                total_amount_per_meal = f"{meal_whole_cans_or_cups} and {meal_partial_volumetric} {food_form}"
            else:
                total_amount_per_meal = f"{meal_whole_cans_or_cups} {food_form}"
        elif whole_cans_or_cups >= 1:
            if is_half_tablespoon and meal_partial_volumetric != "0":
                total_amount_per_meal = f"{meal_whole_cans_or_cups} {food_form_plural} and {meal_partial_volumetric}"
            elif not is_half_tablespoon and meal_partial_volumetric != "0":
                total_amount_per_meal = f"{meal_whole_cans_or_cups} and {meal_partial_volumetric} {food_form_plural}"
            else:
                total_amount_per_meal = f"{meal_whole_cans_or_cups} {food_form_plural}"
        elif whole_cans_or_cups == 0 and meal_partial_volumetric != "0":
            if is_half_tablespoon:
                total_amount_per_meal = f"{meal_partial_volumetric}"
            else:
                total_amount_per_meal = f"{meal_partial_volumetric} {food_form_plural}"
        elif whole_cans_or_cups == 0 and meal_partial_volumetric == "0":
            total_amount_per_meal = "0"
        else:
            # Under 1 whole can or cup amount
            total_amount_per_meal = f"{daily_partial_volumetric}"
    else:
        # If the user asks for 1 meal per day amounts, total_amount_per_meal = daily amount
        per_meal = daily_amount_to_feed.split("day")[0]
        total_amount_per_meal = f"{per_meal}meal"
    
    # Suggested by CoPilot    
    if total_amount_per_meal.startswith("0 and "):
        total_amount_per_meal = total_amount_per_meal.replace("0 and ", "")
    elif total_amount_per_meal.endswith(" and 0"):
        total_amount_per_meal = total_amount_per_meal.replace(" and 0", "")
    
    print(total_amount_per_meal)
    
    print(daily_amount_to_feed)
    # Set session variables 
            
    session["der"] = der
    session["der_modifier"] = der_modifier
    session["daily_amount_to_feed_cur_food"] = daily_amount_to_feed
    session["current_food_amt_per_meal"] = total_amount_per_meal
        
    
    try:          
        print(session["pet_name"])
        print(session["user_id"])
                                   
        # If the pet has a completed report, don't update date_of_first_report
        if pet_data[0]["date_of_first_report"]:
            db.execute(
                "UPDATE pets SET der = :der, der_modifier = :der_modifier, current_food_amt_rec = :daily_amount_to_feed, \
                    most_recent_report_date = CURRENT_TIMESTAMP, current_food_amt_per_meal = :total_amount_per_meal \
                        WHERE pet_id = :pet_id AND owner_id = :user_id",
                der=der, der_modifier=der_modifier, daily_amount_to_feed=daily_amount_to_feed, total_amount_per_meal=total_amount_per_meal, \
                    pet_id=pet_id, user_id=session["user_id"]
            )
        else:
            db.execute(
                "UPDATE pets SET der = :der, der_modifier = :der_modifier, current_food_amt_rec = :daily_amount_to_feed, \
                    date_of_first_report = CURRENT_TIMESTAMP, most_recent_report_date = CURRENT_TIMESTAMP, \
                    current_food_amt_per_meal = :total_amount_per_meal WHERE pet_id = :pet_id AND owner_id = :user_id",
                der=der, der_modifier=der_modifier, daily_amount_to_feed=daily_amount_to_feed, total_amount_per_meal=total_amount_per_meal, \
                    pet_id=pet_id, user_id=session["user_id"]
            )
        

    except Exception as e:
        flash(f"Unable to update data, Exception: {e}")
        return redirect(url_for("der", pet_id=pet_id))

    
    return render_template("der.html",
                           pet_id=pet_id,
                           rer=rer,
                           der=der,
                           name=name,
                           sex=sex,
                           food_form=food_form,
                           meals_per_day=meals_per_day,
                           object_pronoun=object_pronoun,
                           possessive_pronoun=possessive_pronoun,
                           der_low_end=der_low_end,
                           der_high_end=der_high_end,
                           current_food_form=current_food_form,
                           total_amount_per_meal=total_amount_per_meal,
                           daily_amount_to_feed=daily_amount_to_feed,
                           der_modifier=der_modifier,
                           species=species,
                           is_nursing=is_nursing,
                           weeks_nursing=weeks_nursing)


@app.route("/completed_report", methods=["GET", "POST"])
@login_required
def completed_report():
    """Return's pet's final completed report"""
    
    try:
        pet_id = request.args.get("pet_id")
        fi = FindInfo(session["user_id"], pet_id) 
        print(f"pet ID: {pet_id}")
        
    except Exception as e:
        print(f"Couldn't find ID, Exception: {e}")
    
            
    print(f"user_id: {session['user_id']}, pet_id: {id}")     

        
    pet_data = fi.pet_data_dictionary(session["user_id"], pet_id)
        
    rer = int(pet_data[0]["rer"])
    der = pet_data[0]["der"]
        
    print(der)
    object_pronoun = fi.find_pronouns(pet_data[0]["sex"])["object_pronoun"]
    subject_pronoun = fi.find_pronouns(pet_data[0]["sex"])["subject_pronoun"]
    possessive_pronoun = fi.find_pronouns(pet_data[0]["sex"])["possessive_pronoun"]
            
    print(object_pronoun, subject_pronoun, possessive_pronoun)
        
    # Find breed ID
    breed_id = fi.find_breed_id()
    print(breed_id)
        

    # Find life stage, notes, and SVGs
    if pet_data[0]["species"] == "Canine":
        
        # Finds dog SVG
        svg = fi.find_svg(session["user_id"], pet_data[0]["pet_id"], pet_data[0]["species"], pet_data[0]["canine_breed_id"])

        if id:

            life_stage_search = db.execute(
                "SELECT life_stage, notes FROM canine_der_factors WHERE factor_id = ?",
                pet_data[0]["canine_der_factor_id"]
            )
                
    elif pet_data[0]["species"] == "Feline":
        
        # Finds cat SVG
        svg = fi.find_svg(session["user_id"], pet_data[0]["pet_id"], pet_data[0]["species"], pet_data[0]["feline_breed_id"])

        if id:
            life_stage_search = db.execute(
                "SELECT life_stage, notes FROM feline_der_factors WHERE factor_id = ?",
                pet_data[0]["feline_der_factor_id"]
            )
    print(svg)                
    if life_stage_search:
        life_stage = life_stage_search[0]["life_stage"]
        notes = life_stage_search[0]["notes"]
            

    if pet_data:
        meals_per_day = pet_data[0]["meals_per_day"]
        
    
    # Find DER range   
    if pet_data[0]["species"] == "Canine":
        
        # Find expected breed size
        breed_search = db.execute(
            "SELECT SizeCategory FROM dog_breeds WHERE BreedID = :breed_id",
            breed_id=pet_data[0]["canine_breed_id"]
        )
        
        
        if breed_search:
            breed_size_category = breed_search[0]["SizeCategory"].lower()
        
        der_low_end = float(fi.find_der_low_end(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"]) * pet_data[0]["rer"])
        der_high_end = float(fi.find_der_high_end(pet_data[0]["species"], pet_data[0]["canine_der_factor_id"]) * pet_data[0]["rer"])
        
        print(der_low_end, der_high_end)
    elif pet_data[0]["species"] == "Feline":
        
        # Find expected breed size
        breed_search = db.execute(
            "SELECT SizeCategory FROM cat_breeds WHERE BreedID = :breed_id",
            breed_id=pet_data[0]["feline_breed_id"]
        )
        
        
        if breed_search:
            breed_size_category = breed_search[0]["SizeCategory"].lower()
            
        der_low_end = float(fi.find_der_low_end(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"]))
        der_high_end = float(fi.find_der_high_end(pet_data[0]["species"], pet_data[0]["feline_der_factor_id"]))
    print(f"Breed size category: {breed_size_category}")
    # Convert to int for easier reading
    der_low_end, der_high_end = int(der_low_end), int(der_high_end)
    
    # Begin food transition table for pets switching their diet or who eat multiple diets a day
    # cf = CalculateFood(session["user_id"], id)
    # transitioning_food_amts_rec = cf.transition_food_calculator(pet_data[0]["der"])
    # transitioning_food_amts_rec = None
    # if pet_data[0]["transitioning_food_one_kcal"] != None:
    #     cf = CalculateFood(session["user_id"], id)
    #         # Loop over each day in transition period and calculate based on DER and percent of food feed

    #     transitioning_food_amts_rec = cf.transition_food_calculator(pet_data[0]["der"])
    #     print(transitioning_food_amts_rec)
        # for day in trans_percents:
        #     day_label = f"Day {day}"

        #     old_food_total = (old_food_amt * trans_percents[day]["Old Food"]) / pet_data[0]["meals_per_day"]
        #     old_food_whole_cans_or_cups = str(old_food_total).split(".")[0]
        #     old_food_partial_amount = str(old_food_total).split(".")[1]

        #     # Convert old food partial amount to volumetric
        #     old_partial_volumetric = cf.convert_decimal_to_volumetric(old_food_partial_amount)
        #     old_food_whole_cans_or_cups = int(old_food_whole_cans_or_cups)

        #     is_pouch = cur_food_form == "pouch"
        #     old_is_half_tablespoon = old_partial_volumetric == "1/2 tablespoon"
        #     old_food_form_plural = f"{cur_food_form}{'es' if is_pouch else 's'}"

        #     if old_partial_volumetric == "1":
        #         # If partial volume is more than 0.86 cups add to whole volume
        #         old_food_whole_cans_or_cups += 1
        #         old_partial_volumetric = "0"

        #     if old_food_whole_cans_or_cups == 1:
        #         if old_is_half_tablespoon and old_partial_volumetric != "0":
        #             old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural} and {old_partial_volumetric}"
        #         elif not old_is_half_tablespoon and old_partial_volumetric != "0":
        #             old_food_amt_rec = f"{old_food_whole_cans_or_cups} and {old_partial_volumetric} {old_food_form_plural}"
        #         else:
        #             old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural}"
        #     elif old_food_whole_cans_or_cups >= 1:
        #         if old_is_half_tablespoon and old_food_whole_cans_or_cups != "0":
        #             old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural} and {old_partial_volumetric}"
        #         elif not old_is_half_tablespoon and old_partial_volumetric != "0":
        #             old_food_amt_rec = f"{old_food_whole_cans_or_cups} and {old_partial_volumetric} {old_food_form_plural}"
        #         else:
        #             old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural}"
        #     elif old_food_whole_cans_or_cups == 0 and old_partial_volumetric != "0":
        #         if old_is_half_tablespoon:
        #             old_food_amt_rec = f"{old_partial_volumetric}"
        #         else:
        #             old_food_amt_rec = f"{old_partial_volumetric} {cur_food_form}"
        #     else:
        #         # Under 1 whole can or cup amount
        #         old_food_amt_rec = f"{old_partial_volumetric}"


        #     # Suggested by CoPilot      
        #     if old_food_amt_rec.startswith("0 and "):
        #         old_food_amt_rec = old_food_amt_rec.replace("0 and ", "")
        #     elif old_food_amt_rec.endswith(" and 0"):
        #         old_food_amt_rec = old_food_amt_rec.replace(" and 0", "")


        #     new_food_total = (new_food_amt * trans_percents[day]["New Food"]) / pet_data[0]["meals_per_day"]
        #     new_food_whole_cans_or_cups = str(new_food_total).split(".")[0]
        #     new_food_partial_amount = str(new_food_total).split(".")[1]

        #     # Convert new food partial amount to volumetric
        #     new_partial_volumetric = cf.convert_decimal_to_volumetric(new_food_partial_amount)
        #     new_is_pouch = new_food_form == "pouch"
        #     new_is_half_tablespoon = new_partial_volumetric == "1/2 tablespoon"
        #     new_food_form_plural = f"{new_food_form}{'es' if new_is_pouch else 's'}"
        #     new_food_whole_cans_or_cups = int(new_food_whole_cans_or_cups)

        #     if new_partial_volumetric == "1":
        #         # If partial volume is more than 0.86 cups add to whole volume
        #         new_food_whole_cans_or_cups += 1
        #         new_partial_volumetric = "0"

        #     if new_food_whole_cans_or_cups == 1:
        #         if new_is_half_tablespoon and new_partial_volumetric != "0":
        #             new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form} and {new_partial_volumetric}"
        #         elif not new_is_half_tablespoon and new_partial_volumetric != "0":
        #             new_food_amt_rec = f"{new_food_whole_cans_or_cups} and {new_partial_volumetric} {new_food_form}"
        #         else:
        #             new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form}"
        #     elif new_food_whole_cans_or_cups >= 1:
        #         if new_is_half_tablespoon and new_partial_volumetric != "0":
        #             new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form_plural} and {new_partial_volumetric}"
        #         elif not new_is_half_tablespoon and new_partial_volumetric != "0":
        #             new_food_amt_rec = f"{new_food_whole_cans_or_cups} and {new_partial_volumetric} {new_food_form_plural}"
        #         else:
        #             new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form_plural}"
        #     elif new_food_whole_cans_or_cups == 0 and new_partial_volumetric != "0":
        #         if new_is_half_tablespoon:
        #             new_food_amt_rec = f"{new_partial_volumetric}"
        #         else:
        #             new_food_amt_rec = f"{new_partial_volumetric} {new_food_form_plural}"
        #     else:
        #         # Under 1 whole can or cup amount
        #         new_food_amt_rec = f"{new_partial_volumetric}"

        #     # Suggested by CoPilot      
        #     if new_food_amt_rec.startswith("0 and "):
        #         new_food_amt_rec = new_food_amt_rec.replace("0 and ", "")
        #     elif new_food_amt_rec.endswith(" and 0"):
        #         new_food_amt_rec = new_food_amt_rec.replace(" and 0", "")

            # transitioning_food_amts_rec[day_label] = {f"Old Food {int(trans_percents[day]['Old Food'] * 100)}%": old_food_amt_rec, 
            #                                           f"New Food {int(trans_percents[day]['New Food'] * 100)}%": new_food_amt_rec}

        # print(transitioning_food_amts_rec)

        # for day in transitioning_food_amts_rec:
        #     if day.startswith("Old Food"):
        #     print(day, day["Old Food"], day["New Food")

    # print(transitioning_food_amts_rec)    
    
    print(type(pet_data[0]["bcs"]))
    return render_template("complete_report.html",
                            pet_data=pet_data,
                            rer=rer,
                            der=der,
                            der_low_end=der_low_end,
                            der_high_end=der_high_end,
                            svg=svg,
                            meals_per_day=meals_per_day,
                            life_stage=life_stage,
                            notes=notes,
                            object_pronoun=object_pronoun,
                            subject_pronoun=subject_pronoun,
                            possessive_pronoun=possessive_pronoun,
                            pet_id=pet_id,
                            breed_size_category=breed_size_category)


@app.route("/finished_reports", methods=["GET", "POST"])
@login_required
def finished_reports():
    """Provides a dropdown list of completed reports"""
    
    # Use user_id and find_info to verify species
    try:
        fi = FindInfo(session["user_id"])
        pet_list = fi.find_all_user_pets(session["user_id"])
    except Exception as e:
        flash(f"Unable to find pet list. Exception: {e}")
        return render_template("finished_reports.html")

    return render_template("finished_reports.html", pet_list=pet_list)


@app.route("/edit_info", methods=["GET", "POST"])
@login_required
def edit_info():
    """Allows a user to edit a pet's info and generate a new report"""
    
    pet_id = request.args.get("pet_id", type=int)
    
    print(pet_id)
    try:
        pet_data = db.execute(
            "SELECT * FROM pets WHERE owner_id = :user_id and pet_id = :pet_id",
            user_id=session["user_id"], pet_id=pet_id
        )
    except Exception as e:
        flash(f"Unable to find pet info. Exception: {e}")
        return render_template("edit_report.html")
        
    if request.method == "POST":
        print(pet_id)
    
    return render_template("edit_report.html", pet_data=pet_data, pet_id=pet_id)


@app.route("/wip_reports", methods=["GET", "POST"])
@login_required
def wip_reports():
    """Brings up a list of in-progress reports for the user to edit"""

    fi = FindInfo(session["user_id"])
    
    wip_reports = fi.find_wip_reports(session["user_id"])
    
    return render_template("wip_reports.html", wip_reports=wip_reports)


    
