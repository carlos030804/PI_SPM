import flet as ft
from flet import icons
from models import CoachProfile, Workout, Exercise
from views.shared import (
    create_app_bar, create_card, show_alert, COLORS,
    show_loading, hide_loading, create_button
)
import logging
from database import DatabaseManager
from datetime import date, datetime

logger = logging.getLogger(__name__)

def create_app_bar(title: str, actions: list = None) -> ft.AppBar:
    """Crea un AppBar reutilizable con un título y acciones opcionales"""
    return ft.AppBar(
        title=ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color="white"),
        bgcolor=COLORS["primary"],
        actions=actions or []
    )

def show_coach_dashboard(page: ft.Page, db):
    # Mostrar loading
    loading = show_loading(page)
    
    try:
        user_id = page.session.get("user_id")
        profile = CoachProfile.get_by_user_id(user_id)
        
        if not profile:
            show_alert(page, "Coach profile not found", "error")
            return
        
        # Obtener datos del entrenador
        athletes = profile.get_assigned_athletes()
        workouts = profile.get_created_workouts()

        # Configurar el AppBar
        page.appbar = create_app_bar(
            f"Coach Dashboard - {profile.full_name}",
            actions=[
                ft.IconButton(
                    icon=icons.LOGOUT,
                    icon_color="white",
                    on_click=lambda e: logout(page),
                    tooltip="Logout"
                )
            ]
        )
        
        # Construir UI
        page.clean()
        page.add(
            ft.Column(
                controls=[
                    
                    ft.Tabs(
                        tabs=[
                            ft.Tab(
                                text="My Athletes",
                                icon=icons.PEOPLE_OUTLINE,
                                content=_create_athletes_tab(page, athletes,profile)
                            ),
                            ft.Tab(
                                text="My Workouts",
                                icon=icons.FITNESS_CENTER,
                                content=_create_workouts_tab(page, workouts, profile)
                            ),
                            ft.Tab(
                                text="Create Workout",
                                icon=icons.ADD_CIRCLE_OUTLINE,
                                content=_create_new_workout_tab(page, profile)
                            )
                        ],
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            )
        )
    except Exception as e:
        logger.error(f"Error loading coach dashboard: {e}")
        show_alert(page, f"Error loading dashboard: {str(e)}", "error")
    finally:
        hide_loading(page, loading)

def _create_athletes_tab(page: ft.Page, athletes: list, profile: CoachProfile) -> ft.Container:
    """Crea la pestaña de atletas asignados"""
    if not athletes:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icons.PEOPLE_OUTLINE, size=48, color=COLORS["primary"]),
                    ft.Text("No athletes assigned yet", size=16)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            expand=True
        )
    
    athlete_list = ft.ListView(
        controls=[
            ft.ListTile(
                title=ft.Text(a['nombre_completo']),
                subtitle=ft.Text(
                    f"Sport: {a['deporte']} | "
                    f"Age: {calculate_age(a['fecha_nacimiento'])} | "
                    f"HR: {a['frecuencia_cardiaca_maxima']}/{a['frecuencia_cardiaca_minima']}"
                ),
                leading=ft.Icon(icons.PERSON_OUTLINE),
                trailing=ft.PopupMenuButton(
                    icon=icons.MORE_VERT,
                    items=[
                        ft.PopupMenuItem(
                            text="View Profile",
                            on_click=lambda e, a=a: show_athlete_profile(page, a)
                        ),
                        ft.PopupMenuItem(
                            text="Assign Workout",
                            on_click=lambda e, a=a: show_assign_workout_to_athlete(page, a, profile)  # Pasa el argumento `profile`
                        )
                    ]
                ),
                on_click=lambda e, a=a: _view_athlete_profile(page, a)
            )
            for a in athletes
        ],
        expand=True
    )
    
    return ft.Container(
        content=athlete_list,
        padding=20,
        expand=True
    )



def calculate_age(birth_date: str) -> int:
    """Calcula la edad basada en la fecha de nacimiento (formato: YYYY-MM-DD o datetime.date)"""
    try:
        # Si birth_date es un string, conviértelo a datetime.date
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        
        # Calcular la edad
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except Exception as e:
        logger.error(f"Error calculating age: {e}")
        return 0  # Retorna 0 si hay un error
    

