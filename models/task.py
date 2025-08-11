"""
Modelo Task - Representa una tarea en la base de datos

Este archivo contiene la definición del modelo Task usando SQLAlchemy ORM.
"""
from sqlalchemy import TypeDecorator
from sqlalchemy import event
from sqlalchemy.types import DateTime
from datetime import datetime
from extensions import db 

class DateTimeWithoutMicroseconds(TypeDecorator):
    """Tipo personalizado para almacenar fechas sin microsegundos"""
    impl = db.String(26)  # Longitud suficiente para incluir microsegundos
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            # Formatear como YYYY-MM-DD HH:MM:SS
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            # Manejar diferentes formatos
            if '.' in value:  # Si tiene microsegundos
                value = value.split('.')[0]
            # Convertir string a datetime
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value

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
                          default=lambda: datetime.utcnow().replace(microsecond=0),
                          nullable=False)
    updated_at = db.Column(DateTimeWithoutMicroseconds(), 
                          default=lambda: datetime.utcnow().replace(microsecond=0),
                          onupdate=lambda: datetime.utcnow().replace(microsecond=0),
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
        pass # TODO: implementar el método
    
    def mark_completed(self):
        """Marca la tarea como completada"""
        pass # TODO: implementar el método
    
    def mark_pending(self):
        """Marca la tarea como pendiente"""
        pass # TODO: implementar el método
    
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
    def get_pending_tasks(order_by=None):
        """
        Obtiene todas las tareas pendientes (no completadas).
        Permite ordenar los resultados por fecha de vencimiento, título o fecha de creación.
        """   
        # Filtra únicamente las tareas que no están completadas
        query = Task.query.filter_by(completed=False)

        # Aplica el ordenamiento si se especifica
        if order_by == 'date':
            query = query.order_by(Task.due_date.asc())
        elif order_by == 'title':
            query = query.order_by(Task.title.asc())
        elif order_by == 'created':
            query = query.order_by(Task.created_at.desc())

        # Devuelve la lista de tareas pendientes
        return query.all()

    @staticmethod
    def get_completed_tasks(order_by=None):
        """
        Obtiene todas las tareas completadas.
        Permite ordenar los resultados por fecha de vencimiento, título o fecha de creación.
        """
        # Filtra únicamente las tareas que están completadas
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
    def get_overdue_tasks(order_by=None):
        """
        Obtiene todas las tareas vencidas que aún no están completadas.
        Permite ordenar los resultados por fecha de vencimiento, título o fecha de creación.
        """
        # Obtiene la fecha y hora actual para comparar con la fecha de vencimiento
        now = datetime.utcnow()

        # Filtra las tareas cuyo vencimiento ya pasó y que no están completadas
        query = Task.query.filter(Task.due_date < now, Task.completed == False)

        if order_by == 'date':
            query = query.order_by(Task.due_date.asc())
        elif order_by == 'title':
            query = query.order_by(Task.title.asc())
        elif order_by == 'created':
            query = query.order_by(Task.created_at.desc())
            
        # Devuelve la lista de tareas vencidas
        return query.all()

    
    def save(self):
        """Guarda la tarea en la base de datos"""
        pass # TODO: implementar el método
    
    def delete(self):
        """Elimina la tarea de la base de datos"""
        pass # TODO: implementar el método

