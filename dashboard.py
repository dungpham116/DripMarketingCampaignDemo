import streamlit as st
import hashlib
import os
import pickle  # For saving/loading the user database to disk
import os.path  # For checking if the database file exists
import pandas as pd
import random
import datetime
import requests
import json
import csv
from pprint import pprint
import io
import pandas as pd
from dotenv import load_dotenv
from crew import email_writing_agent
# --- App Configuration ---
APP_NAME = "Main Dashboard"
DATABASE_FILE = "user_database.pkl" # File to store the user database
load_dotenv('example.env')  
secret = os.getenv('SMARTLEAD_API_KEY')
# --- Database: File-based (Persistent) ---
# This stores the user database in a file using pickle.  Better than in-memory,
# but for production, a real database is still highly recommended.

def load_user_database():
    """Loads the user database from the file."""
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "rb") as f:
            return pickle.load(f)
    else:
        return {}  # Return an empty dictionary if the file doesn't exist

def save_user_database(user_database):
    """Saves the user database to the file."""
    with open(DATABASE_FILE, "wb") as f:
        pickle.dump(user_database, f)


# Initialize the user database from the file.  Crucially, do this *once*
USER_DATABASE = load_user_database()

# --- Helper Functions ---
def hash_password(password, salt=None):
    """Hashes the password using SHA-256 with a salt."""
    if salt is None:
        salt = os.urandom(16)  # Generate a random salt (16 bytes is typical)
    salted_password = salt + password.encode('utf-8')  # Combine salt and password
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return hashed_password, salt

def verify_password(hashed_password, salt, user_password):
    """Verifies if the given password matches the hashed password, given the salt."""
    salted_password = salt + user_password.encode('utf-8') # Recombine salt and password
    return hashed_password == hashlib.sha256(salted_password).hexdigest()

def create_user(username, password):
    """Creates a new user in the database."""
    global USER_DATABASE  # Needed to modify the global variable
    if username in USER_DATABASE:
        return False, "Username already exists."
    hashed_password, salt = hash_password(password)
    USER_DATABASE[username] = {"hashed_password": hashed_password, "salt": salt}  # Store both hash and salt
    save_user_database(USER_DATABASE)  # Save the database to disk!
    return True, "User created successfully."

def authenticate_user(username, password):
    """Authenticates a user based on username and password."""
    if username not in USER_DATABASE:
        return False, "Username does not exist."

    user_data = USER_DATABASE[username]
    hashed_password = user_data["hashed_password"]
    salt = user_data["salt"]

    if verify_password(hashed_password, salt, password):
        return True, "Authentication successful."
    else:
        return False, "Incorrect password."
def get_campaigns():
    """Generates mock data for the SmartLead dashboard."""
    data = requests.get(f"https://server.smartlead.ai/api/v1/campaigns?api_key={secret}")
    return data.json()

