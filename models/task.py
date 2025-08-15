"""
Modelo Task - Representa una tarea en la base de datos

Este archivo contiene la definición del modelo Task usando SQLAlchemy ORM.
"""
from sqlalchemy import TypeDecorator
from sqlalchemy import event
from sqlalchemy.types import DateTime
from datetime import datetime
from zoneinfo import ZoneInfo
from extensions import db 

class DateTimeWithoutMicroseconds(TypeDecorator):
    """Tipo personalizado para almacenar fechas sin microsegundos"""
    impl = db.String(26)  # Longitud suficiente para incluir microsegundos
    
# Zona local usada para interpretar/normalizar fechas
LOCAL_TZ = ZoneInfo('America/Chicago')

class DateTimeWithoutMicroseconds(TypeDecorator):
    """Tipo personalizado para almacenar fechas en ISO (sin microsegundos) y con zona."""
    impl = db.String(40)  # suficiente para 'YYYY-MM-DDTHH:MM:SS+HH:MM'
    
    def process_bind_param(self, value, dialect):
        """
        Acepta datetime y str:
        - Si es datetime: normaliza a zona local (LOCAL_TZ) y devuelve string 'YYYY-MM-DD HH:MM:SS'
        - Si es str: intenta parsear ISO o formato legacy y devuelve string normalizado
        - Si es None devuelve None
        """
        if value is None:
            return None

        # Si ya es string, intentar parsearlo a datetime y normalizar
        if isinstance(value, str):
            try:
                # Intento parsear ISO primero (soporta offsets)
                dt = datetime.fromisoformat(value)
            except Exception:
                # Compatibilidad con formato legacy "YYYY-MM-DD HH:MM:SS" (sin microsegundos)
                try:
                    s = value
                    if '.' in s:
                        s = s.split('.')[0]
                    dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    # Si no se puede parsear, devolver tal cual (fallback)
                    return value
            # Si dt no tiene tz, asumimos LOCAL_TZ; luego normalizamos y devolvemos string
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=LOCAL_TZ)
            dt = dt.astimezone(LOCAL_TZ).replace(microsecond=0)
            return dt.strftime('%Y-%m-%d %H:%M:%S')

        # Si es datetime: asegurarse tz-aware (asumir LOCAL_TZ si es naive) y formatear
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=LOCAL_TZ)
            v = value.astimezone(LOCAL_TZ).replace(microsecond=0)
            return v.strftime('%Y-%m-%d %H:%M:%S')

        # Fallback: convertir a str
        try:
            return str(value)
        except Exception:
            return None
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Manejar diferentes formatos guardados; devolver datetime con tz LOCAL_TZ
        try:
            # Intentar ISO (aunque guardamos legacy, esto hace la función robusta)
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=LOCAL_TZ)
            return dt
        except Exception:
            # Formato legacy "YYYY-MM-DD HH:MM:SS"
            if '.' in value:
                value = value.split('.')[0]
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt.replace(tzinfo=LOCAL_TZ)