def _view_athlete_profile(page: ft.Page, athlete: dict):
    """Muestra el perfil detallado de un atleta"""
    details = (
        f"Nombre: {athlete['nombre_completo']}\n"
        f"Deporte: {athlete['deporte']}\n"
        f"Edad: {calculate_age(athlete['fecha_nacimiento'])} años\n"
        f"Frecuencia Cardiaca Máxima: {athlete['frecuencia_cardiaca_maxima']} bpm\n"
        f"Frecuencia Cardiaca Mínima: {athlete['frecuencia_cardiaca_minima']} bpm"
    )
    page.dialog = ft.AlertDialog(
        title=ft.Text("Athlete Profile"),
        content=ft.Text(details),
        actions=[
            ft.ElevatedButton("Cerrar", on_click=lambda e: setattr(page.dialog, "open", False))
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    page.dialog.open = True
    page.update()



def _view_workout_details(page: ft.Page, workout: dict):
    """Muestra los detalles de un entrenamiento"""
    logger.debug(f"View Details called with workout: {workout}")
    details = (
        f"Título: {workout['titulo']}\n"
        f"Duración Estimada: {workout['duracion_estimada']} minutos\n"
        f"Dificultad: {workout['nivel_dificultad'].capitalize()}\n"
        f"Asignaciones: {workout['asignaciones']}"
    )
    page.dialog = ft.AlertDialog(
        title=ft.Text("Detalles del Entrenamiento"),
        content=ft.Text(details),
        actions=[
            ft.ElevatedButton("Cerrar", on_click=lambda e: setattr(page.dialog, "open", False))
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    page.dialog.open = True
    page.update()




def _assign_workout_to_athletes(athlete_id: int, workout_id: int) -> bool:
    """Asigna un entrenamiento a un atleta en la base de datos"""
    try:
        logger.debug(f"Assigning workout {workout_id} to athlete {athlete_id}")
        query = """
        INSERT INTO asignaciones_atletas (id_atleta, id_entrenamiento, fecha_asignacion, estado)
        VALUES (%s, %s, NOW(), 'pendiente')
        """
        DatabaseManager.execute_query(query, (athlete_id, workout_id), commit=True)
        return True
    except Exception as e:
        logger.error(f"Error assigning workout to athlete: {e}")
        return False


def _create_workouts_tab(page: ft.Page, workouts: list, profile: CoachProfile) -> ft.Container:
    """Crea la pestaña de entrenamientos creados"""
    logger.debug(f"Workouts data: {workouts}")
    if not workouts:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icons.FITNESS_CENTER, size=48, color=COLORS["primary"]),
                    ft.Text("No workouts created yet", size=16)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            expand=True
        )
    
    workout_list = ft.ListView(
        controls=[
            ft.ListTile(
                title=ft.Text(w['titulo']),
                subtitle=ft.Text(
                    f"Duration: {w['duracion_estimada']} min | "
                    f"Difficulty: {w['nivel_dificultad']} | "
                    f"Assignments: {w['asignaciones']}"
                ),
                leading=ft.Icon(icons.FITNESS_CENTER),
                trailing=ft.PopupMenuButton(
                    icon=icons.MORE_VERT,
                    items=[
                        ft.PopupMenuItem(
                            text="View Details",
                            on_click=lambda e, w=w: show_workout_details(page, w)
                        ),
                        ft.PopupMenuItem(
                            text="Edit",
                            on_click=lambda e, w=w: show_edit_workout(page, w)
                        ),
                        ft.PopupMenuItem(
                            text="Assign to Athletes",
                            on_click=lambda e, w=w: show_assign_workout(page, w, profile)
                        )
                    ]
                ),
                on_click=lambda e, w=w: _view_workout_details(page, w)
            )
            for w in workouts
        ],
        expand=True
    )
    
    return ft.Container(
        content=workout_list,
        padding=20,
        expand=True
    )

def logout(page: ft.Page):
    """Cierra la sesión y redirige al login"""
    try:
        # Limpiar la sesión del usuario
        page.session.clear()

        # Limpiar la página
        page.clean()
        page.appbar = None  # Eliminar el AppBar actual

        # Redirigir al login
        from views.shared import show_login
        show_login(page, DatabaseManager())

        # Forzar actualización de la página
        page.update()
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        show_alert(page, "Error during logout", "error")

def _create_new_workout_tab(page: ft.Page, profile: CoachProfile) -> ft.Container:
    """Crea la pestaña para crear nuevos entrenamientos"""
    titulo_field = ft.TextField(label="Título del Entrenamiento", width=300)
    descripcion_field = ft.TextField(label="Descripción", multiline=True, min_lines=3, max_lines=5, width=300)
    duracion_field = ft.TextField(label="Duración Estimada (min)", keyboard_type=ft.KeyboardType.NUMBER, width=300)
    dificultad_dropdown = ft.Dropdown(
        label="Nivel de Dificultad",
        options=[
            ft.DropdownOption("principiante"),
            ft.DropdownOption("intermedio"),
            ft.DropdownOption("avanzado")
        ],
        width=300
    )
    error_text = ft.Text("", color="red")

    def create_workout(e):
        """Crea un nuevo entrenamiento"""
        if not titulo_field.value or not duracion_field.value or not dificultad_dropdown.value:
            error_text.value = "Todos los campos son obligatorios."
            page.update()
            return
        
        # Validar que el nivel de dificultad sea válido
        if dificultad_dropdown.value not in ["principiante", "intermedio", "avanzado"]:
            error_text.value = "El nivel de dificultad no es válido."
            page.update()
            return

        try:
            query = """
            INSERT INTO entrenamientos (id_entrenador, titulo, descripcion, duracion_estimada, nivel_dificultad)
            VALUES (%s, %s, %s, %s, %s)
            """
            DatabaseManager.execute_query(
                query,
                (profile.id, titulo_field.value, descripcion_field.value, int(duracion_field.value), dificultad_dropdown.value),
                commit=True
            )
            show_alert(page, "Entrenamiento creado correctamente.", "success")
            show_coach_dashboard(page, DatabaseManager())
        except Exception as ex:
            logger.error(f"Error creating workout: {ex}")
            error_text.value = "Error al crear el entrenamiento."
            page.update()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Crear Nuevo Entrenamiento", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ft.Divider(),
                titulo_field,
                descripcion_field,
                duracion_field,
                dificultad_dropdown,
                error_text,
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Crear",
                            icon=icons.ADD,
                            on_click=create_workout,
                            style=ft.ButtonStyle(
                                bgcolor=COLORS["primary"],
                                color="white"
                            )
                        ),
                        ft.ElevatedButton(
                            "Cancelar",
                            icon=icons.CANCEL,
                            on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                            style=ft.ButtonStyle(
                                bgcolor="gray",
                                color="white"
                            )
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        padding=20,
        expand=True
    )

def show_workout_details(page: ft.Page, workout: dict):
    """Redirige a una vista con los detalles del entrenamiento"""
    page.appbar = create_app_bar(
        "Detalles del Entrenamiento",
        actions=[
            ft.IconButton(
                icon=icons.ARROW_BACK,
                on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                tooltip="Volver"
            )
        ]
    )
    page.clean()
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    
                    ft.Text("Detalles del Entrenamiento", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                    ft.Divider(),
                    ft.Text(f"Título:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(workout['titulo'], size=16),
                    ft.Text(f"Duración Estimada:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{workout['duracion_estimada']} minutos", size=16),
                    ft.Text(f"Dificultad:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(workout['nivel_dificultad'].capitalize(), size=16),
                    ft.Text(f"Asignaciones:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(workout['asignaciones'], size=16),
                    ft.ElevatedButton(
                        "Volver",
                        on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                        style=ft.ButtonStyle(bgcolor=COLORS["primary"], color="white")
                    )
                ],
                spacing=15
            ),
            padding=20
        )
    )
def show_edit_workout(page: ft.Page, workout: dict):
    """Redirige a una vista para editar un entrenamiento"""
    page.appbar = create_app_bar(
        "Editar Entrenamiento",
        actions=[
            ft.IconButton(
                icon=icons.ARROW_BACK,
                on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                tooltip="Volver"
            )
        ]
    )
    titulo_field = ft.TextField(label="Título", value=workout['titulo'], width=400)
    duracion_field = ft.TextField(label="Duración (min)", value=str(workout['duracion_estimada']), keyboard_type=ft.KeyboardType.NUMBER, width=400)
    dificultad_dropdown = ft.Dropdown(
        label="Dificultad",
        options=[
            ft.DropdownOption("principiante"),
            ft.DropdownOption("intermedio"),
            ft.DropdownOption("avanzado")
        ],
        value=workout['nivel_dificultad'],
        width=400
    )

    def save_changes(e):
        """Guarda los cambios realizados al entrenamiento"""
        if not titulo_field.value or not duracion_field.value or not dificultad_dropdown.value:
            show_alert(page, "Todos los campos son obligatorios.", "error")
            return

        try:
            query = """
            UPDATE entrenamientos
            SET titulo = %s, duracion_estimada = %s, nivel_dificultad = %s
            WHERE id_entrenamiento = %s
            """
            DatabaseManager.execute_query(
                query,
                (titulo_field.value, int(duracion_field.value), dificultad_dropdown.value, workout['id_entrenamiento']),
                commit=True
            )
            show_alert(page, "Entrenamiento actualizado correctamente.", "success")
            show_coach_dashboard(page, DatabaseManager())  # Redirige al dashboard
        except Exception as ex:
            logger.error(f"Error updating workout: {ex}")
            show_alert(page, "Error al actualizar el entrenamiento.", "error")

    page.clean()
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    
                    ft.Text("Editar Entrenamiento", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                    ft.Divider(),
                    titulo_field,
                    duracion_field,
                    dificultad_dropdown,
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Guardar",
                                on_click=save_changes,
                                style=ft.ButtonStyle(bgcolor=COLORS["primary"], color="white")
                            ),
                            ft.ElevatedButton(
                                "Cancelar",
                                on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                                style=ft.ButtonStyle(bgcolor="gray", color="white")
                            )
                        ],
                        spacing=10
                    )
                ],
                spacing=15
            ),
            padding=20
        )
    )

