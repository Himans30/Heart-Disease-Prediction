import sqlite3
import pickle
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# Load the trained model
try:
    heart_disease_model = pickle.load(open('heart_disease_model.sav', 'rb'))
except FileNotFoundError:
    st.error("Model file not found. Please upload 'heart_disease_model.sav'.")
    st.stop()

# Initialize session state
#welcome
if 'user_data' not in st.session_state:
    st.session_state['user_data'] = []

if 'users' not in st.session_state:
    st.session_state['users'] = {"admin": {"password": "password123", "is_admin": True}}

if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None

if 'selected_page' not in st.session_state:
    st.session_state['selected_page'] = 'Home'

# SQLite Database Setup
def create_db():
    conn = sqlite3.connect('heart_disease.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        is_admin BOOLEAN NOT NULL
    )
    ''')

    # Create predictions table with a username column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        username TEXT,
        age INTEGER,
        sex INTEGER,
        chest_pain_type INTEGER,
        resting_blood_pressure INTEGER,
        cholesterol INTEGER,
        fasting_blood_sugar INTEGER,
        resting_ecg INTEGER,
        max_heart_rate INTEGER,
        exercise_induced_angina INTEGER,
        oldpeak REAL,
        slope INTEGER,
        num_vessels INTEGER,
        thalassemia INTEGER,
        prediction INTEGER,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    ''')

    conn.commit()
    conn.close()

# Initialize the database
create_db()

# Helper Functions
def authenticate_user(username, password):
    """Authenticate a user based on stored credentials."""
    conn = sqlite3.connect('heart_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def register_user(username, password):
    """Register a new user in the database."""
    conn = sqlite3.connect('heart_disease.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)', (username, password,False))
    conn.commit()
    conn.close()

def store_prediction_data(username, input_data, prediction):
    """Store prediction data for a user in the database."""
    conn = sqlite3.connect('heart_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO predictions (username, age, sex, chest_pain_type, resting_blood_pressure, cholesterol, 
                            fasting_blood_sugar, resting_ecg, max_heart_rate, exercise_induced_angina, 
                            oldpeak, slope, num_vessels, thalassemia, prediction)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, *input_data, prediction))
    conn.commit()
    conn.close()

def get_all_user_data():
    """Fetch all user prediction data."""
    conn = sqlite3.connect('heart_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM predictions')
    user_data = cursor.fetchall()
    conn.close()
    return user_data

