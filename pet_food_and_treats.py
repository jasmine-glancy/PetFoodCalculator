"""Imports pet_foods_and-treats.db and allows queries"""

import re
from sqlalchemy import create_engine, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Define database URI
PET_FOODS_AND_TREATS_URI = "sqlite:///pet_foods_and_treats.db"

# Create engine for the database
pet_food_treat_engine = create_engine(PET_FOODS_AND_TREATS_URI)

# Create session for the database
PetFoodSession = sessionmaker(bind=pet_food_treat_engine)
pet_food_db = PetFoodSession()

class Base(DeclarativeBase):
    pass

# Define modules that map to the tables in the existing database
class AAFCOStatements(Base):
    __tablename__ = "AAFCOStatements"
    statement_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    aafco_statement = Column(String, unique=True)
    
class FoodForms(Base):
    __tablename__ = "FoodForms"
    form_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    food_form = Column(String, unique=True)
    
class LifeStages(Base):
    __tablename__ = "LifeStages"
    life_stage_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    life_stage = Column(String, unique=True)
    
class PackageSizes(Base):
    __tablename__ = "PackageSizes"
    size_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    package_size = Column(String, unique=True)
    
class ProteinSources(Base):
    __tablename__ = "ProteinSources"
    protein_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    protein_source = Column(String, unique=True)
    protein_type = Column(String)
    
    def __repr__(self):
        return f"<ProteinSources(protein_id={self.protein_id}, protein_source='{self.protein_source}', protein_type='{self.protein_type}')>"

class PetFoods(Base):
    __tablename__ = "PetFoods"
    food_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    brand = Column(String, ForeignKey("PetFoodBrands.brand_id"))
    food_name = Column(String, unique=True)
    food_form = Column(String, ForeignKey("FoodForms.form_id"))
    life_stage = Column(String, ForeignKey("LifeStages.life_stage_id"))
    description = Column(String)
    size = Column(String, ForeignKey("PackageSizes.size_id"))
    aafco_statement = Column(Integer, ForeignKey("AAFCOStatements.statement_id"))
    kcal_per_kg = Column(Integer)
    kcal_per_cup_can_pouch = Column(Integer)
    first_protein_source = Column(Integer, ForeignKey("ProteinSources.protein_id"))
    second_protein_source = Column(Integer, ForeignKey("ProteinSources.protein_id"))
    third_protein_source = Column(Integer, ForeignKey("ProteinSources.protein_id"))
    ingredient_list = Column(String)
    date_added = Column(DateTime)
    date_updated = Column(DateTime)
    
class PetFoodBrands(Base):
    __tablename__ = "PetFoodBrands"
    brand_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    brand_name = Column(String, unique=True)
    company = Column(String)
    offers_grain_free = Column(String)
    offers_raw = Column(String)
    notes = Column(String)
    
def find_aafco_statement(text):
    """Queries the database for the AAFCO statement"""
    
    aafco_statements = pet_food_db.query(
                AAFCOStatements
            ).all()
    
    formulated_to_meet = re.compile(r'formulated to meet', re.IGNORECASE)
    feeding_tests = re.compile(r'feeding tests using', re.IGNORECASE)
    
    for statement in aafco_statements:
        # Find the index of the AAFCO statement
        match = formulated_to_meet.search(text) or feeding_tests.search(text)
        
        # If the phrase is found, return the substring starting from the index
        if match:
            matched_text = text[match.start():]
            
            if statement.aafco_statement.lower() in matched_text.lower():
                return statement.statement_id
        
    return -1

    
def find_life_stage(food_name, product_category):
    """Queries the database for the life stage of the product"""
    
    life_stages = pet_food_db.query(
                LifeStages
            ).all()
            
    puppy = re.compile(r'puppy', re.IGNORECASE)
    kitten = re.compile(r'kitten', re.IGNORECASE)

    # Gestation/lactation diets
    dog_lactation_gestation = re.compile(r'babydog', re.IGNORECASE)
    cat_lactation_gestation = re.compile(r'babycat', re.IGNORECASE)
    
    # General dog or cat foods
    dog = re.compile(r'dog|canine', re.IGNORECASE)
    cat = re.compile(r'cat|feline', re.IGNORECASE)
    
    # Mature dogs and cats 
    older_age_search = re.compile(r'aging\s*\d+\+|mature\s*\d+\+', re.IGNORECASE)
    senior_search = re.compile(r'senior', re.IGNORECASE)
    
    # Adult dogs and cats
    adult = re.compile(r'adult', re.IGNORECASE)
        

    # Find the index of the life stage
    for stage in life_stages:
        # For neonate or pediatric dogs/cats
        puppy_match = (puppy.search(food_name) and dog_lactation_gestation.search(food_name)) \
            or puppy.search(food_name)

        kitten_match = (kitten.search(food_name) and cat_lactation_gestation.search(food_name)) \
            or kitten.search(food_name)
        
        # Find gestation or lactation match
        lactation_gestation_canine = dog_lactation_gestation.search(food_name)
        lactation_gestation_feline = cat_lactation_gestation.search(food_name)

        # Adult dogs or cats
        adult_dogs = ((dog.search(food_name) or dog.search(product_category)) and adult.search(food_name))
        adult_cats = ((cat.search(food_name) or cat.search(product_category)) and adult.search(food_name))
        
        # Mature/senior dogs or cats
        mature_dogs = ((dog.search(food_name) or dog.search(product_category)) and older_age_search.search(food_name))
        mature_cats = ((cat.search(food_name) or cat.search(product_category)) and older_age_search.search(food_name))
        senior_dogs = ((dog.search(food_name) or dog.search(product_category)) and senior_search.search(food_name))
        senior_cats = ((cat.search(food_name) or cat.search(product_category)) and senior_search.search(food_name))
                
        # If a string matching puppy/kitten or neonate diets is not found, look for canine or feline matches
        dog_match = dog.search(food_name) or dog.search(product_category)
        cat_match = cat.search(food_name) or cat.search(product_category)

        # If a specialty match (i.e. puppy, kitten, lactating/gestating mother dogs or cats) is found, return the substring starting from the index
        if puppy_match:
            matched_text = "Puppy"
        elif kitten_match:
            matched_text = "Kitten"
        elif lactation_gestation_canine:
            matched_text = "Adult Canine Gestation/Lactation"
        elif lactation_gestation_feline:
            matched_text = "Adult Feline Gestation/Lactation"
        elif adult_dogs:
            matched_text = "Adult Canine"
        elif adult_cats:
            matched_text = "Adult Feline"
        elif mature_dogs or senior_dogs:
            matched_text = "Adult Canine Senior"
        elif mature_cats:
            matched_text = "Adult Feline Mature"
        elif senior_cats:
            matched_text = "Adult Feline Senior"
        elif dog_match:
            matched_text = "Canine"
        elif cat_match:
            matched_text = "Feline"
        else:
            matched_text = "" 
            
        # print(f"Matched text: {matched_text}")
        
        if stage.life_stage.lower() in matched_text.lower():
            # print(f"Match found: {stage.life_stage_id}")
            return stage.life_stage_id
            
        # print(f"life stage: {stage.life_stage_id}")
    return -1
            

