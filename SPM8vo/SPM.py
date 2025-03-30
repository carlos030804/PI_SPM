import flet as ft
from flet import icons as icons
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime, date
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64

# Color palette
COLOR_PRIMARIO = "#FF7F2A"  # Orange
COLOR_SECUNDARIO = "#F5F5F5"  # Light gray
COLOR_FONDO = "#FFFFFF"       # White
COLOR_TEXTO = "#333333"       # Dark gray
COLOR_ACENTO = "#FFA05A"      # Light orange
COLORES_ZONAS = ["#FF6B6B", "#FFA500", "#FFD700", "#90EE90", "#4682B4"]

# Database configuration
def init_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="aplicacion_deportiva"
        )
        return conn
    except Error as e:
        print("Error connecting to MySQL:", e)
        raise

# Initialize connection
conn = init_db()

# Utility functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))

def calculate_age(birth_date):
    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_max_hr(age):
    """Calculate maximum heart rate using traditional formula (220 - age)"""
    return 220 - age

def calculate_hr_zones(max_hr, resting_hr):
    """Calculate training zones using Karvonen formula"""
    hr_range = max_hr - resting_hr
    zones = {
        "Zone 1 (Recovery)": int(resting_hr + 0.5 * hr_range),
        "Zone 2 (Light Aerobic)": int(resting_hr + 0.6 * hr_range),
        "Zone 3 (Aerobic)": int(resting_hr + 0.7 * hr_range),
        "Zone 4 (Anaerobic Threshold)": int(resting_hr + 0.8 * hr_range),
        "Zone 5 (Maximum Effort)": int(resting_hr + 0.9 * hr_range),
        "Max HR": max_hr
    }
    return zones