def get_all_users():
    """Fetch all registered users from the database."""
    conn = sqlite3.connect("heart_disease.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, is_admin FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

# Sidebar for navigation
with st.sidebar:
    selected = option_menu(
        'Heart Disease Prediction System',
        ['Home', 'Sign In/Sign Up', 'Heart Disease Prediction', 'Admin', 'About'],
        icons=['house', 'key', 'heart', 'person', 'info-circle'],
        default_index=0, key='sidebar_menu'
    )
    
    # Show logout button only if user is logged in
    if st.session_state['logged_in_user']:
        st.button("Logout", on_click=lambda: st.session_state.update(logged_in_user=None, user_data=[], selected_page='Home'))

    st.session_state['selected_page'] = selected  # Store the selected page

# Home Page
if selected == 'Home':
    st.title("Welcome to the Heart Disease Prediction System")
    st.write("""
        This system uses machine learning algorithms to assess the likelihood of heart disease based on user-provided health data.
        
        ### Key Features:
        - **User Authentication**: Secure sign-in and sign-up for users.
        - **Heart Disease Prediction**: Input your health details and get a prediction on heart disease risk.
        - **Admin Dashboard**: Admins can view user data and download it for further analysis.
    """)
    st.image("white-sign-love-heart-line-red-843297-pxhere.com.jpg", caption="Heart Disease Awareness", use_container_width=True)
    

# Sign In/Sign Up Page
if selected == 'Sign In/Sign Up':
    st.title("Sign In / Sign Up")
    
    # Tabs for Sign In and Sign Up
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    # Sign In Tab
    with tab1:
        st.subheader("Sign In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state['logged_in_user'] = username
                st.session_state['selected_page'] = 'Heart Disease Prediction'
                st.success(f"Welcome back, {username}!")
            else:
                st.error("Invalid credentials. Try again.")

    # Sign Up Tab
    with tab2:
        st.subheader("Sign Up")
        new_username = st.text_input("Choose a Username")
        new_password = st.text_input("Choose a Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords do not match. Please try again.")
            elif authenticate_user(new_username, new_password):
                st.error("Username already exists. Please choose another.")
            else:
                register_user(new_username, new_password)
                st.success("User registered successfully! You can now log in.")

# Prediction Page
if selected == 'Heart Disease Prediction':
    if not st.session_state['logged_in_user']:
        st.warning("Please sign in to access this page.")
    else:
        st.title('Heart Disease Prediction')

        # Input fields
        st.write("### Enter your health details:")
        col1, col2, col3 = st.columns(3)

        with col1:
            age = st.number_input('Age', min_value=1, max_value=120, step=1)
        with col2:
            sex = st.selectbox('Sex', options=[0, 1], format_func=lambda x: 'Male' if x == 1 else 'Female')
        with col3:
            chest_pain_type = st.selectbox('Chest Pain Type', options=[0, 1, 2, 3])

        with col1:
            resting_blood_pressure = st.number_input('Resting Blood Pressure (mm Hg)', min_value=0, max_value=200, step=1)
        with col2:
            cholesterol = st.number_input('Cholesterol (mg/dl)', min_value=0, max_value=600, step=1)
        with col3:
            fasting_blood_sugar = st.selectbox('Fasting Blood Sugar > 120 mg/dl', options=[0, 1])

        with col1:
            resting_ecg = st.selectbox('Resting Electrocardiographic Results', options=[0, 1, 2])
        with col2:
            max_heart_rate = st.number_input('Maximum Heart Rate Achieved', min_value=0, max_value=220, step=1)
        with col3:
            exercise_induced_angina = st.selectbox('Exercise Induced Angina', options=[0, 1])

        oldpeak = st.number_input('Oldpeak', min_value=0.0, max_value=10.0, step=0.1)
        slope = st.selectbox('Slope of the Peak Exercise ST Segment', options=[0, 1, 2])
        num_vessels = st.selectbox('Number of Major Vessels Colored by Fluoroscopy', options=[0, 1, 2, 3])
        thalassemia = st.selectbox('Thalassemia', options=[0, 1, 2, 3])

        if st.button('Predict'):
            input_data = [age, sex, chest_pain_type, resting_blood_pressure, cholesterol, fasting_blood_sugar, 
                          resting_ecg, max_heart_rate, exercise_induced_angina, oldpeak, slope, num_vessels, thalassemia]
            prediction = heart_disease_model.predict([input_data])[0]
            store_prediction_data(st.session_state['logged_in_user'], input_data, prediction)

            st.write("### Prediction Result")
            if prediction == 1:
                st.error("Likely to have heart disease.")
            else:
                st.success("Unlikely to have heart disease.")
            
            df_input = pd.DataFrame([input_data], columns=['Age', 'Sex', 'Chest Pain', 'Resting BP', 'Cholesterol', 
                                                           'Fasting Blood Sugar', 'Resting ECG', 'Max Heart Rate', 
                                                           'Exercise Angina', 'Oldpeak', 'Slope', 'Vessels', 'Thalassemia'])
            st.write("### Input Data")
            st.dataframe(df_input)
            df_input['Prediction'] = 'Heart Disease' if prediction == 1 else 'No Heart Disease'
            
            st.bar_chart(df_input.drop(columns=['Prediction']).T)



# Admin Page
if selected == 'Admin':
    if not st.session_state['logged_in_user'] or not st.session_state['users'].get(st.session_state['logged_in_user'], {}).get('is_admin', False):
        st.warning("Only admins can access this page.")
    else:
        st.title("Admin Dashboard")
        
        # Section 1: Registered Users
        st.subheader("Registered Users")
        users = get_all_users()  # Fetch all registered users from the database
        user_df = pd.DataFrame(users, columns=['Username', 'Password', 'Is Admin'])  # Adjust column names as per your DB
        st.write(f"Total Registered Users: {len(user_df)}")
        st.dataframe(user_df)

        # Section 2: Prediction Data
        st.subheader("User Prediction Data")
        user_data = get_all_user_data()  # Fetch all prediction data from the database
        if user_data:
            df = pd.DataFrame(user_data, columns=[
                'Username', 'Age', 'Sex', 'Chest Pain Type', 'Resting BP', 'Cholesterol',
                'Fasting Blood Sugar', 'Resting ECG', 'Max Heart Rate', 'Exercise Angina', 
                'Oldpeak', 'Slope', 'Num Vessels', 'Thalassemia', 'Prediction'
            ])
           
            st.dataframe(df)

            # Convert DataFrame to CSV
            csv = df.to_csv(index=False)

            # Add a download button for the CSV file
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name="user_predictions.csv",
                mime="text/csv"
            )
        else:
            st.info("No prediction data available.")


# About Page
if selected == 'About':
    st.title("About This System")
    st.write("""
        The Heart Disease Prediction System is designed to help individuals assess their risk of heart disease using machine learning techniques. 
        The model is trained on a dataset of health parameters and provides predictions based on user input.
        
               
        ### Acknowledgments:
        We would like to thank the contributors of the dataset and the open-source community for their invaluable resources and support.
    """)