def find_size_id(sizes):
    """Queries the database for the container size ID"""
    
    
    normalized_sizes = sizes.strip().lower()
    
    print(normalized_sizes)
    container_sizes = pet_food_db.query(PackageSizes).filter(
            PackageSizes.package_size.ilike(normalized_sizes)
        ).all()
    
    
    if container_sizes:
        for size in container_sizes:
            return size.size_id
               
    return None

def find_food_form(food_name, product_category):
    """Queries the database for the food form ID"""
    
    food_forms = pet_food_db.query(
                FoodForms
            ).all()
    
    dry = re.compile(r'dry', re.IGNORECASE)
    canned = re.compile(r'canned|wet', re.IGNORECASE)
    pouch = re.compile(r'pouch', re.IGNORECASE)
    
    matched_text = ""
        
    for form in food_forms:        
        # Check for matches in food_name and product_category
        if dry.search(food_name) or dry.search(product_category):
            matched_text = "Dry"
        elif pouch.search(food_name) or pouch.search(product_category):
            matched_text = "Semi-moist"
        elif canned.search(food_name) or canned.search(product_category):
            matched_text = "Canned"
        
        # Find the index of the food form
        if form.food_form.lower() in matched_text.lower():
            return form.form_id
     
def find_food_brand_id(product_description):
    """Queries the database for the brand ID"""
    
    pet_food_brands = pet_food_db.query(
                PetFoodBrands
            ).all()
    
    match = None
    
    for brand in pet_food_brands:        
        # Find the index of the pet food brand
        if brand.brand_name in product_description:
            match = brand.brand_id
            print(f"Match found: {brand.brand_name}, ID: {match}")
            break
        
    if match is None:
        # If the pet food brand is not found in the name, 
        # manually add RC's index number
        match = 1 
        
    print(match)
            
    return match
        
def check_protein_id(ingredient):
    """Checks an ingredient against ProteinSources database"""

    try:
        # print(f"Checking ingredient {ingredient}...")
        protein_sources = pet_food_db.query(
                    ProteinSources
                ).all()
        
        # Find the index of the protein source
        for protein in protein_sources:

            if protein.protein_source == ingredient:
                # print(f"Checking protein ID: {protein.protein_source} with ID: {protein.protein_id}")

                return protein.protein_id

        return None
        
    except Exception as e:
        print(f"{ingredient} not found, exception: {e}")
        return None
    
def check_protein_type(protein):
    """Checks an ingredient source against ProteinSources database"""

    try:
        # print(f"Checking Protein ID {protein}...")
        protein_types = pet_food_db.query(
                    ProteinSources
                ).filter(ProteinSources.protein_id == protein).all()
        
        # print(f"Protein type found: {protein_types}")
        
        # Find the index of the protein source
        for id in protein_types:
            # print(f"Checking protein source: {id.protein_source} with ID: {id.protein_id}")

            if id.protein_id == protein:
                # print(f"Protein type found: {id.protein_type}")
                return id.protein_type

        print(f"No protein sources found for ingredient: {protein}")
        return None
        
    except Exception as e:
        print(f"{protein} not found, exception: {e}")
        return None
    
    
def check_if_diet_in_database(food):
    """Queries PetFoods for the food name"""
    

    try:
        check_food = pet_food_db.query(
            PetFoods
            ).filter_by(food_name=food).first()

        if check_food:
            return True
        
    except Exception as e:
        print(f"Diet not found, exception: {e}")
        return False


def is_link_hidden_or_missing(driver, element):
    """Checks if a link is hidden or missing,
    suggested by CoPilot"""
    
    # Check if the href attribute is empty or missing
    href = element.get_attribute("href")
    if not href:
        return True
    
    # Check if the element is hidden using CSS properties
    style = element.get_attribute("style")
    if "display: none" in style or "visibility: hidden" in style or "opacity: 0" in style:
        return True
    
    # Check if the element is hidden using computed style
    is_displayed = driver.execute_script("return window.getComputedStyle(arguments[0]).display !== 'none' && window.getComputedStyle(arguments[0]).visibility !== 'hidden' && window.getComputedStyle(arguments[0]).opacity !== '0';", element)
    if not is_displayed:
        return True
    
    return False