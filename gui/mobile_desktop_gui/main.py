from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder

# Load the KV file
Builder.load_file('screens/mainpage.kv')


class MainPage(Screen):
    pass


class CaffeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainPage(name='main'))
        return sm

    def show_orders(self):
        print("Orders button clicked - will show orders screen")

    def show_menu(self):
        print("Menu button clicked - will show menu screen")

    def show_inventory(self):
        print("Inventory button clicked - will show inventory screen")

    def show_reports(self):
        print("Reports button clicked - will show reports screen")


if __name__ == '__main__':
    CaffeApp().run()