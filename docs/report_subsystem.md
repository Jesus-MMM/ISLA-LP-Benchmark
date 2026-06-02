# Subsistema de Reportes Científicos

## Visión General

El subsistema `src/report/` es un motor de generación de reportes científicos **modular e impulsado por CSV**. Su objetivo es tomar definiciones de reporte en archivos CSV, resolver variables dinámicas (`{{variable}}`), aplicar localización (i18n) y estilos, y renderizar a múltiples formatos de salida: **PDF**, **HTML** y **Markdown**.

Está diseñado para separar completamente la **definición del contenido** (CSV) de la **lógica de renderizado**, permitiendo modificar la estructura del reporte sin tocar código Python.

---

## Arquitectura (Pipeline)

```
CSV de definición del reporte
         │
         ▼
  csv_loader.py  ──►  rows_to_elements()
         │
         ▼
  data_binding.py ──►  bind_data_to_model()   ──►  resuelve {{variables}} y {% condiciones %}
         │
         ▼
  i18n.py         ──►  get_text()              ──►  resuelve claves de traducción
         │
         ▼
  styles.py       ──►  StyleDefinition lookup  ──►  aplicación de temas/estilos
         │
         ▼
  DocumentModel (representación intermedia del documento)
         │
         ▼
  renderers/      ──►  render(model, output_path)
         │
         ▼
  PDF / HTML / Markdown
```

**Orquestador central:** `ReportEngine` en `engine.py` maneja todo el pipeline de principio a fin.

---

## Estructura del Módulo

```
src/report/
├── __init__.py           # Re-exporta tipos y excepciones públicas
├── engine.py              # ReportEngine — orquestador principal (API pública)
├── csv_loader.py          # Carga y parseo de archivos CSV de definición
├── data_binding.py        # Sustitución de {{variables}} y {% condiciones %}
├── i18n.py                # Localización (carga de traducciones CSV)
├── styles.py              # Sistema de estilos (carga desde CSV y defaults)
├── validation.py          # Validador de reportes (schema, estilos, i18n)
├── rich_text.py           # Parser de etiquetas inline [b]bold[/b], [color=#FF0000], etc.
├── apa.py                 # Utilidades de formato APA 7ma edición
│
├── core/                  # Tipos y excepciones fundamentales
│   ├── __init__.py
│   ├── types.py           # Data classes: ReportElement, DocumentModel, ContentType, ...
│   └── exceptions.py      # Excepciones: ReportError, CSVParseError, RenderError, ...
│
├── adapters/              # Puentes entre objetos de dominio y plantillas CSV
│   ├── __init__.py
│   ├── types.py           # ReportData — contenedor estándar de datos
│   ├── formatters.py      # Formateadores de bajo nivel (coeficientes, expresiones, etc.)
│   ├── single.py          # adapt_single_solution() — reporte de solución única
│   ├── multi.py           # adapt_multi_problem() — reporte multi-problema
│   └── benchmark.py       # adapt_benchmark() — reporte de benchmark comparativo
│
├── renderers/             # Renderizadores de salida
│   ├── __init__.py
│   ├── base.py            # BaseRenderer (abstracto) + RenderResult
│   ├── pdf.py             # PDFRenderer — renderizado a PDF con fpdf2
│   ├── html.py            # HTMLRenderer — renderizado a HTML
│   └── markdown.py        # MarkdownRenderer — renderizado a Markdown
│
└── templates/             # Plantillas de estilo específicas
    └── apa/
        └── pdf.py         # Renderizado PDF con estilo APA (extiende PDFRenderer)
```

---

## Conceptos Fundamentales

### ContentType (Enum)

Define 33 tipos de contenido que puede tener un elemento del reporte:

| Tipo | Descripción |
|------|-------------|
| `TITLE` | Título principal del documento |
| `SUBTITLE` | Subtítulo |
| `HEADING` | Encabezado de sección |
| `PARAGRAPH` | Párrafo de texto |
| `IMAGE` | Imagen |
| `TABLE` | Tabla de datos |
| `CHART` | Gráfico/figura |
| `SPACER` | Espaciado vertical |
| `CITATION` | Cita bibliográfica |
| `REFERENCE` | Referencia bibliográfica |
| `PAGE_BREAK` | Salto de página |
| `LIST` | Lista con items |
| `CODE_BLOCK` | Bloque de código |
| `FORMULA` | Fórmula matemática |
| `NOTE` | Nota aclaratoria |
| `FOOTER` | Pie de página |
| `HEADER` | Encabezado de página |
| `ABSTRACT` | Resumen |
| `CAPTION` | Leyenda de tabla/figura |
| `DATA_BLOCK` | Bloque de datos sin formato |
| `CUSTOM` | Elemento personalizado |

