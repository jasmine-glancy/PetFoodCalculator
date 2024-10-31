# PET FOOD CALCULATOR

## Video Demo: <[Pet Food Calculator](https://youtu.be/GNHv3KKURjY)>

## Description

Welcome to the Pet Food Calculator! This is an open source Flask web application that allows you to input your pet's information and get recommended feeding amounts. It will also provide specific recommendations based on your pet's life stage.

When changing your pet from one food to another, it is important to do a slow transition over 5-14 days (the actual time depends on how sensitive your pet's stomach is, though generally, the transition period is 5-7 days).

- [Project Structure](https://github.com/jasmine-glancy/PetFoodCalculator/blob/main/README_DIR/PROJECT_STRUCTURE_README.md)
- [Future Version Goals](https://github.com/jasmine-glancy/PetFoodCalculator/blob/main/README_DIR/TODO_README.md)

Please email [jasmine.glancy.vt@gmail.com](mailto:jasmine.glancy.vt@gmail.com) or submit a pull request if you would like to contribute. I'd love to collaborate. Thank you for your consideration!

## Features

- [X] Calculates Resting Energy Requirements (RER) and Daily Energy Requirements (DER) for dogs and cats
  - [X] Assigns feeding recommendations based on the middle value of the DER first
  - [X] Calculates maximum calories a dog or cat can receive from treats a day without unbalancing their diets (based on 8-10% of their RER)
- [X] Provides information to users so they may make informed decisions about their pet's nutrition by providing resources and formulas that veterinarians trust
  - [X] Including links to the American Animal Hospital Association (AAHA), Association of American Feed Control Officials (AAFCO), and World Small Animal Veterinary Association (WSAVA) so users may learn more without being swamped with misinformation
- [X] Assigns recommendations for the following:
  - [X] Dogs and cats with ideal body condition scores
  - [X] Mildly obese (Body Condition Score [BCS] 6-7/9) dogs and cats
  - [X] Obese (BCS 8+/9) dogs and cats
  - [X] Pregnant dogs and cats
  - [X] Nursing dogs and cats
- [X] Provides exercise tips if pets are not already active

### Needs Tweaking

- [ ] Pediatric dogs and cats disclaimers

### Credits

#### Images

- Canine and feline BCS image credit to [McLean Animal Hospital](https://www.mcleanvet.com/know-pet-good-weight/)
- Canine and feline puzzle toy images credited to their respective Chewy.com pages
  - [Canine](https://www.chewy.com/brightkins-dj-doggo-puzzle-feeder-dog/dp/930046)
  - [Feline](https://www.chewy.com/doc-phoebes-cat-co-indoor-hunting-cat/dp/179101)

#### SVGs

- All cat and dog SVGs credited to [WallArtBox on Etsy](https://www.etsy.com/shop/wallartbox)
- Dog paw, cat paw, food bowl, and pet food bag SVGs credited to [RostoumArt on Etsy](https://www.etsy.com/shop/RostoumArt)

## Version 2 (completed 9/3/24)

### Treat Calculator

![a screen grab of the human food lookup page](static/assets/img/human_food_search_default.png)

The portfolio project for day 96 of [100 Days of Code: The Complete Python Pro Bootcamp](https://www.udemy.com/course/100-days-of-code). The goal was to create a web application based on an API we found interesting. I chose the API from [FatSecret](https://platform.fatsecret.com/) because I wanted to to see the caloric information of various human foods. Using this information, the Pet Food Calculator calculates how much of a chosen human food they can receive per day without unbalancing their diet. Treat amounts are between 8-10% of a pet's resting energy requirements.

#### Choosing a Human Food

![a screen grab of the human food lookup page with search results](static/assets/img/human_food_search_results.png)

The user can choose the food that they want to calculate for by clicking the "Calculate Treat Amounts" button.

#### Final Treat Page Result

![a screen grab of the final treat calculation page](static/assets/img/human_food_calculation.png)

The final treat calculation page provides a reminder of the max amount of calories a pet can have per day from treats without unbalancing their diet. If there is more than a certain amount of a type of treat, users are cautioned to ensure with their vet that there will be no expected side effects or potential health issues.
