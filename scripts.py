import requests
import os
from dotenv import load_dotenv

load_dotenv()  # load environment variables

# Obtain necessary API keys and list ID from environment variables
mailchimp_api_key = os.getenv("MAILCHIMP_API_KEY")
mailchimp_list_id = os.getenv("MAILCHIMP_LIST_ID")

# Define the endpoint URL
url = f"https://usX.api.mailchimp.com/3.0/lists/{mailchimp_list_id}/members"

# Define the headers
headers = {"Authorization": f"Bearer {mailchimp_api_key}"}

# Make the API request
response = requests.get(url, headers=headers)

# Parse the response
data = response.json()

knack_app_id = os.getenv("KNACK_APP_ID")
knack_api_key = os.getenv("KNACK_API_KEY")

headers = {
    "Content-Type": "application/json",
    "X-Knack-Application-Id": knack_app_id,
    "X-Knack-REST-API-Key": knack_api_key,
}

# Loop over the members and update each one in Knack
for member in data["members"]:
    knack_object_id = ...  # You'll need to obtain the corresponding Knack object ID
    url = f"https://api.knack.com/v1/objects/{knack_object_id}/records"

    # Define the data to update
    update_data = {
        # Fill this with the fields you want to update
    }

    # Make the API request
    response = requests.put(url, headers=headers, json=update_data)

    # Check for errors
    if response.status_code != 200:
        print(f"Failed to update member {member['email_address']}")
