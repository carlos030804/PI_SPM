import flet as ft
from flet import icons
from datetime import date
from models import AthleteProfile, WorkoutAssignment
from views.shared import (
    create_app_bar, create_card, show_alert, COLORS,
    show_loading, hide_loading, create_button
)
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import logging

logger = logging.getLogger(__name__)

def show_athlete_dashboard(page: ft.Page, db):
    # Mostrar loading
    loading = show_loading(page)
    
    try:
        user_id = page.session.get("user_id")
        profile = AthleteProfile.get_by_user_id(user_id)
        
        if not profile:
            show_alert(page, "Athlete profile not found", "error")
            return
        
        # Calcular zonas de frecuencia cardiaca si existen los datos necesarios
        hr_zones = {}
        chart_img = None
        
        if profile.max_hr and profile.resting_hr:
            hr_zones = calculate_hr_zones(profile.max_hr, profile.resting_hr)
            chart_img = create_hr_zones_chart(hr_zones, profile.resting_hr)
        
        # Obtener entrenamientos asignados
        workouts = profile.get_workouts()
        
        # Construir UI
        page.clean()
        page.add(
            ft.Column(
                controls=[
                    create_app_bar(
                        "Athlete Dashboard",
                        actions=[
                            ft.IconButton(
                                icon=icons.LOGOUT,
                                icon_color="white",
                                on_click=lambda e: logout(page),
                                tooltip="Logout"
                            )
                        ]
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                _create_profile_section(page, profile),
                                _create_hr_zones_section(hr_zones, chart_img, profile) 
                                if profile.max_hr and profile.resting_hr 
                                else ft.Container(),
                                _create_workouts_section(page, workouts)
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
    except Exception as e:
        logger.error(f"Error loading athlete dashboard: {e}")
        show_alert(page, f"Error loading dashboard: {str(e)}", "error")
    finally:
        hide_loading(page, loading)

def _create_profile_section(page: ft.Page, profile: AthleteProfile) -> ft.Card:
    """Crea la sección de perfil del atleta"""
    coach_name = "Not assigned"
    if profile.coach_id:
        # En una implementación real, obtendrías el nombre del entrenador de la base de datos
        coach_name = "Coach Name"  # Temporal
    
    return create_card(
        ft.Column([
            ft.Text("Personal Information", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                ft.Text("Full Name:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(profile.full_name)
            ]),
            ft.Row([
                ft.Text("Age:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(f"{profile.age} years")
            ]),
            ft.Row([
                ft.Text("Sport:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(profile.sport)
            ]),
            ft.Row([
                ft.Text("Coach:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(coach_name)
            ]),
            ft.Row([
                ft.Text("Height:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(f"{profile.height} cm")
            ]),
            ft.Row([
                ft.Text("Weight:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(f"{profile.weight} kg")
            ]),
            ft.Row([
                create_button(
                    "Edit Profile",
                    lambda e: _edit_profile(page, profile),
                    icon=icons.EDIT,
                    width=150
                )
            ], alignment=ft.MainAxisAlignment.END)
        ], spacing=10),
        title="My Profile"
    )

def _edit_profile(page: ft.Page, profile: AthleteProfile):
    """Muestra el diálogo para editar el perfil"""
    # Implementación del diálogo de edición
    pass

def _create_hr_zones_section(zones: dict, chart_img: str, profile: AthleteProfile) -> ft.Card:
    """Crea la sección de zonas de frecuencia cardiaca"""
    return create_card(
        ft.Column([
            ft.Text("Heart Rate Zones", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                ft.Text("Max HR:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(f"{profile.max_hr} bpm")
            ]),
            ft.Row([
                ft.Text("Resting HR:", width=150, weight=ft.FontWeight.BOLD),
                ft.Text(f"{profile.resting_hr} bpm")
            ]),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Zone", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Range (bpm)", weight=ft.FontWeight.BOLD)),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(zone)),
                            ft.DataCell(ft.Text(
                                f"{zones[zone]}" if i == len(zones)-1 
                                else f"{zones[zone]} - {list(zones.values())[i+1]}"
                            ))
                        ]
                    )
                    for i, zone in enumerate(zones)
                ],
                border=ft.border.all(1, COLORS["primary"]),
            ),
            ft.Container(
                ft.Image(src_base64=chart_img, width=600, height=300),
                alignment=ft.alignment.center,
                padding=10
            )
        ], spacing=15),
        title="Heart Rate Analysis"
    )

def _create_workouts_section(page: ft.Page, workouts: list) -> ft.Column:
    """Crea la sección de entrenamientos asignados"""
    workout_list = ft.ListView(
        controls=[
            ft.ListTile(
                title=ft.Text(w['titulo']),
                subtitle=ft.Text(
                    f"Status: {w['estado'].replace('_', ' ').title()} | "
                    f"Duration: {w['duracion_estimada']} min | "
                    f"Difficulty: {w['nivel_dificultad'].capitalize()}"
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
                            text="Mark as Completed",
                            on_click=lambda e, w=w: _mark_workout_completed(page, w),
                            disabled=w['estado'] == 'completado'
                        )
                    ]
                )
            )
            for w in workouts
        ],
        expand=True,
        spacing=5
    )
    
    return ft.Column([
        ft.Text("My Workouts", size=18, weight=ft.FontWeight.BOLD),
        workout_list if workouts else ft.Text("No workouts assigned yet.", italic=True)
    ], spacing=10)

