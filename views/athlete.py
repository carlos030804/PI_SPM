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
from database import DatabaseManager
import base64
import logging

logger = logging.getLogger(__name__)

def show_athlete_dashboard(page: ft.Page, db):
    # Mostrar loading
    if not page.session.get("user_id"):
        return logout(page, db)
    
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

        # Configurar el AppBar primero
        page.appbar = create_app_bar(
            "Athlete Dashboard",
            actions=[
                ft.IconButton(
                    icon=icons.LOGOUT,
                    icon_color="white",
                    on_click=lambda e: logout(page, db),  # Pasa db aquí
                    tooltip="Logout"
                )
            ]
        )

        # Configurar el contenido principal SIN incluir el AppBar
        page.add(
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
        )

    except Exception as e:
        logger.error(f"Error loading athlete dashboard: {e}")
        show_alert(page, f"Error loading dashboard: {str(e)}", "error")
    finally:
        hide_loading(page, loading)

def _create_profile_section(page: ft.Page, profile: AthleteProfile) -> ft.Container:
    """Crea la sección de perfil del atleta con un diseño mejorado"""
    coach_name = "No asignado"
    if profile.coach_id:
        # En una implementación real, obtendrías el nombre del entrenador de la base de datos
        coach_name = "Nombre del Entrenador"  # Temporal

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Información Personal", size=20, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.Icon(icons.PERSON, color=COLORS["primary"]),
                        ft.Text("Nombre Completo:", weight=ft.FontWeight.BOLD),
                        ft.Text(profile.full_name, italic=True)
                    ],
                    spacing=10
                ),
                ft.Row(
                    controls=[
                        ft.Icon(icons.CAKE, color=COLORS["primary"]),
                        ft.Text("Edad:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"{profile.age} años", italic=True)
                    ],
                    spacing=10
                ),
                ft.Row(
                    controls=[
                        ft.Icon(icons.SPORTS, color=COLORS["primary"]),
                        ft.Text("Deporte:", weight=ft.FontWeight.BOLD),
                        ft.Text(profile.sport, italic=True)
                    ],
                    spacing=10
                ),
                ft.Row(
                    controls=[
                        ft.Icon(icons.SCHOOL, color=COLORS["primary"]),
                        ft.Text("Entrenador:", weight=ft.FontWeight.BOLD),
                        ft.Text(coach_name, italic=True)
                    ],
                    spacing=10
                ),
                ft.Row(
                    controls=[
                        ft.Icon(icons.STRAIGHTEN, color=COLORS["primary"]),
                        ft.Text("Altura:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"{profile.height} cm", italic=True)
                    ],
                    spacing=10
                ),
                ft.Row(
                    controls=[
                        ft.Icon(icons.FITNESS_CENTER, color=COLORS["primary"]),
                        ft.Text("Peso:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"{profile.weight} kg", italic=True)
                    ],
                    spacing=10
                ),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Editar Perfil",
                            icon=icons.EDIT,
                            on_click=lambda e: show_edit_profile(page, profile),
                            style=ft.ButtonStyle(
                                bgcolor=COLORS["primary"],
                                color="white"
                            ),
                            width=150
                        )
                    ],
                    alignment=ft.MainAxisAlignment.END
                )
            ],
            spacing=15
        ),
        border=ft.border.all(1, COLORS["primary"]),  # Agregar borde manualmente
        border_radius=10,
        padding=15,
        bgcolor="#F9F9F9"
    )

