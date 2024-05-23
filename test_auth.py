import streamlit as st
import streamlit_authenticator as stauth
import os

# hashed_passwords = stauth.Hasher(['abc', 'def']).generate()
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator import Authenticate
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],

)
authenticator.login()