def _view_workout_details(page: ft.Page, workout: dict):
    """Muestra los detalles de un entrenamiento"""
    # Implementación de la vista de detalles
    pass

def _mark_workout_completed(page: ft.Page, workout: dict):
    """Marca un entrenamiento como completado"""
    # Implementación de la finalización de entrenamiento
    pass

def calculate_hr_zones(max_hr: int, resting_hr: int) -> dict:
    """Calcula las zonas de frecuencia cardiaca"""
    hr_range = max_hr - resting_hr
    return {
        "Zone 1 (Recovery)": int(resting_hr + 0.5 * hr_range),
        "Zone 2 (Light Aerobic)": int(resting_hr + 0.6 * hr_range),
        "Zone 3 (Aerobic)": int(resting_hr + 0.7 * hr_range),
        "Zone 4 (Anaerobic Threshold)": int(resting_hr + 0.8 * hr_range),
        "Zone 5 (Maximum Effort)": int(resting_hr + 0.9 * hr_range),
        "Max HR": max_hr
    }

def create_hr_zones_chart(zones: dict, resting_hr: int) -> str:
    """Crea un gráfico de las zonas de frecuencia cardiaca"""
    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        
        zone_names = list(zones.keys())
        zone_values = list(zones.values())
        
        # Gráfico de líneas con puntos
        ax.plot(zone_names, zone_values, 
                marker='o', 
                linestyle='-', 
                color='#FF7F2A', 
                markersize=8,
                linewidth=2)
        
        # Línea de frecuencia cardiaca en reposo
        ax.axhline(y=resting_hr, 
                  color='gray', 
                  linestyle='--', 
                  label='Resting HR',
                  linewidth=1.5)
        
        # Colores para las zonas
        zone_colors = ["#FF6B6B", "#FFA500", "#FFD700", "#90EE90", "#4682B4"]
        
        # Áreas coloreadas para cada zona
        for i in range(len(zone_values)-1):
            ax.axhspan(zone_values[i], 
                      zone_values[i+1], 
                      facecolor=zone_colors[i], 
                      alpha=0.2)
        
        # Configuración del gráfico
        ax.set_title("Heart Rate Training Zones", 
                    pad=20, 
                    fontsize=14, 
                    fontweight='bold')
        ax.set_ylabel("Beats per minute (bpm)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Rotar etiquetas del eje X para mejor legibilidad
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(fontsize=10)
        
        # Leyenda
        plt.legend(fontsize=10)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Guardar en buffer
        buf = BytesIO()
        plt.savefig(buf, 
                   format='png', 
                   dpi=100, 
                   bbox_inches='tight',
                   transparent=False)
        plt.close(fig)
        buf.seek(0)
        
        # Convertir a base64
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error creating HR zones chart: {e}")
        return ""

def logout(page: ft.Page):
    """Cierra la sesión y redirige al login"""
    page.session.clear()
    from views.shared import show_login
    show_login(page)