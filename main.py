import asyncio
import threading
import json
import os
import requests  # For HTTP requests

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen

# Import your custom screens
from login_screen import LoginScreen
from main_screen import MainScreen

################################################################################
# If you need `mock_user` or `wallet` loaded at startup, do it here
# or in main_screen. For demonstration, we keep it minimal:

# E.g., If main_screen.py expects a `mock_user`, you can define it here and pass
# it to MainScreen, or define it in main_screen. Just be consistent.

################################################################################
# Define a custom ScreenManager to hold references to the App

class MainScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # This reference to the App can help screens access app-level data
        # like app.jwt_token, app.current_user
        self.app = None


################################################################################
# The main Kivy App
class BLEAppMain(App):
    """The main Kivy App that initializes the ScreenManager and loads screens."""
    def build(self):
        # 1. Create an instance of our custom ScreenManager
        self.sm = MainScreenManager()
        self.sm.app = self  # So screens can do: app = self.manager.app

        # 2. Create instances of your login and main screens
        login_screen = LoginScreen()
        main_screen = MainScreen()

        # 3. Add them to the ScreenManager
        self.sm.add_widget(login_screen)
        self.sm.add_widget(main_screen)

        # 4. Start on the login screen
        self.sm.current = "login"

        # 5. Return the ScreenManager so Kivy can display it
        return self.sm

    # You can store the user/token here for easy access
    jwt_token = None
    current_user = None


if __name__ == "__main__":
    BLEAppMain().run()
