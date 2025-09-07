from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from file import handle_eat 
from file import handle_advice
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import os
import ast


model = OllamaLLM(model="llama3.2", temperature=0)
embeddings = OllamaEmbeddings(model= "mxbai-embed-large")
db_location = "./chrome_langchain_db"
add_documents = not os.path.exists(db_location)

sorting_template="""
You are a classifier assistant. I will give you a sentence.

Your task is to classify it into one of three categories:
- "age" → if the sentence mentions the person's age or how old they are and their gender
- "eat" → if it talks about food, eating, or meals
- "advice" → if it asks for health or diet advice

ONLY respond with one of these **exact** strings:
"age", "eat", or "advice".

Here is the input:
"{question}"
"""

extract_template="""
From this input: "{question}"
xtract all specific food and drink names mentioned **literally**.

Rules:
- Only include items actually present in the text. Do NOT infer, guess, or add extra items.
- Be literal: if someone says "juice", output "juice"; do not assume type or variant.
- Return ONLY a JSON array of strings, e.g., ["item1"] or ["item1", "item2"].
- Do NOT add duplicates (if "beef burger" is found, don’t also add "burger").
- Do NOT return explanations, code, or any text outside the JSON array.

"""

advice_template="""
You are a nutritionist

Here are the name of the dish or beverage {name}

tell me about the nutrient {nutrient}

what is your advice

"""
age_template= """
You are a helpful assistant. You will get an {question}.
you just need to Give the age as a float.  Do NOT assume based on name, age, or context.
Give me only the float of the age,  Nothing else dont include anything else
Output example: 20 or 0.2
"""

gender_template= """
You are a gender classifier.

Extract gender from the following input ONLY if the gender is explicitly stated. Do NOT assume based on name, age, or context. If gender is not directly mentioned, respond with "None".

Return ONLY one of the following strings exactly Only one this is case sensitive: Males, Females, Pregnancy, Lactation or None
If the input says pregnant → return "Pregnancy"
If the input says lactating / breastfeeding → return "Lactation"

Input: {question}
"""

weight_template= """
You are a weight extractor.

Input: {question}

Rules:
- Extract the weight in kilograms as a float.
- If already in kg, just return the number.
- If in pounds/lbs, convert by multiplying with 0.453 do not include any mathematical expression.
- Round to 1 decimal place.
- Output ONLY the float (e.g., 80.0). Do not return code, text, or units or any mathematical expression.
"""

exercise_template= """
You are an exercise classifier.

Extract the excercise time from the following input. and classify them, for example if they dont work out give sedentary.
if :
- workout less than 2 times a week: sedentary
-workout atleast 2 times a week to 4: moderately active
- workout more than 4 : active

Return ONLY one of the following strings exactly Only one : sedentary, moderately active, active.
This is case sensitive so return exactly on the list
Just give me the string dont add any explanation

Input: {question}
"""

recipe_template= """
You are a culinary assistant that outputs realistic, per-serving ingredient amounts. Return ONLY a JSON array of objects.

Rules:
- If {dish_name} is a single whole food ingredient (like apple, banana), return just that ingredient with the weight of one serving.
- If {dish_name} is a complex dish (like fried chicken, beef burger, fried rice), list all typical ingredients with realistic per-serving weights.
- Each ingredient must be an object with:
  - "name": ingredient name
  - "weight": approximate weight in grams
- Do NOT include explanations, extra text, or code formatting.
- Return an array of JSON objects, not a string.

Examples:
- Single ingredient: [{{"name": "banana", "weight": 120}}]
- Complex dish: [{{"name": "bread", "weight": 60}}, {{"name": "butter", "weight": 5}}]


"""

answer_template= """
You a nutritionist and recipe expert

Here are some food to fullfill the nutrition of the person : {nutrition}

Here is the question to answer: {question}
"""

extract_prompt = ChatPromptTemplate.from_template(extract_template)
extract_chain = extract_prompt | model

recipe_prompt = ChatPromptTemplate.from_template(recipe_template)
recipe_chain = recipe_prompt | model

sorting_prompt = ChatPromptTemplate.from_template(sorting_template)
sorting_chain = sorting_prompt | model

age_prompt = ChatPromptTemplate.from_template(age_template)
age_chain = age_prompt | model

gender_prompt = ChatPromptTemplate.from_template(gender_template)
gender_chain = gender_prompt | model

exercise_prompt = ChatPromptTemplate.from_template(exercise_template)
exercise_chain = exercise_prompt | model

weight_prompt = ChatPromptTemplate.from_template(weight_template)
weight_chain = weight_prompt | model

answer_prompt = ChatPromptTemplate.from_template(answer_template)
answer_chain = answer_prompt | model

print("Hello I am an AI that is here to help you making choices about your diet.")
print("You can start by telling me what you have eaten and your age (in years) and biological gender please specify if you are pregnant or on Lactation.")
age = 0
weight = 0
gender = "None"
exercise= None
while True:
    print(gender)
    print(age)
    question = input("What can I help you with?")
    if question == "q":
        break
    que= sorting_chain.invoke({"question":question})
    if(que=="eat"):
        print("eat")
        dish_name = extract_chain.invoke({"question":question})
        dish_list = ast.literal_eval(dish_name)
        print(dish_name)
        ingredients = []
        for dish in dish_list:
            ingredient= recipe_chain.invoke({"dish_name":dish})
            ingredients.append(ingredient)
        print(ingredients)
        handle_eat(ingredients)
    if(que == "age"):
        print("yearrs")
        age = float(age_chain.invoke({"question": question}))
        gender = gender_chain.invoke({"question": question})
        print(gender) 
        print(age)
    if(que=="advice"):    
        print("advice")
        while (age == 0 or gender == "None"):
            question = input("Tell me what your age (in years) and biological gender so we can asses better: ")
            if question == "q":
                break
            try:
                age = float(age_chain.invoke({"question": question}))
                gender = gender_chain.invoke({"question": question})
                if gender == "None" or age == 0:
                    raise ValueError()
            except (ValueError) as e:
                print(f"your age is {age} and your gender is {gender}, please input missing information")
            print(gender) 
            print(age)
        while (exercise == None and gender not in ["Pregnancy", "Lactation"]):
            if (exercise == None and gender not in ["Pregnancy", "Lactation"]):
                if question == "q":
                    break
                question = input("Tell me How often you exercise: ")
                exercise = exercise_chain.invoke({"question": question})
                if exercise != "sedentary" and exercise != "moderately active" and exercise != "active":
                    exercise = None
                    print("Sorry! I didn't understand. Please try again")
        if weight==0:
            if question == "q":
                break
            question = input("Tell me what is your body weight: ")
            weight = float(weight_chain.invoke({"question": question}))
        if question == "q":
                break
        print(exercise)
        print(weight)
        documents=handle_advice(age, gender, exercise, weight)

        vector_store = Chroma(
            collection_name="Food_Nutrients",
            persist_directory = db_location,
            embedding_function = embeddings
        )
        if documents:
            vector_store.add_documents(documents)

        retriever = vector_store.as_retriever (
             search_kwargs={"k": 45}
        )
        while True:
            question = input("I have gotten your information tell me what do you want to know")
            if question == "q":
                break
            nutrient = retriever.invoke(question)
            nutrient_texts = [doc.page_content for doc in nutrient]
            print("Retrieved nutrition docs:", nutrient_texts)
            result = answer_chain.invoke({"nutrition": nutrient, "question":question})
            print(result)
        


    
         