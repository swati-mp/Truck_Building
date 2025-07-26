<<<<<<< HEAD
import streamlit as st
st.set_page_config(page_title="Truck Configuration", layout="wide")
import json
import os
from utils import auth
auth.require_login_and_sidebar()

# # Access role:
# role = st.session_state.get("role", "admin") 

st.title("⚙️ Truck Load Configuration")

CONFIG_FILE = "config/config.json"

# Load configuration or set default with error handling
config = {"min_load_percent": 60, "max_load_percent": 95}  # Default values
=======
# import streamlit as st
# st.set_page_config(page_title="Truck Configuration", layout="wide")
# import json
# import os
# from utils import auth
# auth.require_login_and_sidebar()

# # # Access role:
# # role = st.session_state.get("role", "admin") 

# st.title("⚙️ Truck Load Configuration")

# CONFIG_FILE = "config/config.json"

# # Load configuration or set default with error handling
# config = {"min_load_percent": 60, "max_load_percent": 95}  # Default values
# if os.path.exists(CONFIG_FILE):
#     try:
#         with open(CONFIG_FILE, "r") as f:
#             content = f.read().strip()
#             if content:
#                 config = json.loads(content)
#     except json.JSONDecodeError:
#         st.warning("⚠️ Configuration file is invalid. Using default values.")

# with st.form("config_form"):
#     st.subheader("🚛 Truck Load Limits")
#     min_load = st.slider("Minimum Truck Load (%)", 0, 100, config.get("min_load_percent", 60))
#     max_load = st.slider("Maximum Truck Load (%)", 0, 100, config.get("max_load_percent", 95))
#     submitted = st.form_submit_button("Save Configuration")

#     if submitted:
#         if min_load >= max_load:
#             st.error("❌ Minimum load should be less than Maximum load.")
#         else:
#             config = {"min_load_percent": min_load, "max_load_percent": max_load}
#             os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
#             with open(CONFIG_FILE, "w") as f:
#                 json.dump(config, f, indent=4)
#             st.success("✅ Configuration saved successfully!")

# st.subheader("🔧 Current Configuration")
# st.json(config)

import streamlit as st
import json
import os
import pandas as pd
from utils import auth

# Page config
st.set_page_config(page_title="Truck Configuration", layout="wide")

# Auth
auth.require_login_and_sidebar()

# Title
st.title("⚙️ Truck Load Configuration")

# Config file path
CONFIG_FILE = "config/config.json"

# Load configuration or use defaults
config = {"min_load_percent": 60, "max_load_percent": 95}
>>>>>>> df81800 (Enhanced delivery map with GraphHopper for optimized truck routing.)
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            content = f.read().strip()
            if content:
                config = json.loads(content)
    except json.JSONDecodeError:
        st.warning("⚠️ Configuration file is invalid. Using default values.")

<<<<<<< HEAD
=======
# Form for configuration
>>>>>>> df81800 (Enhanced delivery map with GraphHopper for optimized truck routing.)
with st.form("config_form"):
    st.subheader("🚛 Truck Load Limits")
    min_load = st.slider("Minimum Truck Load (%)", 0, 100, config.get("min_load_percent", 60))
    max_load = st.slider("Maximum Truck Load (%)", 0, 100, config.get("max_load_percent", 95))
    submitted = st.form_submit_button("Save Configuration")

    if submitted:
        if min_load >= max_load:
            st.error("❌ Minimum load should be less than Maximum load.")
        else:
            config = {"min_load_percent": min_load, "max_load_percent": max_load}
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            st.success("✅ Configuration saved successfully!")

<<<<<<< HEAD
st.subheader("🔧 Current Configuration")
st.json(config)
=======
# Display current configuration as a table
st.subheader("📋 Current Configuration")
config_df = pd.DataFrame({
    "Parameter": ["Minimum Truck Load (%)", "Maximum Truck Load (%)"],
    "Value": [config["min_load_percent"], config["max_load_percent"]]
})
st.table(config_df)
>>>>>>> df81800 (Enhanced delivery map with GraphHopper for optimized truck routing.)