### ReportElement

Es la unidad básica de contenido del reporte. Cada fila del CSV se convierte en un `ReportElement`:

```python
@dataclass
class ReportElement:
    element_id: str                         # ID único
    content_type: ContentType               # Tipo (TITLE, PARAGRAPH, etc.)
    content: str                            # Contenido textual (con {{variables}})
    language: str = ""                       # Idioma del elemento
    style: str = "default"                  # Nombre del estilo a aplicar
    visible: bool = True                    # Visibilidad (puede ser condicional)
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list[ReportElement] = field(default_factory=list)
    condition: str = ""                     # Condición {% if var %} / {% unless var %}
    order: float = 0                        # Orden de aparición en el documento
```

### DocumentModel

Representación intermedia del documento completo, lista para renderizar:

```python
@dataclass
class DocumentModel:
    elements: list[ReportElement]
    page_config: PageConfig
    styles: dict[str, StyleDefinition]
    metadata: dict[str, Any]
    language: str = "en"
    title: str = ""
    author: str = ""
    date: str = ""
    references: list[ReferenceDefinition] = field(default_factory=list)
    citations: list[CitationDefinition] = field(default_factory=list)
```

### PageConfig

Configuración de geometría de página:

| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `page_width` | `int` | 216 | Ancho en mm (letter) |
| `page_height` | `int` | 279 | Alto en mm (letter) |
| `margin_top` | `int` | 25 | Margen superior en mm |
| `margin_bottom` | `int` | 25 | Margen inferior en mm |
| `margin_left` | `int` | 25 | Margen izquierdo en mm |
| `margin_right` | `int` | 25 | Margen derecho en mm |
| `page_numbers` | `bool` | True | Numeración de páginas |
| `header_enabled` | `bool` | True | Encabezado de página |
| `footer_enabled` | `bool` | False | Pie de página |
| `orientation` | `str` | "portrait" | "portrait" o "landscape" |
| `size` | `str` | "letter" | "letter", "legal", "a4" |

---

## API Pública: ReportEngine

`ReportEngine` es el punto de entrada principal. Su uso típico es:

```python
from src.report import ReportEngine

engine = ReportEngine(
    language="es",
    fallback_language="en",
    locale_dir="data/locale/",
    theme_dir="data/themes/",
    page_config=my_page_config,
)
engine.load_csv("data/report.csv")
engine.set_variables({"experiment_name": "Prueba A", "solver": "HiGHS"})
engine.render_pdf("output/reporte.pdf")
engine.render_html("output/reporte.html")
engine.render_markdown("output/reporte.md")
```

### Métodos Principales

| Método | Descripción |
|--------|-------------|
| `load_csv(path)` | Carga definiciones desde archivo CSV |
| `load_csv_string(content)` | Carga definiciones desde string CSV |
| `load_locale_dir(directory)` | Carga traducciones desde directorio |
| `load_theme_dir(directory)` | Carga estilos desde directorio |
| `set_variable(key, value)` | Asigna una variable para `{{key}}` |
| `set_variables(dict)` | Asigna múltiples variables |
| `set_references(list)` | Define lista de referencias bibliográficas |
| `add_style(name, style)` | Agrega/sobrescribe un estilo |
| `set_page_config(config)` | Configura la página |
| `set_metadata(key, value)` | Define metadato (título, autor, etc.) |
| `build_document_model()` | Construye el `DocumentModel` resuelto |
| `render_pdf(path)` | Renderiza a PDF |
| `render_html(path)` | Renderiza a HTML |
| `render_markdown(path)` | Renderiza a Markdown |
| `validate(strict=False)` | Valida el reporte completo |
| `get_diagnostics()` | Obtiene mensajes de diagnóstico |
| `clear_cache()` | Limpia cachés internas |

---

## Definición de Reportes en CSV

Cada fila del CSV define un elemento del reporte.

