import streamlit as st
from st_files_connection import FilesConnection
import pandas as pd
import json
import io
from PIL import Image

# Set up the app
st.title("Diamond Rating App")

# Initialize GCS connection
conn = st.connection('gcs', type=FilesConnection)

# GCS bucket name
BUCKET_NAME = "vanzandt-streamlit-bucket"


# Function to load json data from GCS
def load_json(file_path):
    content = conn.read(file_path, ttl=600)
    return json.loads(content)


# Function to save json data to GCS
def save_json(data, file_path):
    json_string = json.dumps(data)
    conn.fs.write_text(file_path, json_string)


# Function to get unrated diamonds
def get_unrated_diamonds(rated_diamonds):
    all_images = set()
    blobs = conn.fs.listdir(f"{BUCKET_NAME}/images")

    for blob in blobs:
        if isinstance(blob, dict) and 'name' in blob:
            file_name = blob['name']
            if file_name.endswith('.jpg'):
                image_id = file_name.split('/')[-1].split('.')[0].split('_')[-1]
                all_images.add(image_id)

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
        {'product_number': [diamond], 'rating': [rating], **{f'json_{k}': [v] for k, v in json_data.items()}})

    # Add the new row to the dataframe
    global ratings_df
    ratings_df = pd.concat([ratings_df, new_row], ignore_index=True)

    # Save the updated dataframe
    save_ratings(ratings_df, output_file)

    # Update rated diamonds list and save to JSON
    rated_diamonds.append(diamond)
    save_json(rated_diamonds, state_file)

    st.success(f"Rating of {rating} for Diamond {diamond} saved successfully!")
    st.rerun()


# Set up the output files
output_file = 'diamond_ratings.csv'
state_file = 'rated_diamonds_state.json'

# Load or initialize the state
try:
    rated_diamonds = load_json(state_file)
except:
    rated_diamonds = []

# Load existing ratings or create a new dataframe
ratings_df = conn.read(f"{BUCKET_NAME}/{output_file}", input_format="csv", ttl=600)

# Get unrated diamonds
unrated_diamonds = get_unrated_diamonds(rated_diamonds)

if unrated_diamonds:
    # Select a random unrated diamond
    current_diamond = unrated_diamonds[0]

    # Get and display the image
    image_path = f"{BUCKET_NAME}/images/diamond_image_{current_diamond}.jpg"
    try:
        image_content = conn.fs.read(image_path)
        image = Image.open(io.BytesIO(image_content))
        st.image(image, caption=f"Diamond {current_diamond}", use_column_width=True)
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")

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
else:
    st.write("All diamonds have been rated!")