def create_hr_zones_chart(zones, resting_hr):
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Prepare chart data
    zone_names = list(zones.keys())
    zone_values = list(zones.values())
    
    # Create line chart with points
    ax.plot(zone_names, zone_values, marker='o', linestyle='-', color=COLOR_PRIMARIO, markersize=8)
    
    # Resting HR line
    ax.axhline(y=resting_hr, color='gray', linestyle='--', label='Resting HR')
    
    # Color zone areas
    for i in range(len(zone_values)-1):
        ax.axhspan(zone_values[i], zone_values[i+1], facecolor=COLORES_ZONAS[i], alpha=0.3)
    
    # Chart settings
    ax.set_title("Heart Rate Training Zones", pad=20)
    ax.set_ylabel("Beats per minute (bpm)")
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    
    # Save to buffer and encode as base64
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# Flet Application
def main(page: ft.Page):
    # Page configuration
    page.title = "SportPro - Sports Management"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = COLOR_FONDO
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.fonts = {
        "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
    }
    page.theme = ft.Theme(font_family="Roboto")

    # UI Components
    def create_text_field(label, password=False, width=300):
        return ft.TextField(
            label=label,
            password=password,
            width=width,
            border_color=COLOR_PRIMARIO,
            focused_border_color=COLOR_ACENTO,
            color=COLOR_TEXTO,
            cursor_color=COLOR_PRIMARIO,
            label_style=ft.TextStyle(color=COLOR_TEXTO)
        )

    def create_button(text, on_click, bgcolor=COLOR_PRIMARIO, color="white"):
        return ft.ElevatedButton(
            text=text,
            on_click=on_click,
            bgcolor=bgcolor,
            color=color,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=15,
                elevation=2
            )
        )

    def create_card(content, color=COLOR_SECUNDARIO):
        return ft.Card(
            content=ft.Container(
                content=content,
                padding=20,
                border_radius=10
            ),
            color=color,
            elevation=5,
            margin=10
        )

    # Authentication components
    login_email = create_text_field("Email")
    login_password = create_text_field("Password", password=True)
    login_error = ft.Text("", color="red")

    register_email = create_text_field("Email")
    register_password = create_text_field("Password", password=True)
    register_confirm_password = create_text_field("Confirm Password", password=True)
    register_type = ft.Dropdown(
        label="User Type",
        options=[
            ft.dropdown.Option("atleta", "Athlete"),
            ft.dropdown.Option("entrenador", "Coach")
        ],
        width=300,
        border_color=COLOR_PRIMARIO,
        focused_border_color=COLOR_ACENTO,
        color=COLOR_TEXTO,
        label_style=ft.TextStyle(color=COLOR_TEXTO)
    )
    register_error = ft.Text("", color="red")
    register_success = ft.Text("", color="green")

    # Additional registration fields
    additional_fields = ft.Column(scroll=ft.ScrollMode.AUTO)

    def update_register_fields(e):
        additional_fields.controls.clear()
        
        if register_type.value == "atleta":
            additional_fields.controls.extend([
                create_text_field("Full Name"),
                create_text_field("Birth Date (YYYY-MM-DD)"),
                create_text_field("Height (cm)"),
                create_text_field("Weight (kg)"),
                create_text_field("Sport"),
                create_text_field("Resting Heart Rate (bpm)"),
                create_text_field("Coach ID (optional)")
            ])
        elif register_type.value == "entrenador":
            additional_fields.controls.extend([
                create_text_field("Full Name"),
                create_text_field("Birth Date (YYYY-MM-DD)"),
                create_text_field("Specialty"),
                ft.TextField(
                    label="Experience",
                    multiline=True,
                    min_lines=3,
                    max_lines=5,
                    width=300,
                    border_color=COLOR_PRIMARIO,
                    focused_border_color=COLOR_ACENTO
                )
            ])
        
        page.update()

    register_type.on_change = update_register_fields

    # Authentication functions
    def login(e):
        email = login_email.value
        password = login_password.value
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM usuarios WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        
        if user and verify_password(user['contrasena_hash'], password):
            page.session.set("user_id", user['id_usuario'])
            page.session.set("user_type", user['tipo'])
            
            # Update last login
            cursor.execute(
                "UPDATE usuarios SET ultimo_login = %s WHERE id_usuario = %s",
                (datetime.now(), user['id_usuario'])
            )
            conn.commit()
            
            # Redirect based on user type
            if user['tipo'] == "administrador":
                show_admin_dashboard()
            elif user['tipo'] == "entrenador":
                show_coach_dashboard()
            else:
                show_athlete_dashboard()
        else:
            login_error.value = "Invalid credentials"
            page.update()

    def register(e):
        # Basic validations
        if register_password.value != register_confirm_password.value:
            register_error.value = "Passwords don't match"
            page.update()
            return
        
        if register_type.value is None:
            register_error.value = "Select a user type"
            page.update()
            return
        
        try:
            cursor = conn.cursor()
            
            # Register main user
            hashed_pw = hash_password(register_password.value)
            cursor.execute(
                "INSERT INTO usuarios (email, contrasena_hash, tipo) VALUES (%s, %s, %s)",
                (register_email.value, hashed_pw, register_type.value)
            )
            user_id = cursor.lastrowid
            
            # Register specific profile
            if register_type.value == "atleta":
                # Calculate age and max HR
                birth_date = additional_fields.controls[1].value
                age = calculate_age(birth_date)
                max_hr = calculate_max_hr(age)
                resting_hr = int(additional_fields.controls[5].value)
                
                cursor.execute(
                    """INSERT INTO perfiles_atletas 
                    (id_usuario, nombre_completo, fecha_nacimiento, altura, peso, deporte, 
                    frecuencia_cardiaca_maxima, frecuencia_cardiaca_minima, id_entrenador) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        user_id,
                        additional_fields.controls[0].value,
                        additional_fields.controls[1].value,
                        float(additional_fields.controls[2].value),
                        float(additional_fields.controls[3].value),
                        additional_fields.controls[4].value,
                        max_hr,  # Automatically calculated
                        resting_hr,  # Provided by user
                        int(additional_fields.controls[6].value) if additional_fields.controls[6].value else None
                    )
                )
            elif register_type.value == "entrenador":
                cursor.execute(
                    """INSERT INTO perfiles_entrenadores 
                    (id_usuario, nombre_completo, fecha_nacimiento, especialidad, experiencia) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (
                        user_id,
                        additional_fields.controls[0].value,
                        additional_fields.controls[1].value,
                        additional_fields.controls[2].value,
                        additional_fields.controls[3].value
                    )
                )
            
            conn.commit()
            register_success.value = "Registration successful! You can now login."
            register_error.value = ""
            page.update()
            
        except Error as err:
            register_error.value = f"Registration error: {err}"
            register_success.value = ""
            conn.rollback()
            page.update()

    # Views
    def show_login(e=None):
        page.clean()
        page.add(
            ft.Container(
                ft.Column([
                    ft.Image(
                        src="https://via.placeholder.com/150",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    ft.Text("SportPro", size=32, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO),
                    ft.Text("Sports Management System", size=16, color=COLOR_TEXTO),
                    create_card(
                        ft.Column([
                            ft.Text("Login", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                            login_email,
                            login_password,
                            create_button("Login", login),
                            login_error,
                            ft.Row([
                                ft.Text("Don't have an account?", color=COLOR_TEXTO),
                                ft.TextButton("Register", on_click=show_register, style=ft.ButtonStyle(color=COLOR_PRIMARIO))
                            ], alignment=ft.MainAxisAlignment.CENTER)
                        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                padding=40,
                expand=True
            )
        )

    def show_register(e=None):
        page.clean()
        page.add(
            ft.Container(
                ft.Column([
                    ft.Image(
                        src="https://via.placeholder.com/150",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    ft.Text("Register", size=32, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO),
                    create_card(
                        ft.Column([
                            register_email,
                            register_password,
                            register_confirm_password,
                            register_type,
                            additional_fields,
                            create_button("Register", register),
                            register_error,
                            register_success,
                            ft.Row([
                                ft.TextButton("Back to login", on_click=show_login, style=ft.ButtonStyle(color=COLOR_PRIMARIO))
                            ], alignment=ft.MainAxisAlignment.CENTER)
                        ], spacing=15, scroll=ft.ScrollMode.AUTO),
                        color=COLOR_FONDO
                    )
                ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                padding=40,
                expand=True
            )
        )

    def show_admin_dashboard():
        page.clean()
        
        # Get statistics
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        total_users = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM perfiles_atletas")
        total_athletes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM perfiles_entrenadores")
        total_coaches = cursor.fetchone()['total']
        
        # Create stats cards
        stats_cards = ft.Row(
            controls=[
                create_card(
                    ft.Column([
                        ft.Text("Users", size=16, color=COLOR_TEXTO),
                        ft.Text(str(total_users), size=24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    COLOR_SECUNDARIO
                ),
                create_card(
                    ft.Column([
                        ft.Text("Athletes", size=16, color=COLOR_TEXTO),
                        ft.Text(str(total_athletes), size=24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    COLOR_SECUNDARIO
                ),
                create_card(
                    ft.Column([
                        ft.Text("Coaches", size=16, color=COLOR_TEXTO),
                        ft.Text(str(total_coaches), size=24, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    COLOR_SECUNDARIO
                )
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
        )
        
        # Build page
        page.add(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("SportPro - Admin Panel", size=20, weight=ft.FontWeight.BOLD, color="white"),
                                ft.IconButton(
                                    icon=icons.LOGOUT_OUTLINED,
                                    icon_color="white",
                                    on_click=logout,
                                    tooltip="Logout"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=15,
                        bgcolor=COLOR_PRIMARIO,
                        border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Statistics", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                                stats_cards
                            ],
                            spacing=20,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True
                        ),
                        padding=20,
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            )
        )

    def show_coach_dashboard():
        page.clean()
        coach_id = page.session.get("user_id")
        
        # Get coach info
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT p.* FROM perfiles_entrenadores p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            WHERE u.id_usuario = %s""",
            (coach_id,)
        )
        coach = cursor.fetchone()
        
        # Get assigned athletes
        cursor.execute(
            """SELECT a.* FROM perfiles_atletas a
            WHERE a.id_entrenador = %s""",
            (coach['id_entrenador'],)
        )
        athletes = cursor.fetchall()
        
        # Get created workouts
        cursor.execute(
            "SELECT * FROM entrenamientos WHERE id_entrenador = %s",
            (coach['id_entrenador'],)
        )
        workouts = cursor.fetchall()
        
        # Build UI
        athlete_list = ft.ListView(
            controls=[
                ft.ListTile(
                    title=ft.Text(athlete['nombre_completo'], color=COLOR_TEXTO),
                    subtitle=ft.Text(f"Sport: {athlete['deporte']}", color=COLOR_TEXTO),
                    leading=ft.Icon(icons.PERSON_OUTLINED, color=COLOR_PRIMARIO),
                    on_click=lambda e, a=athlete: show_athlete_detail(a)
                )
                for athlete in athletes
            ],
            expand=True,
            spacing=5
        )
        
        workout_list = ft.ListView(
            controls=[
                ft.ListTile(
                    title=ft.Text(workout['titulo'], color=COLOR_TEXTO),
                    subtitle=ft.Text(f"Duration: {workout['duracion_estimada']} min", color=COLOR_TEXTO),
                    leading=ft.Icon(icons.FITNESS_CENTER_OUTLINED, color=COLOR_PRIMARIO),
                    trailing=ft.PopupMenuButton(
                        icon=icons.MORE_VERT_OUTLINED,
                        items=[
                            ft.PopupMenuItem(text="Edit"),
                            ft.PopupMenuItem(text="Delete"),
                        ]
                    )
                )
                for workout in workouts
            ],
            expand=True,
            spacing=5
        )
        
        page.add(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(f"Welcome, {coach['nombre_completo']}", size=20, weight=ft.FontWeight.BOLD, color="white"),
                                ft.IconButton(
                                    icon=icons.LOGOUT_OUTLINED,
                                    icon_color="white",
                                    on_click=logout,
                                    tooltip="Logout"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=15,
                        bgcolor=COLOR_PRIMARIO,
                        border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
                    ),
                    ft.Tabs(
                        tabs=[
                            ft.Tab(
                                text="My Athletes",
                                icon=icons.GROUP_OUTLINED,
                                content=ft.Container(
                                    content=athlete_list,
                                    padding=10,
                                    expand=True
                                )
                            ),
                            ft.Tab(
                                text="My Workouts",
                                icon=icons.FITNESS_CENTER_OUTLINED,
                                content=ft.Container(
                                    content=workout_list,
                                    padding=10,
                                    expand=True
                                )
                            ),
                            ft.Tab(
                                text="New Workout",
                                icon=icons.ADD_OUTLINED,
                                content=ft.Container(
                                    content=ft.Column(
                                        controls=[
                                            ft.Text("Create new workout", size=18, color=COLOR_TEXTO),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                    ),
                                    expand=True
                                )
                            )
                        ],
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            )
        )

    def show_athlete_dashboard():
        page.clean()
        athlete_id = page.session.get("user_id")
        
        # Get athlete info
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT a.*, p.nombre_completo as nombre_entrenador 
            FROM perfiles_atletas a
            LEFT JOIN perfiles_entrenadores p ON a.id_entrenador = p.id_entrenador
            WHERE a.id_usuario = %s""",
            (athlete_id,)
        )
        athlete = cursor.fetchone()
        
        # Get assigned workouts
        cursor.execute(
            """SELECT e.*, a.estado 
            FROM asignaciones_atletas a
            JOIN entrenamientos e ON a.id_entrenamiento = e.id_entrenamiento
            WHERE a.id_atleta = %s""",
            (athlete['id_atleta'],)
        )
        workouts = cursor.fetchall()
        
        # Calculate age
        birth_date = athlete['fecha_nacimiento']
        age = calculate_age(birth_date)
        
        # Get heart rate data
        max_hr = athlete['frecuencia_cardiaca_maxima']
        resting_hr = athlete['frecuencia_cardiaca_minima']
        
        # Calculate HR zones
        zones = calculate_hr_zones(max_hr, resting_hr)
        
        # Create zones chart
        chart_base64 = create_hr_zones_chart(zones, resting_hr)
        chart_img = ft.Image(src_base64=chart_base64, width=600, height=300)
        
        # Build UI
        profile_card = create_card(
            ft.Column([
                ft.Text(athlete['nombre_completo'], size=20, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO),
                ft.Divider(),
                ft.Row([ft.Text("Age:", width=150), ft.Text(f"{age} years")]),
                ft.Row([ft.Text("Max HR (220 - age):", width=150), ft.Text(f"{max_hr} bpm")]),
                ft.Row([ft.Text("Resting HR:", width=150), ft.Text(f"{resting_hr} bpm")]),
                ft.Row([ft.Text("Sport:", width=150), ft.Text(athlete['deporte'])]),
                ft.Row([ft.Text("Coach:", width=150), ft.Text(athlete['nombre_entrenador'] or 'Not assigned')]),
                ft.Row([ft.Text("Height:", width=150), ft.Text(f"{athlete['altura']} cm")]),
                ft.Row([ft.Text("Weight:", width=150), ft.Text(f"{athlete['peso']} kg")])
            ], spacing=10),
            COLOR_SECUNDARIO
        )
        
        zones_card = create_card(
            ft.Column([
                ft.Text("Heart Rate Training Zones", size=18, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARIO),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Zone", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Range (bpm)", weight=ft.FontWeight.BOLD)),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(zone)),
                                ft.DataCell(ft.Text(f"{zones[zone]}" if i == len(zones)-1 else f"{zones[zone]} - {list(zones.values())[i+1]}"))
                            ]
                        )
                        for i, zone in enumerate(zones)
                    ],
                    border=ft.border.all(1, COLOR_PRIMARIO),
                ),
                ft.Container(
                    chart_img,
                    alignment=ft.alignment.center,
                    padding=10
                )
            ], spacing=15)
        )
        
        workout_list = ft.ListView(
            controls=[
                ft.ListTile(
                    title=ft.Text(workout['titulo'], color=COLOR_TEXTO),
                    subtitle=ft.Text(f"Status: {workout['estado'].replace('_', ' ').title()}", color=COLOR_TEXTO),
                    leading=ft.Icon(icons.FITNESS_CENTER_OUTLINED, color=COLOR_PRIMARIO),
                    trailing=ft.Text(f"{workout['duracion_estimada']} min", color=COLOR_TEXTO),
                    on_click=lambda e, w=workout: show_workout_detail(w)
                )
                for workout in workouts
            ],
            expand=True,
            spacing=5
        )
        
        page.add(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("My Profile", size=20, weight=ft.FontWeight.BOLD, color="white"),
                                ft.IconButton(
                                    icon=icons.LOGOUT_OUTLINED,
                                    icon_color="white",
                                    on_click=logout,
                                    tooltip="Logout"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=15,
                        bgcolor=COLOR_PRIMARIO,
                        border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                profile_card,
                                zones_card,
                                ft.Text("My Workouts", size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                                workout_list
                            ],
                            spacing=20,
                            scroll=ft.ScrollMode.AUTO,
                            expand=True
                        ),
                        padding=20,
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            )
        )

    def show_athlete_detail(athlete):
        # To implement: Athlete detail view
        pass

    def show_workout_detail(workout):
        # To implement: Workout detail view
        pass

    def logout(e):
        page.session.clear()
        show_login()

    # Show login initially
    show_login()

# Run the application
ft.app(target=main, view=ft.AppView.WEB_BROWSER)