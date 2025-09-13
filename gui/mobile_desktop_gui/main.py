from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDIconButton
import kivy
# Load the KV file
# Builder.load_file('screens/mainpage.kv')
# Builder.load_file('screens/menupage.kv')
# print(kivy.__version__)

class MainPage(Screen):
    pass

class MenuPage(Screen):
    pass


class CaffeApp(MDApp):
    def build(self):
        # Load the KV files INSIDE the build method, after the app object has been initialized.
        Builder.load_file('screens/mainpage.kv')
        Builder.load_file('screens/menupage.kv')

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"  # "Purple", "Red"
        sm = ScreenManager()
        sm.add_widget(MainPage(name='main'))
        sm.add_widget(MenuPage(name="menu"))
        return sm

    def show_orders(self):
        print("Orders button clicked - will show orders screen")

    def show_menu(self):
        print("Menu button clicked - will show menu screen")
        self.root.current = 'menu'

    def show_inventory(self):
        print("Inventory button clicked - will show inventory screen")

    def show_reports(self):
        print("Reports button clicked - will show reports screen")

    def back(self):
        print("back")
        self.root.current = 'main'



if __name__ == '__main__':
    CaffeApp().run()