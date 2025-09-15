from kivy.lang import Builder

from kivymd.font_definitions import theme_font_styles
from kivymd.app import MDApp

KV = '''
MDScreen:
    md_bg_color: self.theme_cls.backgroundColor

    MDRecycleView:
        id: rv
        key_viewclass: 'viewclass'
        key_size: 'height'

        RecycleBoxLayout:
            padding: dp(10)
            spacing: dp(10)
            default_size: None, dp(48)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: "vertical"
'''


class Example(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def on_start(self):
        for style in theme_font_styles:
            if style != "Icon":
                for role in theme_font_styles[style]:
                    font_size = int(theme_font_styles[style][role]["font-size"])
                    self.root.ids.rv.data.append(
                        {
                            "viewclass": "MDLabel",
                            "text": f"{style} {role} {font_size} sp",
                            "adaptive_height": "True",
                            "font_style": style,
                            "role": role,
                        }
                    )


Example().run()