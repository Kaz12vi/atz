from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.popup import Popup

import sys
import requests

Window.size = (700, 540)

class ChatLog(Label):
    pass

class SecureMessenger(BoxLayout):
    chat_history = StringProperty("")
    username = "YourUsername"
    email = ""
    password = ""
    fav_contacts = []
    friends_list = []
    selected_contact = StringProperty("")

    def __init__(self, username=None, email=None, password=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, 1)
        if username:
            self.username = username
        if email:
            self.email = email
        if password:
            self.password = password
        if not hasattr(self, 'chat_history') or self.chat_history is None:
            self.chat_history = ""
        if not hasattr(self, 'friends_list') or self.friends_list is None:
            self.friends_list = []
        if not hasattr(self, 'fav_contacts') or self.fav_contacts is None:
            self.fav_contacts = []
        # Always attempt to load user data, but never block UI construction
        try:
            self.load_user_data()
        except Exception as e:
            self.chat_history = f"[color=ff0000]Error loading user data: {e}[/color]"
        # Always show a welcome message if chat_history is empty
        if not self.chat_history or not self.chat_history.strip():
            self.chat_history = '[b][color=2288ff]Welcome to Secure Messenger![/color][/b]\nStart chatting securely.'
        # --- Sidebar construction ---
        sidebar = BoxLayout(orientation='vertical', size_hint_x=0.32, padding=0, spacing=0)
        sidebar_canvas = BoxLayout(orientation='vertical', padding=0, spacing=0)
        with sidebar_canvas.canvas.before:
            Color(1, 1, 1, 1)
            self.sidebar_rect = Rectangle(size=sidebar_canvas.size, pos=sidebar_canvas.pos)
        sidebar_canvas.bind(size=self._update_sidebar_rect, pos=self._update_sidebar_rect)
        profile_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=(8,8,8,8), spacing=8)
        profile_pic = Button(text='👤', size_hint_x=None, width=44, background_color=(0.8,0.9,1,1), font_size=28, color=(0.2,0.4,0.8,1))
        profile_name = Label(text=f'[b]{self.username}[/b]', markup=True, font_size=17, color=(0.2,0.4,0.8,1), size_hint_x=1)
        profile_box.add_widget(profile_pic)
        profile_box.add_widget(profile_name)
        sidebar_canvas.add_widget(profile_box)

        Window.bind(on_request_close=lambda *args: (App.get_running_app().stop(), sys.exit(0)))
        # Intercept all right-clicks in the sidebar area
        def suppress_right_clicks(window, touch):
            if touch.button == 'right' and touch.x < 200:  # Sidebar width
                return True
        Window.bind(on_touch_down=suppress_right_clicks)

        # Custom clickable label for contacts (no ripple)
        class ClickableLabel(Label):
            def on_touch_down(self, touch):
                if self.collide_point(*touch.pos) and touch.button == 'left':
                    if hasattr(self, 'on_click'):
                        self.on_click()
                    return True
                return False
        # Custom row for contacts (avatar + name)
        class ContactRow(BoxLayout):
            def __init__(self, contact_name, on_click=None, **kwargs):
                super().__init__(orientation='horizontal', size_hint_y=None, height=36, spacing=6, **kwargs)
                profile_pic = Label(text='👤', font_size=18, size_hint_x=None, width=28, color=(0.2,0.4,0.8,1))
                name_lbl = ClickableLabel(text=contact_name, font_size=15, color=(0.18,0.18,0.18,1))
                if on_click:
                    name_lbl.on_click = lambda: on_click(name_lbl)
                self.add_widget(profile_pic)
                self.add_widget(name_lbl)
        # Collapsible Favourites section (now empty, no friends)
        self.fav_expanded = True
        def update_fav_height():
            fav_contacts_box.height = 0
        def toggle_fav_section():
            self.fav_expanded = not self.fav_expanded
            fav_contacts_box.clear_widgets()
            fav_arrow.text = '▲' if self.fav_expanded else '▼'
            update_fav_height()
        fav_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=28)
        fav_label = Label(text='[b]Favourites[/b]', markup=True, font_size=15, color=(0.2,0.4,0.8,1), size_hint_x=0.8)
        fav_arrow = ClickableLabel(text='▲', font_size=15, color=(0.2,0.4,0.8,1), size_hint_x=0.2)
        fav_arrow.on_click = toggle_fav_section
        fav_header.add_widget(fav_label)
        fav_header.add_widget(fav_arrow)
        sidebar_canvas.add_widget(fav_header)
        fav_contacts_box = BoxLayout(orientation='vertical', size_hint_y=None)
        update_fav_height()
        sidebar_canvas.add_widget(fav_contacts_box)

        # Spacer to push bottom row down
        sidebar_canvas.add_widget(Widget())

        # Bottom row: gear icon only for settings, add friend next to it, flush and visually separated
        bottom_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=8, padding=(8,8,8,8))
        normal_color = (0.2, 0.5, 0.9, 1)
        pressed_color = (0.13, 0.35, 0.7, 1)  # lighter blue than outline
        settings_btn = Button(text='⚙️', size_hint=(None, 1), width=44, font_size=22, background_color=normal_color, color=(1,1,1,1), border=(0,0,0,0), background_normal='', background_down='')
        add_friend_btn = Button(text='+', size_hint=(None, 1), width=44, font_size=22, background_color=normal_color, color=(1,1,1,1), border=(0,0,0,0), background_normal='', background_down='')
        from kivy.uix.image import Image
        placeholder_img = Image(source='data/logo/kivy-icon-256.png', size_hint=(None, 1), width=44)
        def on_press_btn(instance):
            instance.background_color = pressed_color
        def on_release_btn(instance):
            instance.background_color = normal_color
        settings_btn.bind(on_press=on_press_btn, on_release=on_release_btn)
        add_friend_btn.bind(on_press=on_press_btn, on_release=on_release_btn)
        # Popup handlers
        def open_settings_popup(instance):
            content = BoxLayout(orientation='vertical', padding=16, spacing=12)
            content.add_widget(Label(text='Settings', font_size=20, color=(0.18,0.18,0.18,1)))
            close_btn = Button(text='Close', size_hint_y=None, height=40)
            popup = Popup(title='', content=content, size_hint=(None, None), size=(320, 220), auto_dismiss=False)
            close_btn.bind(on_press=popup.dismiss)
            content.add_widget(close_btn)
            popup.open()
        def open_add_friend_popup(instance):
            # Create the popup content
            popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            popup_content.add_widget(Label(text='Add a Friend', font_size=20, size_hint_y=None, height=30))
            username_input = TextInput(hint_text='Username', multiline=False, size_hint_y=None, height=40)
            email_input = TextInput(hint_text='Email', multiline=False, size_hint_y=None, height=40)
            popup_content.add_widget(username_input)
            popup_content.add_widget(email_input)
            # Buttons row
            buttons_row = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
            send_button = Button(text='Send', size_hint=(None, None), size=(100, 40))
            close_button = Button(text='Close', size_hint=(None, None), size=(100, 40))
            close_button.bind(on_release=lambda x: popup.dismiss())
            # Placeholder for send action
            send_button.bind(on_release=lambda x: self.send_friend_request(username_input.text, email_input.text, popup))
            buttons_row.add_widget(send_button)
            buttons_row.add_widget(close_button)
            popup_content.add_widget(buttons_row)
            popup = Popup(title='', content=popup_content, size_hint=(None, None), size=(350, 250), auto_dismiss=False)
            popup.open()
        settings_btn.bind(on_release=open_settings_popup)
        add_friend_btn.bind(on_release=open_add_friend_popup)
        def add_outline(btn):
            from kivy.graphics import Color, Line
            def update_outline(instance, value):
                btn.canvas.after.clear()
                with btn.canvas.after:
                    Color(0.08, 0.18, 0.38, 1)  # dark blue
                    Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=2)
            btn.bind(pos=update_outline, size=update_outline)
            update_outline(btn, None)

        add_outline(settings_btn)
        add_outline(add_friend_btn)
        bottom_row.add_widget(settings_btn)
        bottom_row.add_widget(add_friend_btn)
        bottom_row.add_widget(placeholder_img)
        sidebar_canvas.add_widget(bottom_row)

        sidebar.add_widget(sidebar_canvas)
        self.add_widget(sidebar)

        # --- Main chat area ---
        main_area = BoxLayout(orientation='vertical', padding=16, spacing=12)
        # Chat Area
        self.chat_scroll = ScrollView(size_hint=(1, 0.75), bar_width=8)
        self.chat_log = ChatLog(text=self.chat_history, markup=True, valign='top', size_hint_y=None, color=(0.18,0.18,0.18,1), font_size=16)
        self.chat_log.bind(texture_size=self._update_chat_height)
        self.chat_scroll.add_widget(self.chat_log)
        main_area.add_widget(self.chat_scroll)

        # Input Area
        input_box = BoxLayout(size_hint_y=None, height=48, spacing=8)
        self.message_input = TextInput(hint_text='Type a message...', multiline=False, font_size=18, background_color=(1,1,1,1), foreground_color=(0.18,0.18,0.18,1), padding=(12,12,12,12), size_hint_x=0.85)
        self.send_button = Button(text='Send', size_hint_x=0.15, background_color=(0.2, 0.6, 1, 1), font_size=18, border=(16,16,16,16))
        self.send_button.bind(on_press=self.send_message)
        self.message_input.bind(on_text_validate=self.send_message)
        input_box.add_widget(self.message_input)
        input_box.add_widget(self.send_button)
        main_area.add_widget(input_box)

        self.add_widget(main_area)

    # Popup handlers
    def open_settings_popup(instance):
        content = BoxLayout(orientation='vertical', padding=16, spacing=12)
        content.add_widget(Label(text='Settings', font_size=20, color=(0.18,0.18,0.18,1)))
        close_btn = Button(text='Close', size_hint_y=None, height=40)
        popup = Popup(title='', content=content, size_hint=(None, None), size=(320, 220), auto_dismiss=False)
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()
    def open_add_friend_popup(instance):
        content = BoxLayout(orientation='vertical', padding=16, spacing=12)
        # Create the popup content
        popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup_content.add_widget(Label(text='Add a Friend', font_size=20, size_hint_y=None, height=30))
        username_input = TextInput(hint_text='Username', multiline=False, size_hint_y=None, height=40)
        email_input = TextInput(hint_text='Email', multiline=False, size_hint_y=None, height=40)
        popup_content.add_widget(username_input)
        popup_content.add_widget(email_input)
        # Buttons row
        buttons_row = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        send_button = Button(text='Send', size_hint=(None, None), size=(100, 40))
        close_button = Button(text='Close', size_hint=(None, None), size=(100, 40))
        close_button.bind(on_release=lambda x: popup.dismiss())
        # Use closure to capture self
        def send_action(x):
            self.send_friend_request(username_input.text, email_input.text, popup)
        send_button.bind(on_release=send_action)
        buttons_row.add_widget(send_button)
        buttons_row.add_widget(close_button)
        popup_content.add_widget(buttons_row)
        popup = Popup(title='', content=popup_content, size_hint=(None, None), size=(350, 250), auto_dismiss=False)
        popup.open()
    def send_friend_request(self, username, email, popup):
        # Placeholder for sending friend request logic
        # You can add backend integration here
        print(f"Friend request sent to: {username} ({email})")
        popup.dismiss()

    def select_contact(self, instance):
        self.selected_contact = instance.text
        # ...future: update chat history for selected contact...

    def _update_chat_height(self, instance, value):
        self.chat_log.height = self.chat_log.texture_size[1]
        self.chat_log.text_size = (self.chat_log.width, None)

    def send_message(self, instance):
        message = self.message_input.text.strip()
        if message:
            self.chat_history += f'[b][color=2288ff]You:[/color][/b] {message}\n'
            self.chat_log.text = self.chat_history
            self.message_input.text = ''
            self.chat_scroll.scroll_y = 0
            self.save_user_data()

    def _update_sidebar_rect(self, instance, value):
        self.sidebar_rect.size = instance.size
        self.sidebar_rect.pos = instance.pos

    def get_user_data_filename(self):
        return f"{self.username}_messages.enc"

    def load_user_data(self):
        import rsa, os
        filename = self.get_user_data_filename()
        key_dir = 'keys'
        private_key_path = os.path.join(key_dir, 'private.pem')
        self.friends_list = []
        self.chat_history = ""
        if os.path.exists(filename) and os.path.exists(private_key_path):
            try:
                with open(private_key_path, 'rb') as f:
                    privkey = rsa.PrivateKey.load_pkcs1(f.read())
                with open(filename, 'rb') as f:
                    encrypted = f.read()
                decrypted = rsa.decrypt(encrypted, privkey).decode('utf-8')
                lines = decrypted.split('\n')
                file_email = lines[0]
                file_password = lines[1]
                if file_email == self.email and file_password == self.password:
                    section = None
                    for line in lines[2:]:
                        if line == "[FRIENDS]":
                            section = "friends"
                        elif line == "[MESSAGES]":
                            section = "messages"
                        elif section == "friends":
                            self.friends_list.append(line)
                        elif section == "messages":
                            self.chat_history += line + "\n"
                else:
                    self.chat_history = "[color=ff0000]Email or password mismatch in user data file.[/color]"
            except Exception as e:
                self.chat_history = f"[color=ff0000]Failed to load user data: {e}[/color]"
        # If no data loaded, show welcome message
        if not self.chat_history.strip():
            self.chat_history = '[b][color=2288ff]Welcome to Secure Messenger![/color][/b]\nStart chatting securely.'

    def save_user_data(self):
        import rsa, os
        filename = self.get_user_data_filename()
        key_dir = 'keys'
        public_key_path = os.path.join(key_dir, 'public.pem')
        if os.path.exists(public_key_path):
            try:
                with open(public_key_path, 'rb') as f:
                    pubkey = rsa.PublicKey.load_pkcs1(f.read())
                data = f"{self.email}\n{self.password}\n[FRIENDS]\n" + "\n".join(self.friends_list) + "\n[MESSAGES]\n" + self.chat_history
                encrypted = rsa.encrypt(data.encode('utf-8'), pubkey)
                with open(filename, 'wb') as f:
                    f.write(encrypted)
            except Exception as e:
                print(f"Failed to save user data: {e}")

