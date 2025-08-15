"""
Controlador de Tareas - Maneja la lógica de negocio de las tareas

Este archivo contiene todas las rutas y lógica relacionada con las tareas.
Representa la capa "Controlador" en la arquitectura MVC.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from models.task import Task, LOCAL_TZ
from models.task import Task
from extensions import db
import re # Para trabajar con expresiones regulares o secuencia de caracteres que define un patrón de búsqueda en un texto.


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
        filter_type = request.args.get('filter', 'all')
        sort_by = request.args.get('sort', 'created')

        # Obtener tareas según filtro
        if filter_type == 'pending':
            tasks = Task.get_pending_tasks(order_by=sort_by)
        elif filter_type == 'completed':
            tasks = Task.get_completed_tasks(order_by=sort_by)  # Usar método corregido
        elif filter_type == 'overdue':
            tasks = Task.get_overdue_tasks(order_by=sort_by)
        else:
            tasks = Task.get_all_tasks(order_by=sort_by)

        # Contadores actualizados
        total = Task.query.count()
        pending_count = Task.get_pending_tasks_count()
        completed_count = Task.get_completed_tasks_count()
        overdue_count = Task.get_overdue_tasks_count()

        context = {
            'tasks': tasks,
            'filter_type': filter_type,
            'sort_by': sort_by,
            'total_tasks': total,
            'pending_count': pending_count,
            'completed_count': completed_count
        }
        # Añadimos la zona local y la hora local actual al contexto de la plantilla
        context.update({
            'LOCAL_TZ': LOCAL_TZ,
            'now_local': datetime.now(LOCAL_TZ).replace(microsecond=0)
        })
        return render_template('task_list.html', **context)
 
    
    def _parse_due_date_flexible(date_str):
        """
        Parseando diferentes formatos de fecha y hora.
        Soporta:
        - 'YYYY-MM-DD'
        - 'YYYY-MM-DDTHH:MM' (datetime-local)
        - 'DD/MM/YYYY HH:MM a. m.' o 'dd/mm/yyyy hh:mm p. m.' (español)
        - 'DD/MM/YYYY' (solo fecha)
        Devuelve datetime (sin microsegundos) o None si no puede parsear.
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
            '%Y-%m-%d %H:%M:%S.%f',  # 2025-08-11 01:20:00.000000
        ]
        
        parsed_date = None
        
        # Primero intentar con formatos estándar
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue

        # Si no funcionó, intentar parseo heurístico
        if not parsed_date:
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
                parsed_date = datetime(int(yyyy), int(mm), int(dd), hh, int(minute))
        
        # Si se obtuvo una fecha válida, truncar microsegundos y adjuntar zona local
        if parsed_date:
            return parsed_date.replace(microsecond=0, tzinfo=LOCAL_TZ)
        
        return None
    
    
    @app.route('/tasks/new', methods=['GET', 'POST'])
    def task_create():
        """
        Creando una nueva tarea usando el metodo 'Get' y 'Post'
        GET: Muestra el formulario de creación
        POST: Procesa los datos del formulario y crea la tarea
        """
        if request.method == 'POST':
            # Leer campos del formulario (proteger contra None)
            title = (request.form.get('title') or '').strip()
            description = (request.form.get('description') or '').strip()
            due_date_str = (request.form.get('due_date') or '').strip()
            
            # --- LEER EL CHECKBOX ---
            completed_val = request.form.get('completed')  # si está marcado -> 'on'
            completed = True if completed_val in ('on', 'true', '1', 'yes') else False

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
                return render_template('task_form.html', form=form, LOCAL_TZ=LOCAL_TZ, now_local=datetime.now(LOCAL_TZ))
            
            if due_date:
                # Forzar truncamiento de microsegundos
                due_date = due_date.replace(microsecond=0)

                # Validación: no permitir fechas de días anteriores.
                # Permitimos cualquier fecha cuyo día sea el de hoy (incluso si la hora ya pasó).
                # Usar hora local para validación
                now = datetime.now(LOCAL_TZ).replace(microsecond=0)
                if due_date.date() < now.date():
                    flash('La fecha de vencimiento no puede ser de días anteriores. Si quieres usar hoy, selecciona la fecha de hoy.', 'error')
                    form = {'title': title, 'description': description, 'due_date': due_date_str}
                    return render_template('task_form.html', form=form, LOCAL_TZ=LOCAL_TZ, now_local=now)
                
            # Crear objeto Task y asignar completed antes de guardar
            task = Task(title=title, description=description or None, due_date=due_date)
            task.completed = completed 
            
            try:
                db.session.add(task)
                db.session.commit()
                flash('Tarea creada correctamente.', 'success')
                return redirect(url_for('task_list'))
            except Exception:
                db.session.rollback()
                flash('Ocurrió un error al crear la tarea. Intente nuevamente.', 'error')
                form = {'title': title, 'description': description, 'due_date': due_date_str}
                return render_template('task_form.html', form=form, LOCAL_TZ=LOCAL_TZ, now_local=datetime.now(LOCAL_TZ))
 

        # GET -> Mostrar formulario vacío
        return render_template('task_form.html', LOCAL_TZ=LOCAL_TZ, now_local=datetime.now(LOCAL_TZ))
    
    
    @app.route('/tasks/<int:task_id>')
    def task_detail(task_id):
        """
        Muestra los detalles de una tarea específica
        
        Args:
            task_id (int): ID de la tarea a mostrar
        
        Returns:
            str: HTML con los detalles de la tarea
        """
        
        task = Task.query.get_or_404(task_id)
        return render_template('task_detail.html', task=task, LOCAL_TZ=LOCAL_TZ)

    
    
    @app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
    def task_edit(task_id):
        """
        Edita una tarea existente

        GET: Muestra el formulario de edición con datos actuales
        POST: Procesa los cambios y actualiza la tarea
        """
        task = Task.query.get_or_404(task_id)

        if request.method == 'POST':
            # Leer campos del formulario (proteger contra None)
            title = (request.form.get('title') or '').strip()
            description = (request.form.get('description') or '').strip()
            due_date_str = (request.form.get('due_date') or '').strip()
            completed_val = request.form.get('completed')  # checkbox -> 'on' si está marcado
            completed = True if completed_val in ('on', 'true', '1', 'yes') else False

            # Validaciones básicas
            if not title:
                flash('El título es obligatorio.', 'error')
                form = {'title': title, 'description': description, 'due_date': due_date_str, 'completed': completed}
                return render_template('task_form.html', task=task, edit=True, form=form)

            # Parsear fecha si fue proporcionada
            due_date = _parse_due_date_flexible(due_date_str)
            if due_date_str and due_date is None:
                flash('Formato de fecha inválido. Use YYYY-MM-DD (o seleccione la fecha correctamente).', 'error')
                form = {'title': title, 'description': description, 'due_date': due_date_str, 'completed': completed}
                return render_template('task_form.html', task=task, edit=True, form=form, LOCAL_TZ=LOCAL_TZ, now_local=datetime.now(LOCAL_TZ))
            
            # Forzar truncamiento de microsegundos
            if due_date:
                due_date = due_date.replace(microsecond=0)  

            # Aplicar cambios al objeto
            task.title = title
            task.description = description or None
            task.due_date = due_date
            task.completed = completed

            try:
                db.session.add(task)
                db.session.commit()
                flash('Tarea actualizada correctamente.', 'success')
                return redirect(url_for('task_detail', task_id=task.id))
            except Exception:
                db.session.rollback()
                flash('Ocurrió un error al actualizar la tarea. Intente nuevamente.', 'error')
                form = {'title': title, 'description': description, 'due_date': due_date_str, 'completed': completed}
                return render_template('task_form.html', task=task, edit=True, form=form, LOCAL_TZ=LOCAL_TZ, now_local=datetime.now(LOCAL_TZ))

        # GET: Mostrar el formulario de edición
        return render_template('task_form.html', task=task, edit=True, LOCAL_TZ=LOCAL_TZ, now_local=datetime.now(LOCAL_TZ))

    
    
    @app.route('/tasks/<int:task_id>/delete', methods=['POST'])
    def task_delete(task_id):
        """
        Elimina una tarea
        
        Args:
            task_id (int): ID de la tarea a eliminar
        
        Returns:
            Response: Redirección a la lista de tareas
        """
        task = Task.query.get_or_404(task_id)

        try:
            db.session.delete(task)
            db.session.commit()
            mensaje = 'Tarea eliminada correctamente.'

            # Si la petición es JSON/AJAX, devolver JSON útil
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': mensaje}), 200

            flash(mensaje, 'success')
        except Exception:
            db.session.rollback()
            mensaje = 'Ocurrió un error al eliminar la tarea. Intente nuevamente.'

            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': mensaje}), 500

            flash(mensaje, 'error')

        return redirect(url_for('task_list'))
    
    
    @app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
    def task_toggle(task_id):
        """
        Cambia el estado de completado de una tarea
        
        Args:
            task_id (int): ID de la tarea a cambiar
        
        Returns:
            Response: Redirección a la lista de tareas
        """
        # Obtener la tarea por ID
        task = Task.query.get_or_404(task_id)
        """
        Cambiar el estado de completado
        Si la tarea ya está completada, la marcamos como pendiente y viceversa
        """
        try:
            was_completed = task.completed
            task.completed = not was_completed
            db.session.commit()
            
            # Mensaje de éxito
            mensaje = 'Tarea marcada como completada.' if task.completed else 'Tarea marcada como pendiente.'
            
            # Si la petición es JSON/AJAX, devolver JSON útil
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'completed': task.completed,
                    'is_overdue': task.is_overdue() if not task.completed else False,
                    'pending_count': len(Task.get_pending_tasks()),
                    'completed_count': len(Task.get_completed_tasks())
                }), 200
                
            flash(mensaje, 'success')
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False, 
                    'message': f'Error: {str(e)}'
                }), 500
            flash('Error al cambiar estado', 'error')
        return redirect(url_for('task_list'))    
    
    # Rutas adicionales para versiones futuras
    
    @app.route('/api/tasks', methods=['GET'])
    def api_tasks():
        """
        Endpoint API para obtener todas las tareas en formato JSON
        
        Query Parameters:
            filter (str): 'all' | 'pending' | 'completed' | 'overdue'
            sort (str): 'date' | 'title' | 'created'
        
        Returns:
            json: Lista de tareas con estructura completa
        """
        # Obtener parámetros de consulta
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
        
        # Convertir tareas a formato JSON
        tasks_json = [task.to_dict() for task in tasks]
        
        # Devolver respuesta JSON
        return jsonify({
            'success': True,
            'count': len(tasks_json),
            'tasks': tasks_json,
            'filter': filter_type,
            'sort': sort_by
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