def show_edit_profile(page: ft.Page, profile: AthleteProfile):
    """Muestra una vista mejorada para editar el perfil del atleta con campos centrados, compactos y con iconos"""
    # Crear campos de texto con iconos representativos
    full_name_field = ft.TextField(
        label="Nombre completo",
        value=profile.full_name,
        disabled=True,
        prefix_icon=icons.PERSON,  # Icono para el nombre
        tooltip="Este es tu nombre completo registrado"
    )
    height_field = ft.TextField(
        label="Altura (cm)",
        value=str(profile.height),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300,  # Limitar el ancho del campo
        prefix_icon=icons.STRAIGHTEN,  # Icono para altura
        tooltip="Introduce tu altura en centímetros"
    )
    weight_field = ft.TextField(
        label="Peso (kg)",
        value=str(profile.weight),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300,  # Limitar el ancho del campo
        prefix_icon=icons.FITNESS_CENTER,  # Icono para peso
        tooltip="Introduce tu peso en kilogramos"
    )
    sport_field = ft.TextField(
        label="Deporte",
        value=profile.sport,
        width=300,  # Limitar el ancho del campo
        prefix_icon=icons.SPORTS,  # Icono para deporte
        tooltip="Introduce el deporte que practicas"
    )
    resting_hr_field = ft.TextField(
        label="Frecuencia cardiaca en reposo (bpm)",
        value=str(profile.resting_hr) if profile.resting_hr else "",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300,  # Limitar el ancho del campo
        prefix_icon=icons.HEART_BROKEN,  # Icono para frecuencia cardiaca en reposo
        tooltip="Introduce tu frecuencia cardiaca en reposo"
    )
    max_hr_field = ft.TextField(
        label="Frecuencia cardiaca máxima (bpm)",
        value=str(profile.max_hr) if profile.max_hr else "",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300,  # Limitar el ancho del campo
        prefix_icon=icons.FAVORITE,  # Icono para frecuencia cardiaca máxima
        tooltip="Introduce tu frecuencia cardiaca máxima"
    )
    error_text = ft.Text("", color="red")

    def save_changes(e):
        """Guarda los cambios del perfil"""
        error_text.value = ""  # Limpia el mensaje de error
        try:
            # Validar altura
            if height_field.value and float(height_field.value) <= 0:
                error_text.value = "La altura debe ser mayor que 0"
                page.update()
                return

            # Validar peso
            if weight_field.value and float(weight_field.value) <= 0:
                error_text.value = "El peso debe ser mayor que 0"
                page.update()
                return

            # Validar frecuencia cardiaca
            if resting_hr_field.value and int(resting_hr_field.value) <= 0:
                error_text.value = "La frecuencia cardiaca debe ser mayor que 0"
                page.update()
                return

            # Guardar cambios
            new_height = float(height_field.value) if height_field.value else None
            new_weight = float(weight_field.value) if weight_field.value else None
            new_sport = sport_field.value.strip() if sport_field.value else None
            new_resting_hr = int(resting_hr_field.value) if resting_hr_field.value else None
            new_max_hr = int(max_hr_field.value) if max_hr_field.value else None

            success = profile.update_profile(
                height=new_height,
                weight=new_weight,
                sport=new_sport,
                resting_hr=new_resting_hr
            )

            # Actualizar frecuencia cardiaca máxima si es diferente
            if new_max_hr != profile.max_hr:
                query = """
                UPDATE perfiles_atletas 
                SET frecuencia_cardiaca_maxima = %s
                WHERE id_atleta = %s
                """
                DatabaseManager.execute_query(
                    query,
                    (new_max_hr, profile.id),
                    commit=True
                )
                profile.max_hr = new_max_hr

            if success:
                show_alert(page, "Perfil actualizado correctamente", "success")
                show_athlete_dashboard(page, DatabaseManager())  # Redirigir al dashboard
            else:
                error_text.value = "Error al actualizar el perfil"
                page.update()

        except Exception as ex:
            logger.error(f"Error saving profile changes: {ex}")
            error_text.value = "Ocurrió un error inesperado"
            page.update()

    def cancel_changes(e):
        """Cancela la edición y regresa al dashboard"""
        show_athlete_dashboard(page, DatabaseManager())

    # Construir la interfaz de edición
    page.clean()
    page.add(
        ft.Column(
            controls=[
                ft.Text("Editar Perfil", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ft.Divider(),
                ft.Column(
                    controls=[
                        ft.Container(full_name_field, alignment=ft.alignment.center),
                        ft.Container(height_field, alignment=ft.alignment.center),
                        ft.Container(weight_field, alignment=ft.alignment.center),
                        ft.Container(sport_field, alignment=ft.alignment.center),
                        ft.Container(resting_hr_field, alignment=ft.alignment.center),
                        ft.Container(max_hr_field, alignment=ft.alignment.center),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                ),
                error_text,
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Guardar",
                            icon=icons.SAVE,
                            on_click=save_changes,
                            style=ft.ButtonStyle(
                                bgcolor=COLORS["primary"],
                                color="white"
                            ),
                            tooltip="Guarda los cambios realizados en tu perfil"
                        ),
                        ft.ElevatedButton(
                            "Cancelar",
                            icon=icons.CANCEL,
                            on_click=cancel_changes,
                            style=ft.ButtonStyle(
                                bgcolor="gray",
                                color="orange"
                            ),
                            tooltip="Cancela los cambios y regresa al dashboard"
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                )
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    )
def _create_hr_zones_section(zones: dict, chart_img: str, profile: AthleteProfile) -> ft.Container:
    """Crea la sección de zonas de frecuencia cardiaca con un diseño mejorado"""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Heart Rate Zones", size=20, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.Icon(icons.FAVORITE, color=COLORS["primary"]),
                        ft.Text("Max HR:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"{profile.max_hr} bpm", italic=True)
                    ],
                    spacing=10
                ),
                ft.Row(
                    controls=[
                        ft.Icon(icons.HEART_BROKEN, color=COLORS["primary"]),
                        ft.Text("Resting HR:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"{profile.resting_hr} bpm", italic=True)
                    ],
                    spacing=10
                ),
                ft.Divider(),
                ft.Text("Zones:", size=18, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
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
                                    f"{zones[zone]}" if i == len(zones) - 1
                                    else f"{zones[zone]} - {list(zones.values())[i + 1]}"
                                ))
                                
                            ]
                            
                        )
                        for i, zone in enumerate(zones)
                    ],
                    
                    border=ft.border.all(1, COLORS["primary"]),
                ),ft.Container(
                    content=ft.Image(src_base64=chart_img, width=600, height=300),
                    alignment=ft.alignment.center,
                    padding=10
                )
                
                
            ],
            spacing=15
        ),
        border=ft.border.all(1, COLORS["primary"]),
        border_radius=10,
        padding=15,
        bgcolor="#F9F9F9"
    )