### Formato de columnas

| Columna | Requerido | Descripción |
|---------|-----------|-------------|
| `type` | Sí | Tipo de contenido (title, paragraph, table, etc.) |
| `id` | Sí | Identificador único del elemento |
| `content` | Sí | Contenido textual (puede incluir `{{variables}}` y etiquetas `[b]...[/b]`) |
| `style` | No | Nombre del estilo a aplicar (default: "default") |
| `language` | No | Idioma específico del elemento |
| `visible` | No | "true" o "false" |
| `condition` | No | Condición (`{% if var %}` o `{% unless var %}`) |
| `order` | No | Orden de aparición (decimal) |
| `metadata` | No | JSON con metadatos adicionales |

### Ejemplo

```csv
type,id,content,style,order
title,main_title,[b]Reporte de Experimentos[/b],title,1
paragraph,abstract,"Este reporte analiza los resultados de {{experiment_name}}.",body,2
heading,sec_intro,Introducción,heading,3
paragraph,p1,El experimento se ejecutó con el solver {{solver_name}}.,body,4
table,results_table,"{{results_headers}}|{{results_rows}}",apa_table,5
chart,prog_chart,Gráfico de progresión,body,6
page_break,pb1,,,7
heading,sec_conclusiones,Conclusiones,heading,8
```

---

## Data Binding (Sustitución de Variables)

El sistema soporta tres formas de interpolación:

### 1. Variables simples `{{variable}}`

```csv
content,El valor óptimo es {{objective_value}} y se resolvió en {{solve_time}} segundos.
```

Soporta notación de punto para acceso anidado:
```
{{result.status}}, {{config.solver.name}}
```

### 2. Condicionales `{% if var %}...{% end %}` y `{% unless var %}...{% end %}`

```csv
content,"{% if has_dual_values %}Los precios sombra están disponibles.{% end %}"
```

El elemento se marca como `visible=False` si la condición no se cumple, y se excluye del modelo final.

### 3. Variables en metadatos

Los metadatos también soportan interpolación:
```csv
metadata,"{""title"": ""Reporte de {{experiment_name}}""}"
```

### DataBinder

La clase `DataBinder` maneja el contexto de datos:

```python
binder = DataBinder()
binder.set_variable("solver_name", "HiGHS")
binder.set_variable("objective_value", "42.0000")
binder.set_variables({"solve_time": "0.13", "status": "OPTIMAL"})
binder.set_table("results", [["x", "1.0"], ["y", "2.0"]])
model = binder.bind(document_model)
```

---

## Localización (i18n)

El sistema de traducción usa archivos CSV:

```
key,en,es,fr
report.title,Experiment Report,Reporte de Experimentos,Rapport d'Expériences
solver.name,Solver Name,Nombre del Solver,Nom du Solveur
status.optimal,OPTIMAL,ÓPTIMO,OPTIMAL
```

### Comportamiento

1. Se carga el directorio de locales escaneando archivos `translations.csv`
2. `get_text(key, language, locale_dict, fallback)` busca:
   - Idioma solicitado → idioma de respaldo → cadena de respaldos → devuelve la clave misma
3. Las claves que comienzan con `#` se tratan como comentarios
4. El `ReportEngine` inyecta automáticamente la función de localización en el pipeline de binding

```python
engine = ReportEngine(language="es", fallback_language="en", locale_dir="data/locale/")
# Ahora todos los {{textos}} pasan por get_text() antes de resolver variables
```

---

## Sistema de Estilos

### Estilos integrados (14 default)

Creados por `create_default_styles()`:

`default`, `title`, `subtitle`, `heading`, `subheading`, `body`, `apa_table`, `apa_table_header`, `caption`, `image_caption`, `note`, `code`, `reference`, `footer`, `header`

### StyleDefinition

Cada estilo tiene 20 propiedades:

```python
@dataclass
class StyleDefinition:
    font_family: str = "Helvetica"
    font_size: int = 12
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str = "#000000"
    background_color: str = "#FFFFFF"
    alignment: str = "left"          # left, center, right, justify
    margin_top: int = 0
    margin_bottom: int = 0
    margin_left: int = 0
    margin_right: int = 0
    padding: int = 0
    border: bool = False
    border_color: str = "#000000"
    width: Optional[int] = None
    height: Optional[int] = None
    indent: int = 0
    line_height: float = 1.15
    spacing_before: int = 0
    spacing_after: int = 0
```

