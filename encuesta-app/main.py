from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.properties import BooleanProperty, StringProperty, ObjectProperty # Añade StringProperty aquí

from datetime import datetime
import json, os
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# For button-hover feature
from hoverable import HoverBehavior

Builder.load_file("design.kv")

USERS_FILE = "users.json"

def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as file:
            json.dump({}, file, indent=4)

class DayToggleButton(ToggleButton):
    """Botón personalizado para selección de días"""
    day_name = StringProperty('')  # Nombre del día asociado
    # Eliminamos cualquier referencia a grupos aquí

class LoginScreen(Screen):
    def sign_up(self):
        self.manager.current = "sign_up_screen"
    
    def login(self, uname, pwd):
        ensure_users_file()
        try:
            with open(USERS_FILE) as file:
                users = json.load(file)
                if uname in users and users[uname]['password'] == pwd:
                    self.manager.get_screen("survey_screen").current_user = uname
                    self.manager.current = "survey_screen"
                else:
                    self.ids.login_wrong.text = 'Usuario o contraseña incorrectos'
        except json.JSONDecodeError:
            self.ids.login_wrong.text = 'Error leyendo los datos'

class SurveyScreen(Screen):
    current_user = ""

    def on_pre_enter(self):
        """Cargar selección previa al entrar"""
        if self.current_user:
            with open(USERS_FILE, 'r') as file:
                users = json.load(file)
                if self.current_user in users and 'availability' in users[self.current_user]:
                    days = users[self.current_user]['availability']
                    for day, selected in days.items():
                        if day in self.ids:
                            self.ids[day].state = 'down' if selected else 'normal'

    def save_availability(self):
        """Guardar la selección de días"""
        availability = {
            'monday': self.ids.monday.state == 'down',
            'tuesday': self.ids.tuesday.state == 'down',
            'wednesday': self.ids.wednesday.state == 'down',
            'thursday': self.ids.thursday.state == 'down',
            'friday': self.ids.friday.state == 'down'
        }
        
        with open(USERS_FILE, 'r') as file:
            users = json.load(file)
        
        if self.current_user in users:
            users[self.current_user]['availability'] = availability
        
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file, indent=4)
        
        self.generate_availability_chart()
        self.manager.current = "results_screen"
    
    def generate_availability_chart(self):
        with open(USERS_FILE, 'r') as file:
            users = json.load(file)
        
        day_counts = {'Lunes':0, 'Martes':0, 'Miércoles':0, 'Jueves':0, 'Viernes':0}
        total_users = 0
        
        for user_data in users.values():
            if 'availability' in user_data:
                total_users += 1
                avail = user_data['availability']
                if avail['monday']: day_counts['Lunes'] += 1
                if avail['tuesday']: day_counts['Martes'] += 1
                if avail['wednesday']: day_counts['Miércoles'] += 1
                if avail['thursday']: day_counts['Jueves'] += 1
                if avail['friday']: day_counts['Viernes'] += 1
        
        plt.figure(figsize=(8,5))
        bars = plt.bar(day_counts.keys(), day_counts.values(), color='skyblue')
        
        for bar in bars:
            height = bar.get_height()
            percentage = (height/total_users)*100 if total_users > 0 else 0
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(percentage)}%', ha='center', va='bottom')
        
        plt.title('Disponibilidad de Usuarios por Día')
        plt.ylabel('Número de Usuarios')
        plt.ylim(0, total_users+1 if total_users > 0 else 1)
        
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close()
        
        results_screen = self.manager.get_screen("results_screen")
        results_screen.ids.chart_image.source = f"data:image/png;base64,{image_base64}"
        
        summary = "\n".join([f"{day}: {count} usuarios ({int((count/total_users)*100)}%)" 
                           for day, count in day_counts.items()])
        results_screen.ids.summary_label.text = f"Resumen de disponibilidad:\n{summary}"

class ResultsScreen(Screen):
    def back_to_survey(self):
        self.manager.current = "survey_screen"
    
    def logout(self):
        self.manager.transition.direction = 'right'
        self.manager.current = "login_screen"

class SignupScreen(Screen):
    def add_user(self, uname, pwd):
        ensure_users_file()
        with open(USERS_FILE, 'r') as file:
            users = json.load(file)
        
        users[uname] = {
            'username': uname,
            'password': pwd,
            'created': datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        }
        
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file, indent=4)
        
        self.manager.current = "sign_up_success"

class SignupSuccessScreen(Screen):
    def login_page(self):
        self.manager.transition.direction = 'right'
        self.manager.current = "login_screen"

class ImageButton(ButtonBehavior, HoverBehavior, Image):
    pass

class RootWidget(ScreenManager):
    pass

class MainApp(App):
    def build(self):
        return RootWidget()

if __name__ == "__main__":
    MainApp().run()