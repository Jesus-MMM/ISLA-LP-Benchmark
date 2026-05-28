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

## Versionado Semántico (SemVer)

Este proyecto utiliza **Versionado Semántico (SemVer)**: `MAJOR.MINOR.PATCH`

### Formato de Commits (Conventional Commits)

Los mensajes de commit deben seguir el estándar para automatizar el versionado:

```
<tipo>(<alcance>): <descripción>

<cuerpo>
<pie>
```

#### Tipos de commit y versionado asociado:

| Tipo | Versión | Ejemplo |
|------|---------|---------|
| `feat:` | **MINOR** ↑ | `feat(solver): agregar nuevo algoritmo` |
| `fix:` | **PATCH** ↑ | `fix(parser): corregir error de parseo LP` |
| `feat!:` | **MAJOR** ↑ | `feat!(api): cambiar estructura de respuesta` |
| `perf:` | **PATCH** ↑ | `perf(benchmark): optimizar cálculos` |
| `docs:` | Sin cambio | `docs: actualizar README` |
| `style:` | Sin cambio | `style: formatear código con ruff` |
| `refactor:` | Sin cambio | `refactor(core): reorganizar módulos` |
| `test:` | Sin cambio | `test(solver): agregar casos de prueba` |
| `chore:` | Sin cambio | `chore: actualizar dependencias` |

#### Ejemplos válidos:

```bash
# Feature nueva (MINOR: 1.8.1 → 1.9.0)
git commit -m "feat(solver): agregar soporte para MILP"

# Bug fix (PATCH: 1.8.1 → 1.8.2)
git commit -m "fix(parser): corregir parsing de restricciones vacías"

# Breaking change (MAJOR: 1.8.1 → 2.0.0)
git commit -m "feat(api)!: cambiar formato de entrada de problemas"

# Sin impacto en versión
git commit -m "docs: mejorar guía de usuario"
```

### Proceso de Release

#### 1. Para desarrolladores (crear nueva versión):

```bash
# Asegurarse de estar en main y sincronizado
git checkout main
git pull origin main

# Ejecutar script de bump
./scripts/bump-version.sh minor   # o major/patch

# El script:
# - Actualiza pyproject.toml
# - Regenera requirements.txt
# - Crea commit
# - Crea tag v1.9.0
# - Muestra instrucciones de push

# Push de cambios y tag
git push origin
git push origin v1.9.0
```

#### 2. GitHub Actions (automático):

- Detecta nuevo tag `v*`
- Valida que coincida con `pyproject.toml`
- Genera changelog automáticamente desde commits
- Crea Release en GitHub
- Construye y publica imagen Docker con etiquetas:
  - `v1.9.0` (semver exact)
  - `1.9` (major.minor)
  - `latest` (si es en main)
  - `sha-abc123` (commit)

### Ramas y versionado

- **`main`**: Rama de producción. Tags v* aquí crean releases estables
- **`Debug`**: Rama de desarrollo. Para PRs y testing
- **feature/\***: Ramas de features. Se mezclan en Debug

### Checklist antes de release

- [ ] Todos los tests pasan: `pytest tests/ -v --cov=src --cov-fail-under=90`
- [ ] Linting correcto: `ruff check src/ tests/`
- [ ] Commits siguen Conventional Commits
- [ ] CHANGELOG.md actualizado (opcional pero recomendado)
- [ ] Versión en `pyproject.toml` es correcta
- [ ] requirements.txt regenerado con pip-tools

### Herramientas útiles

**Instalar pip-tools** (para regenerar requirements.txt):
```bash
pip install pip-tools
pip-compile pyproject.toml --output-file=requirements.txt
```

**Ver commits sin push:**
```bash
git log origin/main..HEAD
```

**Ver últimos tags:**
```bash
git tag -l --sort=-version:refname | head -5
```
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