def show_assign_workout(page: ft.Page, workout: dict, profile: CoachProfile):
    """Redirige a una vista para asignar un entrenamiento a atletas"""
    athletes = profile.get_assigned_athletes()

    if not athletes:
        show_alert(page, "No hay atletas disponibles para asignar este entrenamiento.", "error")
        return

    athlete_checkboxes = [
        ft.Checkbox(label=a['nombre_completo'], value=False, data=a['id_atleta'])
        for a in athletes
    ]

    def assign_workout(e):
        """Asigna el entrenamiento a los atletas seleccionados"""
        selected_athletes = [cb.data for cb in athlete_checkboxes if cb.value]
        if not selected_athletes:
            show_alert(page, "Selecciona al menos un atleta.", "error")
            return

        for athlete_id in selected_athletes:
            success = _assign_workout_to_athletes(athlete_id, workout['id_entrenamiento'])
            if not success:
                show_alert(page, f"Error al asignar el entrenamiento al atleta ID {athlete_id}.", "error")
                return

        show_alert(page, "Entrenamiento asignado correctamente a los atletas seleccionados.", "success")
        show_coach_dashboard(page, DatabaseManager())  # Redirige al dashboard

    page.clean()
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    
                    ft.Text("Asignar Entrenamiento", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                    ft.Divider(),
                    ft.Column(athlete_checkboxes, spacing=10),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Asignar",
                                on_click=assign_workout,
                                style=ft.ButtonStyle(bgcolor=COLORS["primary"], color="white")
                            ),
                            ft.ElevatedButton(
                                "Cancelar",
                                on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                                style=ft.ButtonStyle(bgcolor="gray", color="white")
                            )
                        ],
                        spacing=10
                    )
                ],
                spacing=15
            ),
            padding=20
        )
    )

