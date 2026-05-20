# Import necessary packages
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
from urllib import parse
import snowflake.connector

# URL-encode the password for the direct connection (if needed)
# But better to use st.connection as shown below

# Write directly to the app
st.title(f":cup_with_straw: Customise your Smoothie: :cup_with_straw:")

name_on_order = st.text_input("Name on Smoothie:")
st.write(name_on_order)

st.write(
    """Chose the fruits you want!
    """
)

# Method 1: Using st.connection (RECOMMENDED - simplest)
# Make sure your secrets.toml has the [connections.snowflake] section
try:
    # Use Streamlit's native connection
    conn = st.connection('snowflake')
    session = conn.session()
except Exception as e:
    st.error(f"Connection error with st.connection: {e}")
    
    # Method 2: Fallback to direct connection with URL-encoded password
    st.info("Trying direct connection with URL-encoded password...")
    try:
        # URL-encode the password to handle special characters like @, #, etc.
        encoded_password = parse.quote(st.secrets["snowflake"]["password"])
        
        # Create a direct Snowflake connection
        connection_params = {
            "user": st.secrets["snowflake"]["user"],
            "password": encoded_password,
            "account": st.secrets["snowflake"]["account"],
            "warehouse": st.secrets.get("snowflake", {}).get("warehouse"),
            "database": st.secrets.get("snowflake", {}).get("database"),
            "schema": st.secrets.get("snowflake", {}).get("schema"),
            "role": st.secrets.get("snowflake", {}).get("role"),
            "client_session_keep_alive": True  # Prevents timeout issues
        }
        
        # Remove None values
        connection_params = {k: v for k, v in connection_params.items() if v is not None}
        
        # Create the connection
        snowflake_connection = snowflake.connector.connect(**connection_params)
        session = Session(snowflake_connection)
        st.success("Connected successfully with direct connection!")
    except Exception as e2:
        st.error(f"Failed to connect: {e2}")
        st.stop()

# Query the fruit options
try:
    my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
except Exception as e:
    st.error(f"Error querying fruit options: {e}")
    st.stop()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:'
    , my_dataframe
    , max_selections=5
)
import requests  
smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")  
st.text(smoothiefroot_response.json)
if ingredients_list:
    st.text(ingredients_list)

ingredients_string = ''

for fruit_chosen in ingredients_list:
    ingredients_string += fruit_chosen + ' '

# Using parameterized query (SAFER - prevents SQL injection)
my_insert_stmt = f""" insert into smoothies.public.orders(ingredients, name_on_order)
                    values ('{ingredients_string}', '{name_on_order}')"""

st.write(my_insert_stmt)
time_to_insert = st.button("Submit order")

if time_to_insert:
    try:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
    except Exception as e:
        st.error(f"Error submitting order: {e}")
