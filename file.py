import os
import requests
import json
import numpy
from langchain_core.documents import Document
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd

model = OllamaLLM(model="llama3.2", temperature=0)
TOKEN = "M1pKNeUlKDlHeb4ZMOtze0x8LdhtaG1UjB6gXggd"


nutrients = {"Carbohydrate":0, "Protein":0, "Fat":0, "Fiber":0, "Vitamin A":0, "Vitamin D":0, "Vitamin E":0, "Vitamin K":0, "Energy":0, "Sodium":0}


cleanUp_template="""

You are a helpful assistant that cleanup data from {data}, and give a VALID JSON array do not include any mathematical formula.
Extract these exact nutrients from the input data and return ONLY a valid JSON array:
- Carbohydrate (from "Carbohydrate, by summation")  
- Protein (from "Protein")
- Fat (from "Total lipid (fat)")
- Fiber (from "Fiber, total dietary")
- Energy (from "Energy")
- Sodium (from "Sodium, Na")  
- Vitamin A (from "Vitamin A")
- Vitamin D (from "Vitamin D (D2 + D3)")
- Vitamin E (from "Vitamin E (alpha-tocopherol)")
- Vitamin K (from "Vitamin K (phylloquinone)")

Input data: {data}

Output ONLY this JSON format with no extra text:
[
{{"name":"Carbohydrate","value":0.0}},
{{"name":"Protein","value":0.0}},
{{"name":"Fat","value":0.0}},
{{"name":"Fiber","value":0.0}},
{{"name":"Energy","value":0.0}},
{{"name":"Sodium","value":0.0}},
{{"name":"Vitamin A","value":0.0}},
{{"name":"Vitamin D","value":0.0}},
{{"name":"Vitamin E","value":0.0}},
{{"name":"Vitamin K","value":0.0}}
]
"""


convert_template="""
You are a nutrition data specialist. Convert this measurement to grams:
- Value: {weight}
- Unit: {unit}


Respond ONLY with the converted number in grams, and NOTHING else. No explanations. No units. No equations.

Return example: 14.0

"""

advice_template= """
You are a helpful nutrition advisor.

The user has a nutrient report indicating which nutrients they are lacking (positive values) or exceeding (negative values). Here is the report:
{nutrient}

Your job is to give **specific food suggestions** that help balance these nutrients.

For each positive (lacking) nutrient, recommend 1-2 common foods, ingredients, or simple dishes that contain that nutrient.

For example:
- Carbohydrate: recommend rice, oats
- Protein: recommend eggs, lentils
- Vitamin A: recommend carrots, sweet potatoes



"""


cleanUp_prompt = ChatPromptTemplate.from_template(cleanUp_template)
cleanUp_chain = cleanUp_prompt | model


convert_prompt = ChatPromptTemplate.from_template(convert_template)
convert_chain = convert_prompt | model      

advice_prompt = ChatPromptTemplate.from_template(advice_template)
advice_chain = advice_prompt | model 

      
def handle_eat(ingridients):
   for x in ingridients:
      x= json.loads(x)
      for ingridient in x:
         INGRIDIENT=ingridient["name"]
         serving=ingridient["weight"]
         print({INGRIDIENT})
         url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={INGRIDIENT}&pageSize=1&dataType=Foundation,SR Legacy,Survey (FNDDS)&api_key={TOKEN}"
         response=requests.get(url)
         data = response.json()
         val= []
         try:
            for nutrient in data["foods"][0]["foodNutrients"]:
               if "value" in nutrient:
                  nut = { "name" : nutrient["nutrientName"],
                  "value": nutrient["value"],
                  "unit": nutrient["unitName"]}
                  val.append(nut)
               elif "median" in nutrient:
                  nut = { "name" : nutrient["nutrientName"],
                  "value": nutrient["median"],
                  "unit": nutrient["unitName"]}
                  val.append(nut)
         except(IndexError) as e:
            print("i dont have this ingridient at my data base {INGRIDIENT}")
            continue
         standardized_lang = {}  
         listofNutrient = {"Carbohydrate":0, "Protein":0, "Fat":0, "Fiber":0, "Vitamin A":0, "Vitamin D":0, "Vitamin E":0, "Vitamin K":0, "Energy":0, "Sodium":0}

         for item in val:
            standardized_lang[item['name']] = float(item['value'])

         if "Carbohydrate, by summation" in standardized_lang:
            listofNutrient["Carbohydrate"] = float(standardized_lang["Carbohydrate, by summation"])
         elif "Carbohydrate, by difference" in standardized_lang:
            listofNutrient["Carbohydrate"] = float(standardized_lang["Carbohydrate, by difference"])
         else:
            listofNutrient["Carbohydrate"] = 0

         if "Protein" in standardized_lang:
            listofNutrient["Protein"]= float(standardized_lang["Protein"])
         else:
            listofNutrient["Protein"] = 0

         if "Total lipid (fat)" in standardized_lang:
            listofNutrient["Fat"]= float(standardized_lang["Total lipid (fat)"])
         else:
            listofNutrient["Fat"] = 0

         if "Fiber, total dietary" in standardized_lang:
            listofNutrient["Fiber"]= float(standardized_lang["Fiber, total dietary"])
         else:
            listofNutrient["Fiber"] = 0

         if "Energy" in standardized_lang:
            listofNutrient["Energy"]= float(standardized_lang["Energy"])
         else:
            listofNutrient["Energy"] = 0

         if "Sodium, Na" in standardized_lang:
            listofNutrient["Sodium"]= float(standardized_lang["Sodium, Na"])
         else:
            listofNutrient["Sodium"] = 0
         
         if "Vitamin A, RAE" in standardized_lang:
            listofNutrient["Vitamin A"]= float(standardized_lang["Vitamin A, RAE"])
         else:
            listofNutrient["Vitamin A"] = 0

         if "Vitamin D (D2 + D3)" in standardized_lang:
            listofNutrient["Vitamin D"]= float(standardized_lang["Vitamin D (D2 + D3)"])
         else:
            listofNutrient["Vitamin D"] = 0
         
         if "Vitamin E (alpha-tocopherol)" in standardized_lang:
            listofNutrient["Vitamin E"]= float(standardized_lang["Vitamin E (alpha-tocopherol)"])
         else:
            listofNutrient["Vitamin E"] = 0
         
         if "Vitamin K (phylloquinone)" in standardized_lang:
            listofNutrient["Vitamin K"]= float(standardized_lang["Vitamin K (phylloquinone)"])
         else:
            listofNutrient["Vitamin K"] = 0
         

         while True:
            try:
               try:
                  serving_size= convert_chain.invoke({"weight":data["foods"][0]["servingSize"], "unit":data["foods"][0]["servingSizeUnit"]})
               except (KeyError, IndexError):
                  serving_size= 100
      
               num= float(serving_size)
               break
            except (IndexError, KeyError, TypeError, ValueError):
               print("val err")

      
         times= serving / num
         print(times)

         for nutrient in listofNutrient:
            name =nutrient
            value= listofNutrient[name] * times
            nutrients[name]+= value
   print("done")
   print(nutrients)
 

