import streamlit as st
from st_files_connection import FilesConnection
import pandas as pd
import json
import io
from PIL import Image
import random

# Set up the app
st.title("Diamond Rating App")

# Initialize GCS connection
conn = st.connection('gcs', type=FilesConnection)

# GCS bucket name
BUCKET_NAME = "vanzandt-streamlit-bucket"

# Function to load json data from GCS
def load_json(file_path):
    content = conn.read(file_path, input_format="json", ttl=600)
    # If content is already a dict, return it directly
    if isinstance(content, dict):
        return content
    # If it's a string, parse it
    elif isinstance(content, str):
        return json.loads(content)
    else:
        raise ValueError(f"Unexpected content type: {type(content)}")

# Function to save json data to GCS
def save_json(data, file_path):
    json_string = json.dumps(data)
    conn.fs.write_text(file_path, json_string)

# Function to get unrated diamonds
def get_unrated_diamonds(rated_diamonds):
    all_images = set(file_name.split('/')[-1].split('.')[0].split('_')[-1]
                     for file_name in conn.fs.listdir(f"{BUCKET_NAME}/images")
                     if file_name.endswith('.jpg'))
    return list(all_images - set(rated_diamonds))

# Function to save ratings
def save_ratings(ratings, output_file):
    csv_string = ratings.to_csv(index=False)
    conn.fs.write_text(f"{BUCKET_NAME}/{output_file}", csv_string)

# Function to handle rating submission
def submit_rating(diamond, rating):
    # Load json data
    json_data = load_json(f"{BUCKET_NAME}/info/diamond_info_{diamond}.json")

    # Prepare the new row
    new_row = pd.DataFrame(
        {'product_number': [diamond], 'rating': [rating], **{f'json_{k}': [v] for k, v in json_data.items()}}
    )

    # Add the new row to the dataframe
    global ratings_df
    ratings_df = pd.concat([ratings_df, new_row], ignore_index=True)

    # Save the updated dataframe
    save_ratings(ratings_df, output_file)

    # Update rated diamonds list and save to JSON
    st.session_state.rated_diamonds.append(diamond)
    save_json(st.session_state.rated_diamonds, f"{BUCKET_NAME}/{state_file}")

    st.success(f"Rating of {rating} for Diamond {diamond} saved successfully!")
    st.rerun()

# Set up the output files
output_file = 'diamond_ratings.csv'
state_file = 'rated_diamonds_state.json'

# Load or initialize the state
if 'rated_diamonds' not in st.session_state:
    try:
        st.session_state.rated_diamonds = load_json(f"{BUCKET_NAME}/{state_file}")
    except:
        st.session_state.rated_diamonds = []

# Load existing ratings or create a new dataframe
ratings_df = conn.read(f"{BUCKET_NAME}/{output_file}", input_format="csv", ttl=600)

# Get unrated diamonds
unrated_diamonds = get_unrated_diamonds(st.session_state.rated_diamonds)

if unrated_diamonds:
    # Select a random unrated diamond
    current_diamond = random.choice(unrated_diamonds)

    # Display the image
    image_path = f"{BUCKET_NAME}/images/diamond_image_{current_diamond}.jpg"
    try:
        with conn.open(image_path, mode="rb") as file:
            image_content = file.read()
        image = Image.open(io.BytesIO(image_content))
        st.image(image, caption=f"Diamond {current_diamond}", use_column_width=True)

        # Create rating buttons
        st.write("Rate this diamond:")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("1"):
                submit_rating(current_diamond, 1)
        with col2:
            if st.button("2"):
                submit_rating(current_diamond, 2)
        with col3:
            if st.button("3"):
                submit_rating(current_diamond, 3)
        with col4:
            if st.button("4"):
                submit_rating(current_diamond, 4)
        with col5:
            if st.button("5"):
                submit_rating(current_diamond, 5)
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")
else:
    st.write("All diamonds have been rated!")

# Display some stats
st.write(f"Total diamonds rated: {len(st.session_state.rated_diamonds)}")
st.write(f"Diamonds left to rate: {len(unrated_diamonds)}")