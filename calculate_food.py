"""Contains the pet food calculator"""

from cs50 import SQL
from flask import session, flash
from find_info import FindInfo


# Configure CS50 Library to use SQLite database (for login checks)
db = SQL("sqlite:///pet_food_calculator.db")

# TODO: Move RER and DER to a different file v2
class CalculateFood():
    def __init__(self, user_id, pet_id=None):
        """Query the pet's info for calculation"""
        
        self.fi = FindInfo(user_id)
        self.pet_data = None
        
        try:
            if user_id != 0 and pet_id != 0:
                # If the user is logged in and there is a pet ID, call data dictionary
                self.pet_data = self.fi.pet_data_dictionary(user_id, pet_id)
            else:
                # If there isn't a pet ID or a user ID greater than 0, call guest
                self.pet_data = self.fi.guest_pet_data_dictionary(user_id, pet_id)

        except Exception as e:
            # Otherwise, raise exception and pass session variables
            print(f"Exception occurred: {e}")
            
        if self.pet_data is not None:
            self.calculate_rer()
        
    def calculate_rer(self):
        """Calculates the minimum number of calories a pet needs at rest per day"""
            
        print(self.pet_data[0]["weight"], self.pet_data[0]["units"])
            
        # Convert lbs weighs to kgs
        if self.pet_data[0]["units"] == "lbs":
            self.pet_data[0]["weight"] = self.pet_data[0]["weight"] / 2.2
            self.pet_data[0]["units"] = "kgs"
            
        print(self.pet_data[0]["weight"], self.pet_data[0]["units"])
            
        self.rer = int(70 * self.pet_data[0]["weight"]**0.75)
                
        print(self.rer) 
        session["rer"] = self.rer
        
        return self.rer


    def calculcate_der(self, species=None, der_factor_id=None):
        """Calculates daily caloric needs based on life stage"""
        
        # Use DER factor id to lookup DER information by species
        self.der_modifier_start_range = self.fi.find_der_low_end(species, der_factor_id)
        self.der_modifier_end_range = self.fi.find_der_high_end(species, der_factor_id)

        # Start with the mid range if this is the first report
        # TODO: check report date and change modifier choice based on weight changes
        self.der_modifier = self.fi.find_der_mid_range(species, der_factor_id)

        # Calculate DER based on the der modifier and pass variables to tempate
        if species == "Feline" and self.pet_data[0]["is_nursing"] == "y":
            self.der = round((self.rer + self.der_modifier * self.litter_size), 2)
        else:
            self.der = round(self.rer * self.der_modifier, 2)
        print(f"DER: {self.der}")
        
        self.der_low_end = self.rer * self.der_modifier_start_range
        self.der_high_end = self.rer * self.der_modifier_end_range
        self.der_low_end, self.der_high_end = int(float(self.der_low_end)), int(float(self.der_high_end))
        
        
        return {"DER": self.der, 
                "DER_low_end": self.der_low_end, 
                "DER_high_end": self.der_high_end,
                "DER_modifier": self.der_modifier}


    def convert_decimal_to_volumetric(self, partial_amount):
        """Convert partial volume amount from decimal to cups"""
        
        # Volume table source: https://amazingribs.com/more-technique-and-science/more-cooking-science/important-weights-measures-conversion-tables/
        
        self.partial_volumetric = ""
        if partial_amount == "0":
            self.partial_volumetric = "0"
        elif partial_amount > "0" and partial_amount <= "03":
            self.partial_volumetric = "1/2 tablespoon"
        elif partial_amount > "03" and partial_amount <= "06":
            self.partial_volumetric = "1/16"
        elif partial_amount > "06" and partial_amount <= "13":
            self.partial_volumetric = "1/8"
        elif partial_amount > "13" and partial_amount <= "25":
            self.partial_volumetric = "1/4"
        elif partial_amount > "25" and partial_amount <= "43":
            self.partial_volumetric = "1/3"
        elif partial_amount > "44" and partial_amount <= "60":
            self.partial_volumetric = "1/2"
        elif partial_amount > "60" and partial_amount <= "67":
            self.partial_volumetric = "2/3"
        elif partial_amount > "67" and partial_amount <= "85":
            self.partial_volumetric = "3/4"
        else:
            # If partial volume is more than 0.86 cups, add to whole volume
            self.partial_volumetric = "1"
            
        return self.partial_volumetric
    
    def transition_food_calculator(self, der):
        """Calculate how much of each food is needed if a pet is going to transition to a new food"""
        
        if self.pet_data[0]["sensitive_stomach"] == "y":
            # If pet has a sensitive stomach, transition over 10-14 days
            trans_percents = {1: 0.05, 2: 0.15, 3: 0.25, 4: 0.30, 5: 0.40, 6: 0.45,
                              7: 0.50, 8: 0.55, 9: 0.60, 10: 0.65, 11: 0.75, 12: 0.85,
                              13: 0.95, 14: 1}
        else:
            # Otherwise, transition over 5-7 days
            trans_percents = {1: 0.25, 2: 0.375, 3: 0.50, 4: 0.625, 
                              5: 0.75, 6: 0.875, 7: 1}
        
        if self.pet_data[0]["transitioning_food_two_kcal"] == 0:
            # If the user doesn't want to transition to more than one diet
            old_food_amt = round(der / self.pet_data[0]["current_food_kcal"], 2)
            new_food_amt = round(der / self.pet_data[0]["transitioning_food_one_kcal"], 2)
            
            transitioning_food_amts_rec = {}
            
            cur_food_form = ""
            if self.pet_data[0]["current_food_form"] == "dry":
                cur_food_form = "cup"
            elif self.pet_data[0]["current_food_form"] == "can":
                cur_food_form = "can"
            elif self.pet_data[0]["current_food_form"] == "pouch":
                cur_food_form = "pouch"
                
            new_food_form = ""
            if self.pet_data[0]["transitioning_food_one_form"] == "dry":
                new_food_form = "cup"
            elif self.pet_data[0]["transitioning_food_one_form"] == "can":
                new_food_form = "can"
            elif self.pet_data[0]["transitioning_food_one_form"] == "pouch":
                new_food_form = "pouch"
                
            # Loop over each day in transition period and calculate based on DER and percent of food feed
            for day in trans_percents:
                day_label = f"Day {day}"

                old_food_percent = int(trans_percents[day] * 100)
                new_food_percent = int(trans_percents[day] * 100)  
                old_food_total = (old_food_amt * trans_percents[day]) / self.pet_data[0]["meals_per_day"]
                old_food_whole_cans_or_cups = str(old_food_total).split(".")[0]
                old_food_partial_amount = str(old_food_total).split(".")[1]
                
                # Convert old food partial amount to volumetric
                old_partial_volumetric = self.convert_decimal_to_volumetric(old_food_partial_amount)
                old_food_whole_cans_or_cups = int(old_food_whole_cans_or_cups)
                is_pouch = cur_food_form == "pouch"
                old_is_half_tablespoon = old_partial_volumetric == "1/2 tablespoon"
                old_food_form_plural = f"{cur_food_form}{'es' if is_pouch else 's'}"
                
                if old_partial_volumetric == "1":
                    # If partial volume is more than 0.86 cups add to whole volume
                    old_food_whole_cans_or_cups += 1
                    old_partial_volumetric = "0"
                    
                if old_food_whole_cans_or_cups == 1:
                    if old_is_half_tablespoon and old_partial_volumetric != "0":
                        old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural} and {old_partial_volumetric}"
                    elif not old_is_half_tablespoon and old_partial_volumetric != "0":
                        old_food_amt_rec = f"{old_food_whole_cans_or_cups} and {old_partial_volumetric} {old_food_form_plural}"
                    else:
                        old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural}"
                elif old_food_whole_cans_or_cups >= 1:
                    if old_is_half_tablespoon and old_food_whole_cans_or_cups != "0":
                        old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural} and {old_partial_volumetric}"
                    elif not old_is_half_tablespoon and old_partial_volumetric != "0":
                        old_food_amt_rec = f"{old_food_whole_cans_or_cups} and {old_partial_volumetric} {old_food_form_plural}"
                    else:
                        old_food_amt_rec = f"{old_food_whole_cans_or_cups} {old_food_form_plural}"
                elif old_food_whole_cans_or_cups == 0 and old_partial_volumetric != "0":
                    if old_is_half_tablespoon:
                        old_food_amt_rec = f"{old_partial_volumetric}"
                    else:
                        old_food_amt_rec = f"{old_partial_volumetric} {cur_food_form}"
                else:
                    # Under 1 whole can or cup amount
                    old_food_amt_rec = f"{old_partial_volumetric}"
                    
                    
                # Suggested by CoPilot      
                if old_food_amt_rec.startswith("0 and "):
                    old_food_amt_rec = old_food_amt_rec.replace("0 and ", "")
                elif old_food_amt_rec.endswith(" and 0"):
                    old_food_amt_rec = old_food_amt_rec.replace(" and 0", "")
                    
                new_food_total = (new_food_amt * trans_percents[day]) / self.pet_data[0]["meals_per_day"]
                new_food_whole_cans_or_cups = str(new_food_total).split(".")[0]
                new_food_partial_amount = str(new_food_total).split(".")[1]
                
                # Convert new food partial amount to volumetric
                new_partial_volumetric = self.convert_decimal_to_volumetric(new_food_partial_amount)
                new_is_pouch = new_food_form == "pouch"
                new_is_half_tablespoon = new_partial_volumetric == "1/2 tablespoon"
                new_food_form_plural = f"{new_food_form}{'es' if new_is_pouch else 's'}"
                new_food_whole_cans_or_cups = int(new_food_whole_cans_or_cups)
                
                if new_partial_volumetric == "1":
                    # If partial volume is more than 0.86 cups add to whole volume
                    new_food_whole_cans_or_cups += 1
                    new_partial_volumetric = "0"
                
                if new_food_whole_cans_or_cups == 1:
                    if new_is_half_tablespoon and new_partial_volumetric != "0":
                        new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form} and {new_partial_volumetric}"
                    elif not new_is_half_tablespoon and new_partial_volumetric != "0":
                        new_food_amt_rec = f"{new_food_whole_cans_or_cups} and {new_partial_volumetric} {new_food_form}"
                    else:
                        new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form}"
                elif new_food_whole_cans_or_cups >= 1:
                    if new_is_half_tablespoon and new_partial_volumetric != "0":
                        new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form_plural} and {new_partial_volumetric}"
                    elif not new_is_half_tablespoon and new_partial_volumetric != "0":
                        new_food_amt_rec = f"{new_food_whole_cans_or_cups} and {new_partial_volumetric} {new_food_form_plural}"
                    else:
                        new_food_amt_rec = f"{new_food_whole_cans_or_cups} {new_food_form_plural}"
                elif new_food_whole_cans_or_cups == 0 and new_partial_volumetric != "0":
                    if new_is_half_tablespoon:
                        new_food_amt_rec = f"{new_partial_volumetric}"
                    else:
                        new_food_amt_rec = f"{new_partial_volumetric} {new_food_form_plural}"
                else:
                    # Under 1 whole can or cup amount
                    new_food_amt_rec = f"{new_partial_volumetric}"
                    
                # Suggested by CoPilot      
                if new_food_amt_rec.startswith("0 and "):
                    new_food_amt_rec = new_food_amt_rec.replace("0 and ", "")
                elif new_food_amt_rec.endswith(" and 0"):
                    new_food_amt_rec = new_food_amt_rec.replace(" and 0", "")

                old_food_percent = 1 - trans_percents[day]
                new_food_percent = trans_percents[day]       
                transitioning_food_amts_rec[day_label] = {f"Old Food {int(old_food_percent * 100)}%": old_food_amt_rec, 
                                                        f"New Food {int(new_food_percent * 100)}%": new_food_amt_rec}
        

                print(old_food_percent, new_food_percent)
                transitioning_food_amts_rec[day_label] = {f"Old Food {old_food_percent}%": old_food_amt_rec, 
                                                      f"New Food {new_food_percent}%": new_food_amt_rec}

        return transitioning_food_amts_rec        