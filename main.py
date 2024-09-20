import streamlit as st
import os
import json
import pandas as pd
from PIL import Image

# Set up the app
st.title("Diamond Rating App")


# Function to load json data
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


# Function to save json data
def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f)


# Function to get unrated diamonds
def get_unrated_diamonds(data_dir, rated_diamonds):
    all_images = set(
        f.split('.')[0].split('_')[-1] for f in os.listdir(os.path.join(data_dir, 'images')) if f.endswith('.jpg'))
    return list(all_images - set(rated_diamonds))


# Function to save ratings
def save_ratings(ratings, output_file):
    ratings.to_csv(output_file, index=False)


# Set up the data directory and output files
data_dir = 'data'
output_file = 'diamond_ratings.csv'
state_file = 'rated_diamonds_state.json'

# Load or initialize the state
if os.path.exists(state_file):
    with open(state_file, 'r') as f:
        rated_diamonds = json.load(f)
else:
    rated_diamonds = []

# Load existing ratings or create a new dataframe
if os.path.exists(output_file):
    ratings_df = pd.read_csv(output_file)
else:
    ratings_df = pd.DataFrame(columns=['product_number', 'rating'] + ['json_' + key for key in load_json(
        os.path.join(data_dir, 'info', os.listdir(os.path.join(data_dir, 'info'))[0])).keys()])

# Get unrated diamonds
unrated_diamonds = get_unrated_diamonds(data_dir, rated_diamonds)

if unrated_diamonds:
    # Select a random unrated diamond
    current_diamond = unrated_diamonds[0]

    # Display the image
    image_path = os.path.join(data_dir, 'images', f'diamond_image_{current_diamond}.jpg')
    image = Image.open(image_path)
    st.image(image, caption=f"Diamond {current_diamond}", use_column_width=True)

    # Get user rating
    rating = st.slider("Rate this diamond (1-5)", 1, 5, 3)

    if st.button("Submit Rating"):
        # Load json data
        json_path = os.path.join(data_dir, 'info', f'diamond_info_{current_diamond}.json')
        json_data = load_json(json_path)

        # Prepare the new row
        new_row = pd.DataFrame({'product_number': [current_diamond], 'rating': [rating],
                                **{f'json_{k}': [v] for k, v in json_data.items()}})

        # Add the new row to the dataframe
        ratings_df = pd.concat([ratings_df, new_row], ignore_index=True)

        # Save the updated dataframe
        save_ratings(ratings_df, output_file)

        # Update rated diamonds list and save to JSON
        rated_diamonds.append(current_diamond)
        save_json(rated_diamonds, state_file)

        st.success(f"Rating for Diamond {current_diamond} saved successfully!")
        st.rerun()
else:
    st.write("All diamonds have been rated!")