def show_athlete_profile(page: ft.Page, athlete: dict):
    """Redirige a una vista con los detalles del perfil del atleta"""
    page.clean()
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    
                    ft.Text("Perfil del Atleta", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                    ft.Divider(),
                    ft.Text(f"Nombre:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(athlete['nombre_completo'], size=16),
                    ft.Text(f"Deporte:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(athlete['deporte'], size=16),
                    ft.Text(f"Edad:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{calculate_age(athlete['fecha_nacimiento'])} años", size=16),
                    ft.Text(f"Frecuencia Cardiaca Máxima:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{athlete['frecuencia_cardiaca_maxima']} bpm", size=16),
                    ft.Text(f"Frecuencia Cardiaca Mínima:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{athlete['frecuencia_cardiaca_minima']} bpm", size=16),
                    ft.ElevatedButton(
                        "Volver",
                        on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                        style=ft.ButtonStyle(bgcolor=COLORS["primary"], color="white")
                    )
                ],
                spacing=15
            ),
            padding=20
        )
    )
def show_assign_workout_to_athlete(page: ft.Page, athlete: dict, profile: CoachProfile):
    """Redirige a una vista para asignar un entrenamiento a un atleta específico"""
    workouts = profile.get_created_workouts()

    if not workouts:
        show_alert(page, "No hay entrenamientos disponibles para asignar.", "error")
        return

    workout_dropdown = ft.Dropdown(
        label="Selecciona un entrenamiento",
        options=[
            ft.DropdownOption(text=w['titulo'], key=w['id_entrenamiento']) for w in workouts
        ],
        width=400
    )

    def assign_workout(e):
        """Asigna el entrenamiento seleccionado al atleta"""
        selected_workout = workout_dropdown.value
        if not selected_workout:
            show_alert(page, "Por favor selecciona un entrenamiento.", "error")
            return

        success = _assign_workout_to_athletes(athlete['id_atleta'], selected_workout)
        if success:
            show_alert(page, "Entrenamiento asignado correctamente.", "success")
            show_coach_dashboard(page, DatabaseManager())  # Redirige al dashboard
        else:
            show_alert(page, "Error al asignar el entrenamiento.", "error")

    page.clean()
    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    
                    ft.Text("Asignar Entrenamiento", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                    ft.Divider(),
                    ft.Text(f"Atleta: {athlete['nombre_completo']}", size=18, weight=ft.FontWeight.BOLD),
                    workout_dropdown,
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Asignar",
                                on_click=assign_workout,
                                style=ft.ButtonStyle(bgcolor=COLORS["primary"], color="white")
                            ),
                            ft.ElevatedButton(
                                "Cancelar",
                                on_click=lambda e: show_coach_dashboard(page, DatabaseManager()),
                                style=ft.ButtonStyle(bgcolor="gray", color="white")
                            )
                        ],
                        spacing=10
                    )
                ],
                spacing=15
            ),
            padding=20
        )
    )