### Carga desde CSV (theme.csv)

```csv
section,name,property,value
style,title,font_family,Times
style,title,font_size,24
style,title,bold,true
style,title,alignment,center
style,title,margin_bottom,12
page,page_config,margin_top,25.4
page,page_config,page_numbers,true
```

Se cargan con:
```python
engine = ReportEngine(theme_dir="data/themes/")
# o
from src.report.styles import load_theme_dir
styles = load_theme_dir("data/themes/")
```

La resolución de estilos sigue esta cadena: nombre exacto → "default" → `StyleDefinition()` vacío.

---

## Renderizado

Cada renderizador hereda de `BaseRenderer` e implementa:

```python
def render(self, model: DocumentModel, output_path: str) -> RenderResult
```

### RenderResult

```python
@dataclass
class RenderResult:
    success: bool
    output_path: Optional[str]
    content: Optional[str]        # Para formatos string (HTML, Markdown)
    pages: int                    # Conteo de páginas (PDF)
    warnings: list[str]
    errors: list[str]
    metadata: dict[str, Any]
```

### PDFRenderer

- Usa la librería `fpdf2` (FPDF)
- Soporta todos los `ContentType`
- Procesa etiquetas rich text (`[b]`, `[i]`, `[color=]`, etc.) como spans con estilo
- Tablas con ancho de columna dinámico
- Imágenes desde rutas locales
- Saltos de página, encabezados y pies

### HTMLRenderer

- Genera documento HTML completo con CSS inline
- `render_to_string(model)` para obtener el HTML como string
- Convierte rich text a `<span>` con estilos CSS
- Tablas como `<table>` con estilos

### MarkdownRenderer

- Genera Markdown estándar
- `render_to_string(model)` para obtener el Markdown como string
- Usa `strip_tags()` para eliminar etiquetas rich text (Markdown maneja su propio formato)
- Tablas, listas, código, imágenes con sintaxis Markdown

### Uso directo de renderizadores

```python
from src.report import DocumentModel
from src.report.renderers import PDFRenderer

renderer = PDFRenderer()
result = renderer.render(model, "output.pdf")
print(f"Páginas: {result.pages}, Éxito: {result.success}")
```

---

## Adaptadores (Domain → ReportData)

Los adaptadores convierten objetos del dominio de resolución de problemas (LP) en `ReportData`, que alimenta las plantillas CSV.

### ReportData

```python
@dataclass
class ReportData:
    variables: dict[str, Any]                                  # Para {{variables}}
    tables: dict[str, tuple[list[str], list[list[str]]]]       # (headers, rows)
    images: dict[str, str]                                     # image_id → file_path
```

### Adaptadores Disponibles

| Función | Ubicación | Propósito | Variables que produce |
|---------|-----------|-----------|----------------------|
| `adapt_single_solution(problem, solution, ...)` | `adapters/single.py` | Reporte de solución única | `solver_name`, `objective_value`, `solve_time`, `status`, `problem_type`, `num_vars`, `num_constraints`, etc. |
| `adapt_multi_problem(results, ...)` | `adapters/multi.py` | Reporte multi-problema | `total_problems`, `success_count`, `fail_count`, `avg_solve_time`, etc. |
| `adapt_benchmark(runner, ...)` | `adapters/benchmark.py` | Comparativa de solvers | Tablas de rendimiento, métricas estadísticas, detección de outliers, matriz de correlación |

### Uso típico

```python
from src.report.adapters.single import adapt_single_solution

data = adapt_single_solution(
    problem=problem,
    solution=solution,
    execution_times=times,
    system_info=sys_info,
    solver_name="HiGHS",
)

engine = ReportEngine(language="es")
engine.load_csv("data/report_template.csv")
engine.set_variables(data.variables)
# Las tablas e imágenes se inyectan según el tipo de elemento en el CSV
engine.render_pdf("output.pdf")
```

---

## Validación

`ReportValidator` realiza estas comprobaciones:

| Verificación | Descripción |
|-------------|-------------|
| Schema CSV | IDs duplicados, tipos desconocidos, IDs faltantes |
| Estilos | Todos los estilos referenciados existen |
| Imágenes | Las rutas de imagen existen en disco (warning) |
| Localización | Todas las claves de traducción existen para los idiomas solicitados |

