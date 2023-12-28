from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import shelve
import time
import re

#--------------------------------------------------------------
# Load API key
#--------------------------------------------------------------

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# --------------------------------------------------------------
# Upload file
# --------------------------------------------------------------

def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(file=open(path, "rb"), purpose="assistants")
    return file

file = upload_file("dataset.pdf")

# --------------------------------------------------------------
# Create assistant
# --------------------------------------------------------------

def create_assistant(file):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name="mobelli AI",
        instructions="As the mobelli AI, developed by Tab Robotics, your main responsibility is to provide users with assistance regarding the services offered by mobelli. When addressing users, please use the pronoun 'we' to refer to the company. Your integration on their website aims to ensure prompt and relevant support in a professional manner, enabling users to navigate through available options efficiently. As a user, my questions will solely pertain to mobelli, and not about the AI itself. Therefore, please only provide information based on the data provided. For instance, if I ask 'What services do you provide?', your response should be concise and informative, stating the specific services offered by mobelli. Additionally, when the user greets you at the start of the conversation, please respond with 'How can I assist you today?' That's all. Please try to answer in very short format points but also provide the most important information in short. Please maintain some space between the sentences or points snd replace '-' with a mid size dot before a sentence'",                                    
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=[file.id],
    )
    return assistant

assistant = create_assistant(file)

print("Creating assistant [-------------------1/5-------------------]")
time.sleep(0.5)
print("Creating assistant [-------------------2/5-------------------]")
time.sleep(0.5)
print("Creating assistant [-------------------3/5-------------------]")
time.sleep(0.5)
print("Creating assistant [-------------------4/5-------------------]")
time.sleep(0.5)
print("Creating assistant [-------------------5/5-------------------]")

assist_id = assistant.id()

print(f"Created Assistant with Assistant ID :", assist_id)

# --------------------------------------------------------------
# Thread management
# --------------------------------------------------------------

def check_if_thread_exists(wa_id):
    with shelve.open("thread_data//threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)

def store_thread(wa_id, thread_id):
    with shelve.open("thread_data//threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

# --------------------------------------------------------------
# Generate response
# --------------------------------------------------------------
        
def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To {name}:", new_message)
    cleaned_response = re.sub(r'【.*】', '', new_message)
    return cleaned_response

# --------------------------------------------------------------
# Run assistant
# --------------------------------------------------------------

def run_assistant(thread):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(assist_id)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # Wait for completion
    while run.status != "completed":
        # Be nice to the API
        #time.sleep(0.1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message

# --------------------------------------------------------------
# Test assistant with flask
# --------------------------------------------------------------

app = Flask(__name__)
CORS(app)

conversation_details = {}
current_stage = "initial"


@app.route('/')
def home():
    return render_template('bannner.html')

# Define a function to check if the user wants to book an appointment
def is_booking_request(user_input):
    booking_keywords = ["track my order", "where is my order", "order tracking", "order status"]
    return any(keyword in user_input for keyword in booking_keywords)

# Define route for getting response
@app.route('/get-response', methods=['POST'])
def get_response():
    global current_stage
    user_input = request.json['message'].lower().strip()
    user_id = request.json.get('user_id')  # Get user/session identifier from the request
    if not user_id:
        return jsonify({'response': "Error: User ID is missing or invalid."})

    # Check if user wants to book an appointment
    if is_booking_request(user_input) and current_stage == "initial":
        current_stage = "date"
        return jsonify({'response': "Sure, I can help you with that. What's your order number?"})

    # Handle stages for booking an appointment
    if current_stage != "initial":
        if current_stage == "date":
            conversation_details['time'] = user_input
            response = "Thank you! What is your name?"
            current_stage = "name"
        elif current_stage == "name":
            conversation_details['name'] = user_input
            response = "Please provide your phone number."
            current_stage = "phone"
        elif current_stage == "phone":
            conversation_details['phone'] = user_input
            response = "Please provide your email address."
            current_stage = "email"
        elif current_stage == "email":
            conversation_details['email'] = user_input
            response = "Thank you! Your order has been {'info'} and you will receive an email for more info about your order."
            current_stage = "initial"  # Reset for the next user
    else:
        flask_output = generate_response(user_input, wa_id=user_id, name="User")  # Use user_id for wa_id
        return jsonify({'response': flask_output})

    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(debug=True)
