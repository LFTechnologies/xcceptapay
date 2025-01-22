import requests
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

API_BASE_URL = "http://localhost:3000"

def register_user(username, email, password):
    url = f"{API_BASE_URL}/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    try:
        resp = requests.post(url, json=data)
        resp.raise_for_status()
        return resp.json()  # Created user object (e.g. { username, email, _id, ... })
    except Exception as e:
        return {"error": str(e)}

def login_user(email, password):
    url = f"{API_BASE_URL}/auth/login"
    data = {"email": email, "password": password}
    try:
        resp = requests.post(url, json=data)
        resp.raise_for_status()
        return resp.json()  # { message, token, user: {...} }
    except Exception as e:
        return {"error": str(e)}

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"  # Screen name for the ScreenManager

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.title_label = Label(text="Register or Login", size_hint=(1, 0.1))
        layout.add_widget(self.title_label)

        self.username_input = TextInput(
            hint_text="Username (for register)", 
            multiline=False, 
            size_hint=(1, 0.1)
        )
        layout.add_widget(self.username_input)

        self.email_input = TextInput(
            hint_text="Email", 
            multiline=False, 
            size_hint=(1, 0.1)
        )
        layout.add_widget(self.email_input)

        self.password_input = TextInput(
            hint_text="Password", 
            multiline=False, 
            password=True, 
            size_hint=(1, 0.1)
        )
        layout.add_widget(self.password_input)

        button_bar = BoxLayout(orientation="horizontal", size_hint=(1, 0.15), spacing=5)

        register_btn = Button(text="Register")
        register_btn.bind(on_press=self.register_action)
        button_bar.add_widget(register_btn)

        login_btn = Button(text="Login")
        login_btn.bind(on_press=self.login_action)
        button_bar.add_widget(login_btn)

        layout.add_widget(button_bar)

        self.feedback_label = Label(text="", size_hint=(1, 0.15))
        layout.add_widget(self.feedback_label)

        self.add_widget(layout)

    def register_action(self, instance):
        username = self.username_input.text.strip()
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not email or not password:
            self.feedback_label.text = "All fields required for registration."
            return

        result = register_user(username, email, password)
        if "error" in result:
            self.feedback_label.text = f"Register error: {result['error']}"
        else:
            # result might look like { _id: "...", username: "John", email: "...", ... }
            self.feedback_label.text = f"User registered: {result.get('username','???')}"

    def login_action(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()

        if not email or not password:
            self.feedback_label.text = "Email & Password required."
            return

        result = login_user(email, password)
        if "error" in result:
            self.feedback_label.text = f"Login error: {result['error']}"
        elif "token" in result:
            # The API response should be something like:
            # {
            #   "message": "Login successful",
            #   "token": "...",
            #   "user": {
            #       "_id": "...", 
            #       "username": "...",
            #       "email": "...",
            #       ...
            #   }
            # }
            app = self.manager.app  # The Kivy App instance via ScreenManager
            app.jwt_token = result["token"]

            # Rename _id to id for convenience
            user_data = result["user"]
            if "_id" in user_data:
                user_data["id"] = user_data.pop("_id")

            # Store entire user object
            app.current_user = user_data

            self.feedback_label.text = f"Login success: {app.current_user.get('username','???')}"
            # Switch to MainScreen
            self.manager.current = "main"
        else:
            self.feedback_label.text = "Unexpected response from server."