class Task(db.Model):
    """
    Modelo para representar una tarea en la aplicación To-Do
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = 'tasks'
    
    # Definición de columnas
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    due_date = db.Column(DateTimeWithoutMicroseconds(), nullable=True)
    created_at = db.Column(DateTimeWithoutMicroseconds(), 
                          default=lambda: datetime.now(LOCAL_TZ).replace(microsecond=0),
                          nullable=False)
    updated_at = db.Column(DateTimeWithoutMicroseconds(), 
                          default=lambda: datetime.now(LOCAL_TZ).replace(microsecond=0),
                          onupdate=lambda: datetime.now(LOCAL_TZ).replace(microsecond=0),
                          nullable=False)
    
    def __init__(self, title, description=None, due_date=None):
        """
        Constructor del modelo Task
        
        Args:
            title (str): Título de la tarea
            description (str, optional): Descripción de la tarea
            due_date (datetime, optional): Fecha de vencimiento
        """
        self.title = title
        self.description = description
        self.due_date = due_date
        self.completed = False
    
    def __repr__(self):
        """Representación en string del objeto Task"""
        return f'<Task {self.id}: {self.title}>'
    
    def to_dict(self):
        """
        Convierte el objeto Task a un diccionario

        Returns:
            dict: Diccionario con los datos de la tarea
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def is_overdue(self):
        """
        Verifica si la tarea está vencida
        
        Returns:
            bool: True si la tarea está vencida, False en caso contrario
        """
        # Si no hay fecha de vencimiento, no puede estar vencida
        if not self.due_date:
            return False

        # Si ya está completada, no considerarla vencida
        if self.completed:
            return False

        now = datetime.now(LOCAL_TZ).replace(microsecond=0)
        due = self.due_date
        # Asegurar que due tiene tzinfo
        if due is not None and due.tzinfo is None:
            due = due.replace(tzinfo=LOCAL_TZ)
        return due < now
    
    def mark_completed(self, commit=True):
        """Marca la tarea como completada"""
        self.completed = True
        self.updated_at = datetime.utcnow().replace(microsecond=0)
        if commit:
            self.save()
    
    def mark_pending(self, commit=True):
        """Marca la tarea como pendiente"""
        self.completed = False
        self.updated_at = datetime.utcnow().replace(microsecond=0)
        if commit:
            self.save()
    
    @staticmethod
    def get_all_tasks(order_by=None):
        """
        Obtiene todas las tareas de la base de datos.
        Permite ordenar los resultados por fecha de vencimiento, título o fecha de creación.

        :return: Lista de todas las tareas.
        """
        # Comienza consultando todas las tareas
        query = Task.query

        # Ordena las tareas según el criterio indicado
        if order_by == 'date':
            query = query.order_by(Task.due_date.asc())  # Orden ascendente por fecha de vencimiento
        elif order_by == 'title':
            query = query.order_by(Task.title.asc())     # Orden alfabético por título
        elif order_by == 'created':
            query = query.order_by(Task.created_at.desc())  # Orden descendente por fecha de creación

        # Devuelve la lista completa de tareas
        return query.all()

    @staticmethod
    def get_completed_tasks(order_by=None):
        """
        Obtiene todas las tareas completadas.
        Permite ordenar los resultados por fecha de vencimiento, título o fecha de creación.
        """
        query = Task.query.filter_by(completed=True)

        if order_by == 'date':
            query = query.order_by(Task.due_date.asc())
        elif order_by == 'title':
            query = query.order_by(Task.title.asc())
        elif order_by == 'created':
            query = query.order_by(Task.created_at.desc())
            
        # Devuelve la lista de tareas completadas
        return query.all()

    @staticmethod
    def get_pending_tasks(order_by=None):
        """
        Obtiene todas las tareas pendientes (no completadas).
        Permite ordenar los resultados por fecha de vencimiento, título o fecha de creación.
        """
        # Filtra las tareas pendientes (no completadas y no vencidas)  
        now = datetime.now(LOCAL_TZ)
        query = Task.query.filter(
            Task.completed == False,
            (Task.due_date == None) | (Task.due_date >= now)
        )

        # Ordena las tareas según el criterio indicado
        if order_by == 'date':
            query = query.order_by(Task.due_date.asc())
        elif order_by == 'title':
            query = query.order_by(Task.title.asc())
        elif order_by == 'created':
            query = query.order_by(Task.created_at.desc())

        # Devuelve la lista de tareas pendientes
        return query.all()

    def get_overdue_tasks(order_by=None):
        """
        Obtiene todas las tareas vencidas que aún no están completadas.
        Permite ordenar los resultados por fecha de vencimiento, título o fecha de creación.
        """
        # Filtra las tareas vencidas (no completadas)
        now = datetime.now(LOCAL_TZ)
        query = Task.query.filter(
            Task.completed == False,
            Task.due_date < now
        )

        # Ordena las tareas según el criterio indicado
        if order_by == 'date':
            query = query.order_by(Task.due_date.asc())
        elif order_by == 'title':
            query = query.order_by(Task.title.asc())
        elif order_by == 'created':
            query = query.order_by(Task.created_at.desc())        
        # Devuelve la lista de tareas vencidas    
        return query.all()
    
    @staticmethod
    def get_pending_tasks_count():
        """Cuenta las tareas pendientes (no completadas y no vencidas)"""
        now = datetime.now(LOCAL_TZ)
        return Task.query.filter(
            Task.completed == False,
            (Task.due_date == None) | (Task.due_date >= now)
        ).count()

    @staticmethod
    def get_overdue_tasks_count():
        """Cuenta las tareas vencidas no completadas"""
        now = datetime.now(LOCAL_TZ)
        return Task.query.filter(
            Task.completed == False,
            Task.due_date < now
        ).count()

    @staticmethod
    def get_completed_tasks_count():
        """Cuenta las tareas completadas"""
        return Task.query.filter_by(completed=True).count()

    # Método para obtener una tarea por su ID
    def save(self):
        try:
            self.updated_at = datetime.utcnow().replace(microsecond=0)
            db.session.add(self)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    
    # Método para eliminar una tarea
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

