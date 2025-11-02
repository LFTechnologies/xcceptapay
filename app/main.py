from kivy.app import App
from kivy.core.window import Window
from main_screen_clean import MainScreen

class BLEAppMain(App):
    def build(self):
        try:
            Window.size = (480, 800)
        except Exception:
            pass
        return MainScreen()

if __name__ == "__main__":
    BLEAppMain().run()