def generate_mock_data(campaign_id):
    """Generates mock data for the SmartLead dashboard."""
    data = requests.get(f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads-export?api_key={secret}")


    decoded_content = data.content.decode('utf-8')
    csv_io = io.StringIO(decoded_content)
    # data = []
    # for i in range(num_leads):
    #     lead = {
    #         'Name': f'Lead {i+1}',
    #         'Email': f'lead{i+1}@example.com',
    #         'Status': random.choice(['Active', 'Paused', 'Completed', 'Error']),
    #         'Campaign': random.choice(['Campaign A', 'Campaign B', 'Campaign C']),
    #         'Open Rate': round(random.uniform(0, 1), 2),
    #         'Click Rate': round(random.uniform(0, 1), 2),
    #         'Reply Rate': round(random.uniform(0, 1), 2),
    #         'Last Activity': datetime.date.today() - datetime.timedelta(days=random.randint(0, 30))
    #     }
    #     data.append(lead)
    return pd.read_csv(csv_io)

# --- Session Management ---
def set_session_state(username):
    """Sets the user as authenticated in the session."""
    st.session_state['username'] = username
    st.session_state['authenticated'] = True

def clear_session_state():
    """Clears the session state (logs out the user)."""
    st.session_state['username'] = None
    st.session_state['authenticated'] = False

# --- Streamlit UI Functions ---
def show_login_page():
    """Displays the login form."""
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        success, message = authenticate_user(username, password)
        if success:
            st.success(message)
            set_session_state(username)
            st.rerun()  # Rerun to show authenticated content
        else:
            st.error(message)

def show_signup_page():
    """Displays the signup form."""
    st.header("Sign Up")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if password != password_confirm:
            st.error("Passwords do not match.")
        elif not username:
            st.error("Please enter a username.")
        elif not password:
            st.error("Please enter a password.")
        else:
            success, message = create_user(username, password)
            if success:
                st.success(message + " Please login.")
            else:
                st.error(message)
def trigger_webhook():
    n8n_webhook_url = "http://localhost:5678/webhook-test/91cf178e-cc07-4218-a0c2-ce7a39c50a4d"
    status = requests.get(n8n_webhook_url)
    json = status.json()
    return json

def transform_delay_field(data):
    """
    Recursively transforms 'delayInDays' to 'delay_in_days' in a dictionary
    
    Args:
        data: Dictionary or list containing the field to transform
        
    Returns:
        Transformed data structure
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            # Transform the specific key
            if key == 'delayInDays':
                new_key = 'delay_in_days'
            else:
                new_key = key
                
            # Recursively transform nested structures
            if isinstance(value, (dict, list)):
                new_dict[new_key] = transform_delay_field(value)
            else:
                new_dict[new_key] = value
        return new_dict
    
    elif isinstance(data, list):
        return [transform_delay_field(item) for item in data]
    
    return data
def add_sequence(campaign_id):
    sequences = requests.get(f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/sequences?api_key={secret}")
    sequences = sequences.json()
    #pprint(sequences)
    sequences = transform_delay_field(sequences)
    #last_sequence = sequences[-1]
    

    # cold_email = email_writing_agent.kickoff(
    #             inputs = {
    #                 'client_mail': row['email'], # Mail to which have to reply
    #                 'conversation_history': '', # Fetch from smartlead API, need more preprocessing
    #                 'sender_name': row['first_name'],
    #                 'company_desc': 'None', # From company search tool
    #                 }
    #             ) 
    data = {
       "id": 1,
       "seq_number": 1,
       "seq_delay_details":{
           "delay_in_days": 1
       },
       "subject": "Test add sequence by AI",
       "email_body": """
            Hi {{first_name}},
            I'm Jason, Executive at Hyred, and I'm reaching out to see if you're looking to build a top-tier team in Southeast Asia or Hong Kong. Recruitment here comes with unique challenges—but we make it seamless.

            For 18 years, we've been helping companies like yours not just fill roles, but find the perfect fit—people who align with your vision, culture, and goals.

            Here's how we make hiring easier for you:
            ✔️ Local expertise - We know these markets inside out.
            ✔️ Tailored approach - We adapt to your hiring needs.
            ✔️ Culture-first mindset - Skills matter, but fit is everything.

            Would you be open to a quick chat to share with us your hiring challenges and explore how we can help you build a talented team?

            Book a 15-min Quick Call

            Looking forward to connecting!
            Best,

            Jason
            Hyred Recruitment Team
            +84 415915232""",
        }
    b = [{
        "id": 8494,
        "seq_number": 1,
        "seq_delay_details": {
            "delay_in_days": 1
        },
        "variant_distribution_type": "MANUAL_EQUAL", # ENUM MANUAL_EQUAL, MANUAL_PERCENTAGE, AI_EQUAL
        "lead_distribution_percentage": 40, # What sample % size of the lead pool to use to find the winner
        "winning_metric_property": "OPEN_RATE", # ENUM: OPEN_RATE, CLICK_RATE, REPLY_RATE,POSITIVE_REPLY_RATE
        "seq_variants": [
            {
            "subject": "Subject",
            "email_body": "<p>Hi<br><br>How are you?<br><br>Hope you're doing good</p>",
            "variant_label": "A",
            "id": 2535, # don't pass the ID key value pair when creating only pass for updating,
            "variant_distribution_percentage": 20
            },
            {
            "subject": "Ema a",
            "email_body": "<p>This is a new game a</p>",
            "variant_label": "B",
            "id": 2536, # don't pass the ID key value pair when creating only pass for updating,
            "variant_distribution_percentage": 60
            },
            {
            "subject": "C emsil",
            "email_body": "<p>Hiii C</p>",
            "variant_label": "C",
            "id": 2537, # don't pass the ID key value pair when creating only pass for updating,
            "variant_distribution_percentage": 20
            }
        ]
    },
    {
        "id": 8495,
        "seq_number": 2,
        "seq_delay_details": {
            "delay_in_days": 1
        },
        "subject": "", # blank makes the follow up in the same thread
        "email_body": "<p>Bump up right!</p>"
    }]
    st.markdown(data)
    sequences.append(data)
    for i in sequences:
        print("-----------------")
        print(i)
    a = {"sequences": data}
    st.markdown(sequences)
    st.markdown(a['sequences'])
    sequence_added = requests.post(f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/sequences?api_key={secret}", data=json.dumps({"sequences": b}), headers={'Content-Type': 'application/json'})
    print(sequence_added.json())

def show_drip_marketing_campaign_dashboard():
    """Displays the dashboard with Drip Marketing Data."""
    st.header("Drip Marketing Campaign Dashboard")
    # --- Mock Data ---
    # --- Get Campaigns ---
    campaigns = get_campaigns()
    campaign_names = None 
    df = pd.DataFrame()
    for campaign in campaigns:
        print(campaign['id'])
        data = generate_mock_data(campaign['id'])
        data['Campaign'] = campaign['name']
        df = pd.concat([df, data])
    df['id'] = df['id'].astype(str)
    df['campaign_lead_map_id'] = df['campaign_lead_map_id'].astype(str)
    # --- Sidebar ---
    with st.sidebar:
        st.header("Filters")
        campaign_filter = st.multiselect("Campaign", options=df['Campaign'].unique(), default=df['Campaign'].unique())
        status_filter = st.multiselect("status", options=['STARTED', 'BLOCKED', 'COMPLETED', 'INPROGRESS'], default=['STARTED', 'BLOCKED', 'COMPLETED', 'INPROGRESS'])
    
    # --- Apply Filters ---
    filtered_df = df[df['Campaign'].isin(campaign_filter) & df['status'].isin(status_filter)]

    # --- Layout ---
    # Columns for KPIs
    kpi1, kpi2, kpi3 = st.columns(3)

    # Calculate KPIs (using the filtered data)
    avg_open_rate = filtered_df['open_count'].sum() / len(filtered_df)
    avg_click_rate = filtered_df['click_count'].sum() / len(filtered_df) 
    avg_reply_rate = filtered_df['reply_count'].sum() / len(filtered_df)

    # Display KPIs
    kpi1.metric(label="Average Open Rate", value=f"{avg_open_rate:.2%}")
    kpi2.metric(label="Average Click Rate", value=f"{avg_click_rate:.2%}")
    kpi3.metric(label="Average Reply Rate", value=f"{avg_reply_rate:.2%}")

    # DataFrame display
    st.subheader("Lead Data")
    st.dataframe(filtered_df, use_container_width=True) # This makes the DF fill the column width
    st.caption("Mock data generated for demonstration purposes only.")

    # --- AI Agent ---
    st.subheader("Email Writing Agent")
    st.write("This is where the email writing agent would be.")
    # Add your email writing agent UI elements here
    if st.button("Add sequence"):
        response = requests.get(f"https://server.smartlead.ai/api/v1/campaigns/1485611/sequences?api_key={secret}")
        seq = add_sequence(1485611)
        st.markdown(response.json())
    if st.button("Email Writing Agent"):
        for i, row in filtered_df.iterrows():
            response = email_writing_agent.kickoff(
                inputs = {
                    'client_mail': row['email'], # Mail to which have to reply
                    'conversation_history': '', # Fetch from smartlead API, need more preprocessing
                    'sender_name': row['first_name'],
                    'company_desc': 'None', # From company search tool
                    }
                )
            print(response)
            st.markdown(response)
    
    if st.button("Logout"):
        clear_session_state()
        st.rerun()

def show_hr_assistant_chatbot():
    """Displays the HR assistant chatbot."""
    st.header("Dashboard")
    st.subheader("HR Assistant Chatbot")
    st.write("This is where the HR assistant chatbot would be.")
    # Add your HR assistant chatbot UI elements here
    if st.button("Logout"):
        clear_session_state()
        st.rerun()

def show_sales_performance_tracker():
    """Displays the sales performance tracker."""
    st.header("Dashboard")
    st.subheader("Sales Performance Tracker")
    st.write("This is where the sales performance tracker would be.")
    # Add your sales performance tracker UI elements here
    if st.button("Logout"):
        clear_session_state()
        st.rerun()  # Force rerun to update UI


# --- Main App ---
def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")

    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None

    # Navigation
    menu = ["Login", "Sign Up"]
    if st.session_state['authenticated']:
        menu = ["Drip Marketing Campaign", "HR Assistant Chatbot", "Sales Performance Tracker", "Logout"]  # Update menu if logged in
    choice = st.sidebar.selectbox("Menu", menu)

    # Display content based on authentication state
    if st.session_state['authenticated']:

        if choice == "Drip Marketing Campaign":
            show_drip_marketing_campaign_dashboard()
        elif choice == "HR Assistant Chatbot":
            show_hr_assistant_chatbot()
        elif choice == "Sales Performance Tracker":
            show_sales_performance_tracker()
        elif choice == "Logout":
            clear_session_state()
            st.rerun()
    else:
        if choice == "Login":
            show_login_page()
        elif choice == "Sign Up":
            show_signup_page()
        else: # Handle logout redirect
            show_login_page() # or display a general welcome page

if __name__ == "__main__":
    main()