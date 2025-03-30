import matplotlib.pyplot as plt
from io import BytesIO
import base64
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def calculate_hr_zones(max_hr: int, resting_hr: int) -> Dict[str, int]:
    """
    Calcula las zonas de frecuencia cardiaca basadas en la fórmula de Karvonen
    
    Args:
        max_hr: Frecuencia cardiaca máxima
        resting_hr: Frecuencia cardiaca en reposo
    
    Returns:
        Diccionario con las zonas de entrenamiento
    """
    hr_range = max_hr - resting_hr
    return {
        "Zone 1 (Recovery)": int(resting_hr + 0.5 * hr_range),
        "Zone 2 (Light Aerobic)": int(resting_hr + 0.6 * hr_range),
        "Zone 3 (Aerobic)": int(resting_hr + 0.7 * hr_range),
        "Zone 4 (Anaerobic Threshold)": int(resting_hr + 0.8 * hr_range),
        "Zone 5 (Maximum Effort)": int(resting_hr + 0.9 * hr_range),
        "Max HR": max_hr
    }

def create_hr_zones_chart(zones: Dict[str, int], resting_hr: int) -> str:
    """
    Crea un gráfico de las zonas de frecuencia cardiaca
    
    Args:
        zones: Diccionario con las zonas de entrenamiento
        resting_hr: Frecuencia cardiaca en reposo
    
    Returns:
        Imagen del gráfico en base64
    """
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