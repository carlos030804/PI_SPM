import flet as ft
from flet import icons
from typing import Optional, Callable, Union, List
import logging
from models import User, AthleteProfile, CoachProfile
from database import DatabaseManager
from utils import calculate_hr_zones, create_hr_zones_chart

logger = logging.getLogger(__name__)

# Paleta de colores
COLORS = {
    "primary": "#FF7F2A",
    "primary_light": "#FFA05A",
    "primary_dark": "#E56A1A",
    "secondary": "#F5F5F5",
    "background": "#FFFFFF",
    "text": "#333333",
    "error": "#D32F2F",
    "success": "#388E3C",
    "warning": "#FFA000",
    "info": "#1976D2"
}

def create_app_bar(
    title: str, 
    actions: Optional[List[ft.Control]] = None,
    bgcolor: str = COLORS["primary"]
) -> ft.AppBar:
    """Crea una barra de aplicación personalizada"""
    return ft.AppBar(
        title=ft.Text(
            title, 
            style=ft.TextStyle(
                color="white", 
                weight=ft.FontWeight.BOLD,
                size=20
            )
        ),
        bgcolor=bgcolor,
        actions=actions or [],
        center_title=False,
        elevation=4,
        toolbar_height=60
    )

def create_text_field(
    label: str,
    value: str = "",
    password: bool = False,
    width: int = 300,
    on_change: Optional[Callable] = None,
    keyboard_type: Optional[ft.KeyboardType] = None,
    multiline: bool = False,
    min_lines: Optional[int] = None,
    max_lines: Optional[int] = None
) -> ft.TextField:
    """Crea un campo de texto personalizado"""
    return ft.TextField(
        label=label,
        value=value,
        password=password,
        width=width,
        border_color=COLORS["primary"],
        focused_border_color=COLORS["primary_light"],
        color=COLORS["text"],
        cursor_color=COLORS["primary"],
        label_style=ft.TextStyle(color=COLORS["text"]),
        on_change=on_change,
        keyboard_type=keyboard_type,
        multiline=multiline,
        min_lines=min_lines,
        max_lines=max_lines
    )

def create_dropdown(
    label: str,
    options: List[ft.dropdown.Option],
    value: Optional[str] = None,
    width: int = 300,
    on_change: Optional[Callable] = None
) -> ft.Dropdown:
    """Crea un dropdown personalizado"""
    return ft.Dropdown(
        label=label,
        options=options,
        value=value,
        width=width,
        border_color=COLORS["primary"],
        focused_border_color=COLORS["primary_light"],
        color=COLORS["text"],
        label_style=ft.TextStyle(color=COLORS["text"]),
        on_change=on_change
    )

def create_button(
    text: str,
    on_click: Callable,
    icon: Optional[str] = None,
    bgcolor: str = COLORS["primary"],
    color: str = "white",
    width: Optional[int] = None,
    disabled: bool = False,
    expand: bool = False
) -> ft.ElevatedButton:
    """Crea un botón personalizado"""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        bgcolor=bgcolor,
        color=color,
        width=width,
        disabled=disabled,
        expand=expand,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=20,
            elevation=2,
            overlay_color=COLORS["primary_light"]
        )
    )

def create_card(
    content: ft.Control,
    title: Optional[str] = None,
    color: str = COLORS["secondary"],
    width: Optional[int] = None,
    height: Optional[int] = None,
    padding: int = 20,
    margin: int = 10
) -> ft.Card:
    """Crea una tarjeta personalizada"""
    header = []
    if title:
        header.append(
            ft.Text(
                title, 
                size=18, 
                weight=ft.FontWeight.BOLD, 
                color=COLORS["primary"]
            )
        )
        header.append(ft.Divider(height=1, color=COLORS["primary_light"]))
    
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=header + [content],
                spacing=15
            ),
            padding=padding,
            width=width,
            height=height
        ),
        color=color,
        elevation=5,
        margin=margin
    )