documents = []
def handle_advice(age, gender, exercise, weight):

   df = pd.read_csv('nutrient_intake.csv')
   find_age= None
   find_gender= gender
   if gender == "Females" or gender == "Males" :
      if age <= 0.5:
         find_age= 2
         find_gender = "Infants"
      elif 0.6<=age<1:
         find_age= 3
         find_gender = "Infants"
      elif 1<=age<=3:
         find_age= 5
         find_gender = "Children"
      elif 4<=age<=8:
         find_age= 6
         find_gender = "Children"
      elif 9<= age <=13:
         find_age= 1
      elif 14<=age<=18:
         find_age= 2
      elif 19<=age<=30:
         find_age= 3
      elif 31<=age<=50:
         find_age= 4
      elif 51<=age<=70:
         find_age= 5
      else:
         find_age= 6
      if find_gender =="Females":
         find_age= find_age+14
      elif find_gender == "Males":
         find_age= find_age+7
   else:
      if age <= 18:
         find_age=1
      elif 19<= age<= 30:
         find_age= 2
      else:
         find_age=3

      if gender =="Pregnancy":
         find_age= find_age+21
      elif gender == "Lactation":
         find_age= find_age+25
   row= df.iloc[find_age]
   my_nutrient = {"Carbohydrate":0, "Protein":0, "Fat":0, "Fiber":0, "Vitamin A":0, "Vitamin D":0, "Vitamin E":0, "Vitamin K":0, "Energy":0, "Sodium":0}
   for col, val in row.items():
      if col in my_nutrient:
         if val == "ND":
            my_nutrient[col]=0
         else:
            my_nutrient[col]= float(val)
   if exercise != None:
      de = pd.read_csv('calories_intake.csv')
      if age>= 75:
         find_age = "75+"
      elif age<=2:
         find_age= 2
      else:
         find_age = round(age)
      find_excercise = gender +"/" + exercise
      print(find_excercise)
      calories = de.at[find_age, find_excercise]
   print(calories)
   my_nutrient["Energy"]= float(calories)
   
   my_nutrient["Carbohydrate"]= my_nutrient["Carbohydrate"]- nutrients["Carbohydrate"]
   my_nutrient["Protein"]= my_nutrient["Protein"] * weight- nutrients["Protein"]
   my_nutrient["Fiber"]= my_nutrient["Fiber"]- nutrients["Fiber"]
   my_nutrient["Vitamin A"]= my_nutrient["Vitamin A"]- nutrients["Vitamin A"]
   my_nutrient["Vitamin D"]= my_nutrient["Vitamin D"]- nutrients["Vitamin D"]
   my_nutrient["Vitamin E"]= my_nutrient["Vitamin E"]- nutrients["Vitamin E"]
   my_nutrient["Vitamin K"]= my_nutrient["Vitamin K"]- nutrients["Vitamin K"]
   my_nutrient["Energy"]= my_nutrient["Energy"]- nutrients["Energy"]
   my_nutrient["Sodium"]= my_nutrient["Sodium"]- nutrients["Sodium"]
   print(my_nutrient)
   advice = advice_prompt.invoke({"nutrient": my_nutrient})
   documents = advice_helper(my_nutrient)
   return documents


def advice_helper(my_nutrient):
   ids = {"Carbohydrate":1005, "Protein":1003, "Fat":1004, "Fiber":1079, "Vitamin A":1106, "Vitamin D":1114, "Vitamin E":1242, "Vitamin K":1185, "Energy":1008, "Sodium":1093}
   food_need=[]
   document = []
   for x in ids:
      if my_nutrient[x] > 0 and x != "Energy":
         url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={x.lower()}&pageSize=10&dataType=Foundation&api_key={TOKEN}&nutrients=ids[x]"
         response=requests.get(url)
         food_name = response.json()
         foods = []
         for name in food_name["foods"]:
            item = name["description"]
            foods.append(item)
            document.append(Document(
               page_content = item,
               metadata = {"nutrient" : x}
            ))
        
         ingridient_advice={
            "name" : x,
            "food" : foods
         }
         food_need.append(ingridient_advice)
   print(food_need)
   return document




   