```python
engine = ReportEngine(language="es")
engine.load_csv("data/report.csv")
engine.set_variables(data.variables)
validator = engine.validate(strict=True)
print(validator.summary())
if validator.has_errors():
    print("Corrige los errores antes de renderizar.")
```

---

## Rich Text (Etiquetas Inline)

El parser `parse_rich_text()` procesa etiquetas dentro del contenido textual:

| Etiqueta | Significado |
|----------|-------------|
| `[b]texto[/b]` | Negrita |
| `[i]texto[/i]` | Cursiva |
| `[u]texto[/u]` | Subrayado |
| `[s]texto[/s]` | Tachado |
| `[sup]texto[/sup]` | Superíndice |
| `[sub]texto[/sub]` | Subíndice |
| `[color=#FF0000]texto[/color]` | Color |
| `[size=14]texto[/size]` | Tamaño de fuente |
| `[font=Arial]texto[/font]` | Tipografía |
| `[center]texto[center]` | Alineación centrada |
| `[right]texto[/right]` | Alineación derecha |
| `[list]...[item]...[item]...[/list]` | Lista |

Soporta anidamiento de etiquetas y modo estricto (lanza `TagParseError` si hay etiquetas mal formadas).

```python
from src.report.rich_text import parse_rich_text, strip_tags

styled = parse_rich_text("[b]Valor: [i]42.0[/i][/b]")
plain = strip_tags("[b]Valor: [i]42.0[/i][/b]")  # → "Valor: 42.0"
```

---

## Soporte APA (7ma Edición)

El módulo `src/report/apa.py` proporciona utilidades para generar reportes en formato APA:

```python
from src.report.apa import (
    create_apa_document,
    format_apa_reference,
    format_apa_citation,
    APA_PAGE_CONFIG,
    APA_STYLES,
)

doc = create_apa_document(
    title="Efectos del Algoritmo Genético en la Optimización LP",
    author="García, J.",
    institution="Universidad Nacional",
    running_header="OPTIMIZACIÓN LP",
    abstract="Este estudio analiza...",
    references=[ref1, ref2],
)
```

El template `templates/apa/pdf.py` contiene un renderizador PDF con estilos APA preconfigurados (Times New Roman 12pt, interlineado doble, márgenes de 1 pulgada, sangría de primera línea).

---

## Ejemplo Completo

```python
from src.report import ReportEngine
from src.report.apa import APA_PAGE_CONFIG
from src.report.adapters.single import adapt_single_solution

# 1. Obtener datos del dominio
solution_data = adapt_single_solution(
    problem=problem,
    solution=solution,
    execution_times=times,
    system_info=system_info,
    solver_name="HiGHS",
)

# 2. Configurar el motor
engine = ReportEngine(
    language="es",
    fallback_language="en",
    locale_dir="data/locale/",
    theme_dir="data/themes/",
    page_config=APA_PAGE_CONFIG,
)

# 3. Cargar definición del reporte
engine.load_csv("data/report_template.csv")

# 4. Inyectar datos
engine.set_variables(solution_data.variables)

# 5. Validar
validator = engine.validate()
if validator.has_errors():
    print(validator.summary())
else:
    # 6. Renderizar
    pdf_result = engine.render_pdf("output/reporte.pdf")
    html_result = engine.render_html("output/reporte.html")
    md_result = engine.render_markdown("output/reporte.md")
    print(f"PDF: {pdf_result.pages} páginas")
    print(f"HTML: {'éxito' if html_result.success else 'falló'}")
    print(f"Markdown: {'éxito' if md_result.success else 'falló'}")
```

---

## Extensibilidad

Para agregar un nuevo formato de salida:

1. Heredar de `BaseRenderer` en `renderers/`
2. Implementar `render(self, model, output_path) -> RenderResult`
3. Opcionalmente implementar `render_to_string(self, model) -> str`
4. Registrar en `renderers/__init__.py`
5. Agregar método en `ReportEngine` (ej: `render_latex(path)`)

Para agregar un nuevo tipo de contenido:

1. Agregar valor al enum `ContentType` en `core/types.py`
2. Implementar renderizado en cada renderizador
3. Agregar mapeo en `csv_loader.py` si se usa desde CSV