def show_alert(
    page: ft.Page,
    message: str,
    alert_type: str = "info",  # "info", "success", "warning", "error"
    duration: int = 3000
) -> None:
    """Muestra un mensaje de alerta"""
    color = COLORS.get(alert_type, COLORS["info"])
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color="white"),
        bgcolor=color,
        duration=duration
    )
    page.snack_bar.open = True
    page.update()

def show_loading(page: ft.Page, message: str = "Loading...") -> ft.Container:
    """Muestra un indicador de carga"""
    loading = ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=50, height=50, color=COLORS["primary"]),
                ft.Text(message, color=COLORS["text"])
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        alignment=ft.alignment.center,
        bgcolor=ft.colors.with_opacity(0.7, "#FFFFFF"),
        border_radius=10,
        width=page.width,
        height=page.height
    )
    page.overlay.append(loading)
    page.update()
    return loading

def hide_loading(page: ft.Page, loading_control: ft.Container) -> None:
    """Oculta el indicador de carga"""
    page.overlay.remove(loading_control)
    page.update()


def show_register(page: ft.Page, db: DatabaseManager):
    """Muestra la pantalla de registro"""
    # Campos del formulario principal
    email_field = create_text_field("Email")
    password_field = create_text_field("Password", password=True)
    confirm_password_field = create_text_field("Confirm Password", password=True)
    user_type_dropdown = create_dropdown(
        "User Type",
        options=[
            ft.dropdown.Option("atleta", "Athlete"),
            ft.dropdown.Option("entrenador", "Coach")
        ]
    )
    
    # Campos adicionales dinámicos
    additional_fields = ft.Column(spacing=10)
    
    # Mensajes de estado
    error_text = ft.Text("", color=COLORS["error"])
    success_text = ft.Text("", color=COLORS["success"])

    def update_additional_fields(e):
        """Actualiza los campos adicionales según el tipo de usuario"""
        additional_fields.controls.clear()
        
        if user_type_dropdown.value == "atleta":
            additional_fields.controls.extend([
                create_text_field("Full Name"),
                create_text_field("Birth Date (YYYY-MM-DD)", keyboard_type=ft.KeyboardType.DATETIME),
                create_text_field("Height (cm)", keyboard_type=ft.KeyboardType.NUMBER),
                create_text_field("Weight (kg)", keyboard_type=ft.KeyboardType.NUMBER),
                create_text_field("Sport"),
                create_text_field("Resting Heart Rate (bpm)", keyboard_type=ft.KeyboardType.NUMBER),
                create_text_field("Coach ID (optional)", keyboard_type=ft.KeyboardType.NUMBER)
            ])
        elif user_type_dropdown.value == "entrenador":
            additional_fields.controls.extend([
                create_text_field("Full Name"),
                create_text_field("Birth Date (YYYY-MM-DD)", keyboard_type=ft.KeyboardType.DATETIME),
                create_text_field("Specialty"),
                create_text_field(
                    "Experience", 
                    multiline=True, 
                    min_lines=3, 
                    max_lines=5
                )
            ])
        
        page.update()

    def on_register(e):
        """Maneja el evento de registro"""
        # Validaciones básicas
        email = email_field.value.strip()
        password = password_field.value
        confirm_password = confirm_password_field.value
        user_type = user_type_dropdown.value
        
        if not email or not password or not confirm_password or not user_type:
            error_text.value = "All fields are required"
            page.update()
            return
        
        if password != confirm_password:
            error_text.value = "Passwords don't match"
            page.update()
            return
        
        if len(password) < 8:
            error_text.value = "Password must be at least 8 characters"
            page.update()
            return
        
        # Validar campos adicionales según el tipo de usuario
        if user_type == "atleta" and len(additional_fields.controls) == 7:
            athlete_fields = additional_fields.controls
            if not all(field.value for field in athlete_fields[:6]):  # Coach ID es opcional
                error_text.value = "All athlete fields are required except Coach ID"
                page.update()
                return
        elif user_type == "entrenador" and len(additional_fields.controls) == 4:
            if not all(field.value for field in additional_fields.controls):
                error_text.value = "All coach fields are required"
                page.update()
                return
        
        loading = show_loading(page, "Creating account...")
        conn = None  # Variable para mantener la conexión
        
        try:
            conn = DatabaseManager.start_transaction()  # Obtiene conexión con transacción iniciada

            # # 1. Insertar usuario (sin commit automático)
            # db.execute_query(user_query, params, commit=False)

            # Registrar usuario principal
            hashed_pw = DatabaseManager.hash_password(password)
            query = """
            INSERT INTO usuarios (email, contrasena_hash, tipo, activo) 
            VALUES (%s, %s, %s, 1)
            """
            db.execute_query(query, (email, hashed_pw, user_type), conn=conn)

            # user_id = db.execute_query("SELECT LAST_INSERT_ID() AS id", fetch_one=True)["id"]
            result = db.execute_query("SELECT LAST_INSERT_ID() AS id", fetch_one=True, conn=conn)
            if not result:
                raise Exception("No se pudo obtener el ID del nuevo usuario")
            user_id = result["id"]
            
            # Registrar perfil específico
            if user_type == "atleta":
                # Procesar campos de atleta
                full_name = additional_fields.controls[0].value
                birth_date = additional_fields.controls[1].value
                height = float(additional_fields.controls[2].value)
                weight = float(additional_fields.controls[3].value)
                sport = additional_fields.controls[4].value
                resting_hr = int(additional_fields.controls[5].value)
                coach_id = additional_fields.controls[6].value or None
                
                # Calcular frecuencia cardiaca máxima (220 - edad)
                from datetime import datetime
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
                today = datetime.now().date()
                age = today.year - birth_date_obj.year - (
                    (today.month, today.day) < (birth_date_obj.month, birth_date_obj.day)
                )
                max_hr = 220 - age
                
                athlete_query  = """
                INSERT INTO perfiles_atletas 
                (id_usuario, nombre_completo, fecha_nacimiento, altura, peso, deporte, 
                frecuencia_cardiaca_maxima, frecuencia_cardiaca_minima, id_entrenador) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                # db.execute_query(
                #     athlete_query,
                #     (user_id, full_name, birth_date, height, weight, sport, 
                #      max_hr, resting_hr, coach_id),
                #     commit=False
                # )
                DatabaseManager.execute_query(
                    athlete_query,
                    (user_id, full_name, birth_date, height, weight, sport, max_hr, resting_hr, coach_id),
                    conn=conn  # Usamos la conexión de transacción
                )       

            elif user_type == "entrenador":
                # Procesar campos de entrenador
                full_name = additional_fields.controls[0].value
                birth_date = additional_fields.controls[1].value
                specialty = additional_fields.controls[2].value
                experience = additional_fields.controls[3].value
                
                coach_query  = """
                INSERT INTO perfiles_entrenadores 
                (id_usuario, nombre_completo, fecha_nacimiento, especialidad, experiencia) 
                VALUES (%s, %s, %s, %s, %s)
                """
                # db.execute_query(
                #     coach_query ,
                #     (user_id, full_name, birth_date, specialty, experience),
                #     commit=False
                # )

                DatabaseManager.execute_query(
                    coach_query,
                    (user_id, full_name, birth_date, specialty, experience),
                    conn=conn  # Usamos la conexión de transacción
                )
            
            # Éxito en el registro
            DatabaseManager.commit_transaction(conn)  # Commit de la transacción
            success_text.value = "Registration successful! You can now login."
            error_text.value = ""
            page.update()
            
            # Limpiar formulario después de 3 segundos
            def clear_form():
                email_field.value = ""
                password_field.value = ""
                confirm_password_field.value = ""
                user_type_dropdown.value = None
                additional_fields.controls.clear()
                success_text.value = ""
                page.update()
            
            page.run_task(lambda: page.run_once(clear_form, delay=3))
        except Exception as e:  # <- ¡Esto es lo que faltaba!
            logger.error(f"Error during registration: {e}")
            error_text.value = "An error occurred during registration"
            page.update()
        finally:
            hide_loading(page, loading)
        pass  # Mantén todo el contenido de esta función igual


        # Configurar el event handler para el dropdown
    user_type_dropdown.on_change = update_additional_fields

    # Construir la interfaz
    page.clean()
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(
                        src="assets/logo.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    ft.Text(
                        "SportPro", 
                        size=32, 
                        weight=ft.FontWeight.BOLD, 
                        color=COLORS["primary"]
                    ),
                    ft.Text(
                        "Create Account", 
                        size=16, 
                        color=COLORS["text"]
                    ),
                    create_card(
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Register", 
                                    size=20, 
                                    weight=ft.FontWeight.BOLD, 
                                    color=COLORS["text"]
                                ),
                                email_field,
                                password_field,
                                confirm_password_field,
                                user_type_dropdown,
                                additional_fields,
                                create_button("Register", on_register),
                                error_text,
                                success_text,
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            "Already have an account?", 
                                            color=COLORS["text"]
                                        ),
                                        ft.TextButton(
                                            "Login", 
                                            on_click=lambda e: show_login(page, db),
                                            style=ft.ButtonStyle(
                                                color=COLORS["primary"]
                                            )
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER
                                )
                            ],
                            spacing=15,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            padding=40,
            expand=True
        )
    )
    page.update()
 


def show_login(page: ft.Page, db: DatabaseManager):
    """Muestra la pantalla de login"""
    # Campos del formulario
    email_field = create_text_field("Email")
    password_field = create_text_field("Password", password=True)
    error_text = ft.Text("", color=COLORS["error"])
    
    def on_login(e):
        """Maneja el evento de login"""
        email = email_field.value.strip()
        password = password_field.value
        
        if not email or not password:
            error_text.value = "Email and password are required"
            page.update()
            return
        
        loading = show_loading(page, "Signing in...")
        
        try:
            user = User.authenticate(email, password)
            
            if user:
                user.update_last_login()
                page.session.set("user_id", user.id)
                page.session.set("user_type", user.type)
                
                # Redirigir según el tipo de usuario
                if user.type == "administrador":
                    from views.admin import show_admin_dashboard
                    show_admin_dashboard(page, db)
                elif user.type == "entrenador":
                    from views.coach import show_coach_dashboard
                    show_coach_dashboard(page, db)
                else:
                    from views.athlete import show_athlete_dashboard
                    show_athlete_dashboard(page, db)
            else:
                error_text.value = "Invalid email or password"
                page.update()
        except Exception as e:
            logger.error(f"Login error: {e}")
            error_text.value = "An error occurred during login"
            page.update()
        finally:
            hide_loading(page, loading)
    
    def on_navigate_to_register(e):
        """Navega a la pantalla de registro"""
        show_register(page, db)
    
    # Construir la interfaz
    page.clean()
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Image(
                        src="assets/logo.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN
                    ),
                    ft.Text(
                        "SportPro", 
                        size=32, 
                        weight=ft.FontWeight.BOLD, 
                        color=COLORS["primary"]
                    ),
                    ft.Text(
                        "Sports Management System", 
                        size=16, 
                        color=COLORS["text"]
                    ),
                    create_card(
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Login", 
                                    size=20, 
                                    weight=ft.FontWeight.BOLD, 
                                    color=COLORS["text"]
                                ),
                                email_field,
                                password_field,
                                create_button("Login", on_login),
                                error_text,
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            "Don't have an account?", 
                                            color=COLORS["text"]
                                        ),
                                        ft.TextButton(
                                            "Register", 
                                            on_click=on_navigate_to_register, 
                                            style=ft.ButtonStyle(
                                                color=COLORS["primary"]
                                            )
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER
                                )
                            ],
                            spacing=15,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            padding=40,
            expand=True
        )
    )
    
    