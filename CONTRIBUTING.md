# Guía de Contribución - Gurobipy-Simplex-General-Solver

¡Gracias por tu interés en contribuir!

Este documento proporciona lineamientos para contribuir a este proyecto.

## Inicio Rápido

1. Hacer fork del repositorio
2. Crear una rama de funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Hacer los cambios
4. Verificar funcionalidad
5. Hacer commit (`git commit -am 'Agregar nueva funcionalidad'`)
6. Push a la rama (`git push origin feature/nueva-funcionalidad`)
7. Crear un Pull Request

## Configuración de Desarrollo

```bash
# Clonar repositorio
git clone <url-del-fork>
cd gurobipy-simplex-general-solver

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install poetry
poetry install

# Instalar pre-commit hooks (opcional)
pre-commit install
```

## Estándares de Código

- **Lenguaje**: Python 3.12+
- **Docstrings**: Español (estándar del proyecto) — todas las funciones públicas deben tener docstring
- **Type hints**: Requerido para código nuevo y modificaciones
- **Formato**: Seguir estilo existente (ruff default)
- **Logging**: Usar `get_logger(__name__)` en vez de `print()` o `except: pass`

## Estilo de Código

```python
# Usar dataclasses para estructuras simples
@dataclass
class MiClase:
    atributo: str
    valor: int = 0

# Usar type hints
def mi_funcion(param: str) -> int:
    return len(param)

# Documentar en español
def mi_funcion(param: str) -> int:
    """
    Descripción de la función.

    Args:
        param: Descripción del parámetro.

    Returns:
        Descripción del valor de retorno.
    """
    pass
```

## Verificación

Antes de enviar, ejecutar:

```bash
# Tests unitarios con cobertura (requiere ≥90%)
pytest tests/ -v --cov=src --cov-fail-under=90

# Linting
ruff check src/ tests/

# Ejecutar test básico de integración
python -m src.cli data/problem.txt
python -m src.cli data/problem_multi.txt --multi
```

## Enviando Cambios

1. Asegurar que todo funcione (tests + linting)
2. Actualizar documentación si es necesario
3. Usar mensajes de commit claros en español o inglés
4. Crear un Pull Request contra la rama `develop`

### Política de PRs

- El título debe describir el cambio (ej: "Fix: NameError en benchmark.py")
- Incluir descripción del problema y solución
- Referenciar issues si aplica
- Mantener PRs pequeños y enfocados
- Asegurar que el CI pase (tests + lint + coverage ≥90%)
- No incluir cambios de formato no relacionados

## Reportando Problemas

Al reportar problemas:

1. Verificar que no haya sido reportado
2. Proporcionar pasos de reproducción
3. Incluir info del entorno (OS, Python, dependencias)
4. Adjuntar archivos de prueba si es posible

## Licencia

Al contribuir, aceptas que tus contribuciones estarán bajo la Licencia MIT.