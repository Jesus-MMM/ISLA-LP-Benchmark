"""
Utilidades para obtener informacion del sistema y entorno.
"""

import platform
import sys
from datetime import datetime
from typing import Any, Dict


def get_system_info() -> dict[str, Any]:
    """
    Obtiene informacion completa del sistema.
    
    Returns:
        Diccionario con informacion del sistema.
    """
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version.split()[0],
            "python_executable": sys.executable,
        },
        "hostname": platform.node(),
        "timestamp": datetime.now().isoformat(),
    }


def format_system_report(info: dict[str, Any]) -> str:
    """
    Formatea la informacion del sistema como reporte legible.
    
    Args:
        info: Diccionario con informacion del sistema.
        
    Returns:
        String con el reporte formateado.
    """
    lines = []
    lines.append("=" * 50)
    lines.append("INFORMACION DEL SISTEMA")
    lines.append("=" * 50)

    p = info.get("platform", {})
    lines.append(f"Sistema: {p.get('system', 'N/A')}")
    lines.append(f"Version: {p.get('release', 'N/A')}")
    lines.append(f"Maquina: {p.get('machine', 'N/A')}")
    lines.append(f"Procesador: {p.get('processor', 'N/A')}")
    lines.append(f"Python: {p.get('python_version', 'N/A')}")
    lines.append(f"Hostname: {info.get('hostname', 'N/A')}")
    lines.append(f"Fecha: {info.get('timestamp', 'N/A')}")

    lines.append("=" * 50)

    return "\n".join(lines)