def _create_workouts_section(page: ft.Page, workouts: list) -> ft.Container:
    """Crea la sección de entrenamientos asignados con un diseño mejorado"""
    # Lista de entrenamientos
    workout_list = ft.Column(
        controls=[
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icons.FITNESS_CENTER, color=COLORS["primary"]),
                        ft.Column(
                            controls=[
                                ft.Text(w['titulo'], weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"Status: {w['estado'].replace('_', ' ').title()} | "
                                    f"Duration: {w['duracion_estimada']} min | "
                                    f"Difficulty: {w['nivel_dificultad'].capitalize()}",
                                    size=12,
                                    italic=True
                                )
                            ],
                            spacing=5
                        ),
                        ft.PopupMenuButton(
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
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=10
                ),
                padding=10,
                border=ft.border.all(1, COLORS["primary"]),
                border_radius=8,
                bgcolor="#F9F9F9"
            )
            for w in workouts
        ],
        spacing=10
    )

    # Contenedor principal
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("My Workouts", size=20, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ft.Divider(),
                workout_list if workouts else ft.Text("No workouts assigned yet.", italic=True, size=14)
            ],
            spacing=15
        ),
        border=ft.border.all(1, COLORS["primary"]),
        border_radius=10,
        padding=15,
        bgcolor="#F9F9F9"
    )
def _view_workout_details(page: ft.Page, workout: dict):
    """Muestra los detalles de un entrenamiento"""
    # Implementación de la vista de detalles
    show_alert(page, f"Workout Details:\n{workout}", "info")

def _mark_workout_completed(page: ft.Page, workout: dict):
    """Marca un entrenamiento como completado"""
    # Implementación de la finalización de entrenamiento
    

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

def logout(page: ft.Page, db):
    """Cierra la sesión y redirige al login"""
    try:
        # Limpiar completamente la página
        page.clean()
        page.appbar = None  # Eliminar el AppBar actual
        
        # Limpiar la sesión
        page.session.clear()
        
        # Redirigir al login
        from views.shared import show_login
        show_login(page, db)
        
        # Forzar actualización de la página
        page.update()
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        show_alert(page, "Error during logout", "error")