class TabTextInput(TextInput):
    def __init__(self, next_field=None, **kwargs):
        super().__init__(**kwargs)
        self.next_field = next_field
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == 'tab' and self.next_field:
            self.next_field.focus = True
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)

class LoginScreen(BoxLayout):
    def __init__(self, on_login, on_account_created, **kwargs):
        super().__init__(orientation='vertical', padding=32, spacing=16, **kwargs)
        self.on_login = on_login
        self.on_account_created = on_account_created
        self.username_input = TabTextInput(hint_text='Username', multiline=False, font_size=18, size_hint_y=None, height=44)
        self.email_input = TabTextInput(hint_text='Email', multiline=False, font_size=18, size_hint_y=None, height=44)
        self.password_input = TabTextInput(hint_text='Password', multiline=False, password=True, font_size=18, size_hint_y=None, height=44)
        # Link tab order
        self.username_input.next_field = self.email_input
        self.email_input.next_field = self.password_input
        self.password_input.next_field = self.username_input
        self.status_label = Label(text='', font_size=16, size_hint_y=None, height=32)
        btn_row = BoxLayout(orientation='horizontal', spacing=16, size_hint_y=None, height=44)
        login_btn = Button(text='Login', font_size=18, background_color=(0.2, 0.6, 1, 1))
        create_btn = Button(text='Create Account', font_size=18, background_color=(0.2, 0.6, 1, 1))
        login_btn.bind(on_release=self.login)
        create_btn.bind(on_release=self.create_account)
        btn_row.add_widget(login_btn)
        btn_row.add_widget(create_btn)
        self.add_widget(Label(text='Secure Messenger', font_size=22, size_hint_y=None, height=44))
        self.add_widget(self.username_input)
        self.add_widget(self.email_input)
        self.add_widget(self.password_input)
        self.add_widget(btn_row)
        self.add_widget(self.status_label)
    def login(self, instance):
        username = self.username_input.text.strip()
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        if username and email and password:
            try:
                resp = requests.post('http://localhost:5000/public_key', json={'username': username, 'email': email, 'password': password})
                if resp.status_code == 200:
                    self.on_login(email)
                else:
                    self.status_label.text = resp.json().get('error', 'Login failed.')
            except Exception as e:
                self.status_label.text = f'Error: {e}'
        else:
            self.status_label.text = 'Please enter username, email, and password.'
    def create_account(self, instance):
        username = self.username_input.text.strip()
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        if username and email and password:
            try:
                resp = requests.post('http://localhost:5000/store_user', json={'username': username, 'email': email, 'password': password})
                if resp.status_code == 200:
                    self.status_label.text = 'Account created! You can now log in.'
                    # Create encrypted user file immediately
                    SecureMessenger(username=username, email=email, password=password).save_user_data()
                    self.on_account_created()
                else:
                    self.status_label.text = resp.json().get('error', 'Error creating account.')
            except Exception as e:
                self.status_label.text = f'Error: {e}'
        else:
            self.status_label.text = 'Please fill all fields.'

class SecureMessengerApp(App):
    def build(self):
        self.login_screen = LoginScreen(self.on_login, self.show_account_created)
        return self.login_screen

    def show_account_created(self):
        pass

    def on_login(self, email):
        username = self.login_screen.username_input.text.strip()
        password = self.login_screen.password_input.text.strip()
        self.root.clear_widgets()
        self.root.add_widget(SecureMessenger(username=username, email=email, password=password))

    def on_request_close(self, *args):
        sys.exit(0)

if __name__ == '__main__':
    SecureMessengerApp().run()
