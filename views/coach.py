import flet as ft
from flet import icons
from models import CoachProfile, Workout, Exercise
from views.shared import (
    create_app_bar, create_card, show_alert, COLORS,
    show_loading, hide_loading, create_button
)
import logging

logger = logging.getLogger(__name__)

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
        
        # Construir UI
        page.clean()
        page.add(
            ft.Column(
                controls=[
                    create_app_bar(
                        f"Coach Dashboard - {profile.full_name}",
                        actions=[
                            ft.IconButton(
                                icon=icons.LOGOUT,
                                icon_color="white",
                                on_click=lambda e: logout(page),
                                tooltip="Logout"
                            )
                        ]
                    ),
                    ft.Tabs(
                        tabs=[
                            ft.Tab(
                                text="My Athletes",
                                icon=icons.PEOPLE_OUTLINE,
                                content=_create_athletes_tab(page, athletes)
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

def _create_athletes_tab(page: ft.Page, athletes: list) -> ft.Container:
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
                            on_click=lambda e, a=a: _view_athlete_profile(page, a)
                        ),
                        ft.PopupMenuItem(
                            text="Assign Workout",
                            on_click=lambda e, a=a: _assign_workout_dialog(page, a)
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

def _create_workouts_tab(page: ft.Page, workouts: list, profile: CoachProfile) -> ft.Container:
    """Crea la pestaña de entrenamientos creados"""
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
                            on_click=lambda e, w=w: _view_workout_details(page, w)
                        ),
                        ft.PopupMenuItem(
                            text="Edit",
                            on_click=lambda e, w=w: _edit_workout(page, w)
                        ),
                        ft.PopupMenuItem(
                            text="Assign to Athletes",
                            on_click=lambda e, w=w: _assign_workout_to_athletes(page, w, profile)
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

def _create_new_workout_tab(page: ft.Page, profile: CoachProfile) -> ft.Container:
    """Crea la pestaña para crear nuevos entrenamientos"""
    # Implementación del formulario para crear nuevos entrenamientos
    pass