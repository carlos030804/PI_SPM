import flet as ft
from flet import icons
from typing import Optional, Callable, Union, List, Dict, Any
import logging
import requests
import re
import threading
import time
from datetime import datetime
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

def fetch_wger_exercises(limit: int = 5) -> Dict[str, Any]:
    """Obtiene ejercicios de la API de Wger"""
    try:
        response = requests.get(
            "https://wger.de/api/v2/exerciseinfo/",
            params={"language": 2, "limit": limit},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener ejercicios: {str(e)}")
        return {"error": str(e)}


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
        # Validaciones básicasa
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
        conn = None
        
        try:
            conn = db.get_connection()  # Obtener conexión de la base de datos
            db.start_transaction(conn)  # Iniciar transacción

            # Registrar usuario principal
            hashed_pw = DatabaseManager.hash_password(password)
            user_query = """
            INSERT INTO usuarios (email, contrasena_hash, tipo, activo) 
            VALUES (%s, %s, %s, 1)
            """
            db.execute_query(user_query, (email, hashed_pw, user_type), conn=conn)

            # Obtener ID del usuario recién creado
            result = db.execute_query("SELECT LAST_INSERT_ID() AS id", fetch_one=True, conn=conn)
            if not result:
                raise Exception("No se pudo obtener el ID del nuevo usuario")
            user_id = result["id"]
            
            # Registrar perfil específico
            if user_type == "atleta":
                full_name = additional_fields.controls[0].value
                birth_date = additional_fields.controls[1].value
                height = float(additional_fields.controls[2].value)
                weight = float(additional_fields.controls[3].value)
                sport = additional_fields.controls[4].value
                resting_hr = int(additional_fields.controls[5].value)
                coach_id = additional_fields.controls[6].value or None
                
                # Calcular frecuencia cardiaca máxima
                from datetime import datetime
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
                today = datetime.now().date()
                age = today.year - birth_date_obj.year - (
                    (today.month, today.day) < (birth_date_obj.month, birth_date_obj.day)
                )
                max_hr = 220 - age
                
                athlete_query = """
                INSERT INTO perfiles_atletas 
                (id_usuario, nombre_completo, fecha_nacimiento, altura, peso, deporte, 
                frecuencia_cardiaca_maxima, frecuencia_cardiaca_minima, id_entrenador) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                db.execute_query(
                    athlete_query,
                    (user_id, full_name, birth_date, height, weight, sport, max_hr, resting_hr, coach_id),
                    conn=conn
                )

            elif user_type == "entrenador":
                full_name = additional_fields.controls[0].value
                birth_date = additional_fields.controls[1].value
                specialty = additional_fields.controls[2].value
                experience = additional_fields.controls[3].value
                
                coach_query = """
                INSERT INTO perfiles_entrenadores 
                (id_usuario, nombre_completo, fecha_nacimiento, especialidad, experiencia) 
                VALUES (%s, %s, %s, %s, %s)
                """
                db.execute_query(
                    coach_query,
                    (user_id, full_name, birth_date, specialty, experience),
                    conn=conn
                )
            
            # Confirmar transacción si todo salió bien
            db.commit_transaction(conn)
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
            
            page.run_once(clear_form, 3)
            
        except Exception as e:
            logger.error(f"Error during registration: {e}", exc_info=True)
            if conn:
                db.rollback_transaction(conn)
            error_text.value = f"An error occurred: {str(e)}"
            page.update()
        finally:
            hide_loading(page, loading)
            if conn:
                db.close_connection(conn)

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
                                ft.Divider(height=20, color="transparent"),
                                ft.Text("Explore example exercises:", size=12),
                                create_button(
                                    "View Exercises",
                                    on_click=lambda e: show_exercises(page),
                                    icon=icons.FITNESS_CENTER,
                                    bgcolor=COLORS["secondary"],
                                    color=COLORS["primary"],
                                    width=200
                                ),
                                create_button(
                                    "Monitoring",
                                    on_click=lambda e: show_monitoring(page),
                                    icon=icons.MONITOR_HEART,
                                    bgcolor=COLORS["secondary"],
                                    color=COLORS["primary"],
                                    width=200
                                ),
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
    page.update()

def show_monitoring(page: ft.Page):
    """Redirige a una vista para mostrar el monitoreo en tiempo real"""
    import time as time_module
    from datetime import datetime

    # Variables de estado
    monitoring_active = True
    simulation_active = False

    # Crear gráficas
    heart_rate_chart = ft.LineChart()
    oxygen_chart = ft.LineChart()

    # Configurar ejes
    heart_rate_chart.left_axis = ft.ChartAxis(
        labels=[
            ft.ChartAxisLabel(value=40, label=ft.Text("40")),
            ft.ChartAxisLabel(value=80, label=ft.Text("80")),
            ft.ChartAxisLabel(value=120, label=ft.Text("120"))
        ],
        labels_size=40
    )

    oxygen_chart.left_axis = ft.ChartAxis(
        labels=[
            ft.ChartAxisLabel(value=80, label=ft.Text("80")),
            ft.ChartAxisLabel(value=90, label=ft.Text("90")),
            ft.ChartAxisLabel(value=100, label=ft.Text("100"))
        ],
        labels_size=40
    )

    # Series de datos
    hr_series = ft.LineChartData(
        data_points=[],
        stroke_width=3,
        color=ft.colors.RED,
        curved=True,
        stroke_cap_round=True,
    )

    oxy_series = ft.LineChartData(
        data_points=[],
        stroke_width=3,
        color=ft.colors.BLUE,
        curved=True,
        stroke_cap_round=True,
    )

    heart_rate_chart.data_series = [hr_series]
    oxygen_chart.data_series = [oxy_series]

    # Iniciar simulación automáticamente
    def start_auto_simulation():
        nonlocal simulation_active
        try:
            response = requests.post("http://localhost:5000/wearable/simular")
            response.raise_for_status()
            simulation_active = True
            show_alert(page, "Simulación automática iniciada", "success")
        except Exception as e:
            show_alert(page, f"Error al iniciar simulación: {str(e)}", "error")

    # Función para detener simulación
    def stop_simulation(e):
        nonlocal simulation_active
        try:
            response = requests.post("http://localhost:5000/wearable/detener")
            response.raise_for_status()
            simulation_active = False
            show_alert(page, "Simulación detenida", "success")
            e.control.disabled = True
            page.update()
        except Exception as e:
            show_alert(page, f"Error al detener simulación: {str(e)}", "error")

    # Función para actualizar gráficas
    def update_charts():
        last_timestamp = None
        start_auto_simulation()  # Iniciar simulación al abrir

        while monitoring_active:
            try:
                response = requests.get("http://localhost:5000/wearable/datos", timeout=5)
                response.raise_for_status()
                data = response.json()

                if data:
                    latest_data = data[-1]

                    if last_timestamp != latest_data["timestamp"]:
                        # Convertir timestamp
                        try:
                            ts = datetime.strptime(
                                latest_data["timestamp"],
                                "%Y-%m-%dT%H:%M:%S.%f"
                            ).timestamp()
                        except:
                            ts = time_module.time()

                        # Agregar nuevos puntos
                        hr_point = ft.LineChartDataPoint(
                            x=ts,
                            y=latest_data["pulso_cardiaco"]
                        )
                        oxy_point = ft.LineChartDataPoint(
                            x=ts,
                            y=latest_data["oxigenacion"]
                        )

                        hr_series.data_points.append(hr_point)
                        oxy_series.data_points.append(oxy_point)

                        # Mantener solo los últimos 30 puntos
                        if len(hr_series.data_points) > 30:
                            hr_series.data_points.pop(0)
                            oxy_series.data_points.pop(0)

                        last_timestamp = latest_data["timestamp"]
                        page.update()

                time_module.sleep(1)  # Actualizar cada segundo

            except Exception as e:
                logger.error(f"Error en monitoreo: {str(e)}")
                time_module.sleep(2)

    # Construir la interfaz
    page.clean()
    page.appbar = create_app_bar(
        "Monitor en Tiempo Real",
        actions=[
            ft.IconButton(
                icon=icons.LOGOUT,
                tooltip="Logout",
                on_click=lambda e: logout(page),
            )
        ],
    )
    
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Monitoreo en Tiempo Real", 
                        weight=ft.FontWeight.BOLD, 
                        size=24, 
                        color=COLORS["primary"]
                    ),
                    
                    ft.Text("Frecuencia Cardíaca (bpm)", weight=ft.FontWeight.BOLD, size=16),
                    ft.Container(height=200, content=heart_rate_chart),
                    ft.Divider(height=20),
                    ft.Text("Nivel de Oxigenación (%)", weight=ft.FontWeight.BOLD, size=16),
                    ft.Container(height=200, content=oxygen_chart),
                    ft.Divider(height=20),
                    ft.ElevatedButton(
                        "Detener simulación",
                        on_click=stop_simulation,
                        icon=icons.STOP,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.RED_400,
                            color=ft.colors.WHITE,
                            padding=20
                        ),
                        width=180
                    )
                ],
                spacing=20
            ),
            padding=20
        )
    )

    # Iniciar hilo de actualización
    threading.Thread(target=update_charts, daemon=True).start()

def show_exercises(page: ft.Page):
    """Redirige a una vista para mostrar ejercicios de la API"""
    loading = show_loading(page, "Loading exercises...")

    try:
        # Obtener datos de la API
        response = requests.get(
            "https://wger.de/api/v2/exerciseinfo/?language=2&limit=10",
            params={"language": 2, "limit": 10},
            timeout=10
        )
        response.raise_for_status()
        exercises_data = response.json()

        if "error" in exercises_data:
            show_alert(page, f"Error: {exercises_data['error']}", "error")
            return

        exercises_list = ft.ListView(expand=True, spacing=10)

        for exercise in exercises_data.get("results", []):
            # Obtener nombre y descripción de las traducciones
            translations = exercise.get("translations", [])
            spanish_translation = next(
                (t for t in translations if t.get("language") == 2),
                None
            )

            name = spanish_translation.get("name") if spanish_translation else "Ejercicio sin nombre"
            description = spanish_translation.get(
                "description") if spanish_translation else "Descripción no disponible"

            # Limpiar HTML de la descripción
            clean_description = re.sub('<[^<]+?>', '',
                                        description) if description else "No hay descripción disponible"

            # Obtener músculos y categoría
            muscles = ", ".join([m["name"] for m in exercise.get("muscles", [])])
            category = exercise.get("category", {}).get("name", "Sin categoría")

            exercises_list.controls.append(
                create_card(
                    content=ft.Column([
                        ft.Text(name, weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(f"Categoría: {category}", size=12),
                        ft.Text(f"Músculos: {muscles or 'No especificado'}", size=12),
                        ft.Text(clean_description, size=12, color=COLORS["text"])
                    ], spacing=5),
                    padding=10,
                    margin=5
                )
            )

        # Construir la interfaz
        page.clean()
        page.appbar = create_app_bar(
            "Biblioteca de Ejercicios",
            actions=[
                ft.IconButton(
                    icon=icons.LOGOUT,
                    tooltip="Logout",
                    on_click=lambda e: logout(page),
                )
            ],
        )
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Ejercicios de la API Wger", weight=ft.FontWeight.BOLD, size=20),
                        exercises_list
                    ],
                    spacing=20
                ),
                padding=20
            )
        )

    except requests.RequestException as e:
        logger.error(f"Error al obtener ejercicios: {str(e)}")
        show_alert(page, f"Error al cargar ejercicios: {str(e)}", "error")
    finally:
        hide_loading(page, loading)
        page.update()

def logout(page: ft.Page):
    """Maneja el evento de logout"""
    try:
        page.session.clear()

        page.clean()
        page.appbar = None

        from views.shared import show_login
        show_login(page, DatabaseManager())

        page.update()
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        show_alert(page, "An error occurred during logout", "error")
        page.update()
