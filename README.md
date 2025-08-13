## Autor
### Estudiante: Daniel Andres Angulo Perez

## [@DanielAngul0](https://github.com/DanielAngul0)

# taller #2 de Arquitectura de Software: MVC

## Descripción

Este proyecto proporciona una plantilla para la implementación de una aplicación web siguiendo el patrón **Modelo** - **Vista** - **Controlador** (**MVC**)

## Objetivos

1. **Comprender la arquitectura Modelo-Vista-Controlador** en el desarrollo de una aplicación Web:
    - **Modelo**: Definir clases con SQLAlchemy y gestionar datos
    - **Vista**: Diseñar plantillas HTML con Jinja2 para representar información
    - **Controlador**: Implementar rutas y lógica de interacción en Flask
2. **Implementar operaciones CRUD** conectadas a una base de datos relacional
3. **Usar el ORM SQLAlchemy** para manipular objetos sin escribir SQL directamente
4. **Aplicar principios de separación de responsabilidades** y organización de código
5. **Comprender el flujo de una petición HTTP** dentro de una aplicación web MVC
6. **Desarrollar una aplicación básica** con persistencia, interfaz web y lógica de negocio estructurada
## Autor
### Estudiante: Daniel Andres Angulo Perez

## [@DanielAngul0](https://github.com/DanielAngul0)


## Estructura del Proyecto

```
as-taller2/
├── .gitignore              # Archivos a ignorar en Git
├── app.py                  # Punto de entrada y configuración
├── config.py               # Configuración de Flask y SQLAlchemy
├── models/                 # Modelo (clases SQLAlchemy)
│   ├── __init__.py
│   └── task.py             # Clase Tarea con atributos y métodos
├── controllers/            # Controladores (rutas y lógica de negocio)
│   ├── __init__.py
│   └── task_controller.py  # CRUD de tareas
├── templates/              # Vistas (HTML con Jinja2)
│   ├── layout.html         # Base común
│   ├── task_list.html      # Lista de tareas
│   ├── task_form.html      # Formulario de crear/editar
│   ├── task_detail.html    # Interfaz de detalles de tareas (Solo las que se editen)
│   └── 404.html            # Interfaz de pagina no encontrada
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
│   └── style.css           # Hoja de estilos
├── extensions.py           # Crean y centraliza las instancias de las extensiones de Flask
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Este archivo
```

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/UR-CC/as-taller2.git
cd as-taller2

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Desarrollo por Versiones

### Versión 1: CRUD Local con Flask + SQLAlchemy

**Objetivo**: Implementar las operaciones básicas CRUD

- [ ] Crear una tarea: título, descripción, estado (pendiente/hecha), fecha de vencimiento
- [ ] Leer (listar) todas las tareas
- [ ] Editar una tarea existente
- [ ] Eliminar una tarea

**Archivos a modificar**: `models/task.py`, `controllers/task_controller.py`, `templates/*.html`

### Versión 2: Validaciones y Mejoras en la Vista

**Objetivo**: Agregar validaciones y mejorar la presentación

- [ ] Validación básica en formularios (campos requeridos, fecha válida)
- [ ] Plantillas Jinja reutilizables usando `layout.html`
- [ ] Estilos básicos con CSS o Bootstrap

**Archivos a modificar**: `templates/*.html`, `static/style.css`, `controllers/task_controller.py`

### Versión 3: Filtros y Mejoras de Usabilidad

**Objetivo**: Añadir funcionalidades de filtrado y ordenamiento

- [ ] Filtrar tareas por estado (pendiente, completada)
- [ ] Ordenar tareas por fecha de vencimiento
- [ ] Mostrar tareas vencidas en otro color

**Archivos a modificar**: `controllers/task_controller.py`, `templates/task_list.html`, `static/style.css`

### Versión 4: Autenticación de Usuarios (Opcional)

**Objetivo**: Agregar sistema de usuarios

- [ ] Registro e inicio de sesión de usuarios
- [ ] Asociar tareas a usuarios específicos
- [ ] Proteger rutas con autenticación

**Archivos nuevos**: `models/user.py`, `controllers/auth_controller.py`, plantillas de autenticación

## Tecnologías Utilizadas

- [Flask](https://flask.palletsprojects.com/en/stable/): Framework web de Python
- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/): ORM para manejo de base de datos
- [Jinja](https://jinja.palletsprojects.com/en/stable/): Motor de plantillas (incluido con Flask)
- [SQLite](https://www.sqlite.org/docs.html): Base de datos ligera para desarrollo
- [HTML](https://lenguajehtml.com/)/[CSS](https://lenguajecss.com): Para la interfaz de usuario

