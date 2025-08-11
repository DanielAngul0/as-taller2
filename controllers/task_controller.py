"""
Controlador de Tareas - Maneja la lógica de negocio de las tareas

Este archivo contiene todas las rutas y lógica relacionada con las tareas.
Representa la capa "Controlador" en la arquitectura MVC.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from models.task import Task
from extensions import db
import re 


def register_routes(app):
    """
    Registra todas las rutas del controlador de tareas en la aplicación Flask
    
    Args:
        app (Flask): Instancia de la aplicación Flask
    """
    
    @app.route('/')
    def index():
        """
        Ruta principal - Redirige a la lista de tareas
        
        Returns:
            Response: Redirección a la lista de tareas
        """
        return redirect(url_for('task_list'))
    
    
    @app.route('/tasks')
    def task_list():
        """
        Muestra la lista de todas las tareas.

        Query Parameters:
            filter (str): 'all' | 'pending' | 'completed' | 'overdue'
            sort (str): 'date' | 'title' | 'created'
        """
        filter_type = request.args.get('filter', 'all')
        sort_by = request.args.get('sort', 'created')

        # Obtener tareas según filtro
        if filter_type == 'pending':
            tasks = Task.get_pending_tasks(order_by=sort_by)
        elif filter_type == 'completed':
            tasks = Task.get_completed_tasks(order_by=sort_by)
        elif filter_type == 'overdue':
            tasks = Task.get_overdue_tasks(order_by=sort_by)
        else:
            tasks = Task.get_all_tasks(order_by=sort_by)

        # Contadores
        total = len(Task.get_all_tasks())
        pending_count = len(Task.get_pending_tasks())
        completed_count = len(Task.get_completed_tasks())

        context = {
            'tasks': tasks,
            'filter_type': filter_type,
            'sort_by': sort_by,
            'total_tasks': total,
            'pending_count': pending_count,
            'completed_count': completed_count
        }
        return render_template('task_list.html', **context)
 
    
    def _parse_due_date_flexible(date_str):
        """
        Intenta parsear diferentes formatos que puedes recibir:
        - 'YYYY-MM-DD'
        - 'YYYY-MM-DDTHH:MM' (datetime-local)
        - 'DD/MM/YYYY HH:MM a. m.' o 'dd/mm/yyyy hh:mm p. m.' (español)
        - 'DD/MM/YYYY' (solo fecha)
        Devuelve datetime o None si no puede parsear.
        """
        if not date_str:
            return None
        s = date_str.strip()

        # Normalizar AM/PM en español a 'AM'/'PM'
        s = re.sub(r'\ba\.?\s?m\.?\b', 'AM', s, flags=re.IGNORECASE)
        s = re.sub(r'\bp\.?\s?m\.?\b', 'PM', s, flags=re.IGNORECASE)

        # Intentos de parseo en orden de probabilidad
        formats = [
            '%Y-%m-%d',           # 2025-08-11
            '%Y-%m-%dT%H:%M',     # 2025-08-11T01:20 (datetime-local)
            '%d/%m/%Y %H:%M',     # 11/08/2025 01:20
            '%d/%m/%Y %I:%M %p',  # 11/08/2025 01:20 AM/PM
            '%d/%m/%Y',           # 11/08/2025
            '%Y-%m-%d %H:%M:%S',  # 2025-08-11 01:20:00
        ]
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue

        # Si ninguno funcionó, intentar parseo heurístico simple (hora al final con AM/PM)
        # ej: "11/08/2025 1:20 AM" (sin cero a la izquierda en la hora)
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)?', s, flags=re.IGNORECASE)
        if m:
            dd, mm, yyyy, hh, minute, ampm = m.groups()
            hh = int(hh)
            if ampm:
                ampm = ampm.upper()
                if ampm == 'PM' and hh < 12:
                    hh += 12
                if ampm == 'AM' and hh == 12:
                    hh = 0
            return datetime(int(yyyy), int(mm), int(dd), hh, int(minute))

        # no pudo parsear
        return None
    
    
    @app.route('/tasks/new', methods=['GET', 'POST'])
    def task_create():
        """
        Crea una nueva tarea

        GET: Muestra el formulario de creación
        POST: Procesa los datos del formulario y crea la tarea
        """
        if request.method == 'POST':
            # Leer campos del formulario (proteger contra None)
            title = (request.form.get('title') or '').strip()
            description = (request.form.get('description') or '').strip()
            due_date_str = (request.form.get('due_date') or '').strip()

            # Validaciones básicas
            if not title:
                flash('El título es obligatorio.', 'error')
                form = {'title': title, 'description': description, 'due_date': due_date_str}
                return render_template('task_form.html', form=form)

            # Parsear fecha si fue proporcionada (formato YYYY-MM-DD)
            due_date = _parse_due_date_flexible(due_date_str)
            if due_date_str and due_date is None:
                flash('Formato de fecha inválido. Use YYYY-MM-DD (o seleccione la fecha correctamente).', 'error')
                form = {'title': title, 'description': description, 'due_date': due_date_str}
                return render_template('task_form.html', form=form)

            # Crear objeto Task y persistir en la base de datos
            task = Task(title=title, description=description or None, due_date=due_date)
            try:
                db.session.add(task)
                db.session.commit()
                flash('Tarea creada correctamente.', 'success')
                return redirect(url_for('task_list'))
            except Exception:
                db.session.rollback()
                flash('Ocurrió un error al crear la tarea. Intente nuevamente.', 'error')
                form = {'title': title, 'description': description, 'due_date': due_date_str}
                return render_template('task_form.html', form=form)

        # GET -> Mostrar formulario vacío
        return render_template('task_form.html')
    
    
    @app.route('/tasks/<int:task_id>')
    def task_detail(task_id):
        """
        Muestra los detalles de una tarea específica
        
        Args:
            task_id (int): ID de la tarea a mostrar
        
        Returns:
            str: HTML con los detalles de la tarea
        """
        pass # TODO: implementar el método
    
    
    @app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
    def task_edit(task_id):
        """
        Edita una tarea existente
        
        Args:
            task_id (int): ID de la tarea a editar
        
        GET: Muestra el formulario de edición con datos actuales
        POST: Procesa los cambios y actualiza la tarea
        
        Returns:
            str: HTML del formulario o redirección tras editar
        """
        if request.method == 'POST':
            pass # TODO: implementar para una solicitud POST
        
        # Mostrar el formulario para editar la tarea
        pass # TODO: implementar para una solicitud GET
    
    
    @app.route('/tasks/<int:task_id>/delete', methods=['POST'])
    def task_delete(task_id):
        """
        Elimina una tarea
        
        Args:
            task_id (int): ID de la tarea a eliminar
        
        Returns:
            Response: Redirección a la lista de tareas
        """
        pass # TODO: implementar el método
    
    
    @app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
    def task_toggle(task_id):
        """
        Cambia el estado de completado de una tarea
        
        Args:
            task_id (int): ID de la tarea a cambiar
        
        Returns:
            Response: Redirección a la lista de tareas
        """
        pass # TODO: implementar el método
    
    
    # Rutas adicionales para versiones futuras
    
    @app.route('/api/tasks', methods=['GET'])
    def api_tasks():
        """
        API endpoint para obtener tareas en formato JSON
        (Para versiones futuras con JavaScript)
        
        Returns:
            json: Lista de tareas en formato JSON
        """
        # TODO: para versiones futuras
        return jsonify({
            'tasks': [],
            'message': 'API en desarrollo - Implementar en versiones futuras'
        })
    
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Maneja errores 404 - Página no encontrada"""
        return render_template('404.html'), 404
    
    
    @app.errorhandler(500)
    def internal_error(error):
        """Maneja errores 500 - Error interno del servidor"""
        db.session.rollback()
        return render_template('500.html'), 500

