from datetime import date, datetime
from typing import Optional, List, Dict, Union, Any
from database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(
        self,
        user_id: int,
        email: str,
        user_type: str,
        registration_date: datetime,
        last_login: Optional[datetime] = None,
        is_active: bool = True
    ):
        self.id = user_id
        self.email = email
        self.type = user_type
        self.registration_date = registration_date
        self.last_login = last_login
        self.is_active = is_active
    
    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional['User']:
        """Autentica un usuario y devuelve el objeto User si es válido"""
        query = "SELECT * FROM usuarios WHERE email = %s AND activo = TRUE"
        user_data = DatabaseManager.execute_query(query, (email,), fetch_one=True)
        
        if user_data and DatabaseManager.verify_password(
            user_data['contrasena_hash'], password
        ):
            return cls(
                user_id=user_data['id_usuario'],
                email=user_data['email'],
                user_type=user_data['tipo'],
                registration_date=user_data['fecha_registro'],
                last_login=user_data['ultimo_login'],
                is_active=bool(user_data['activo'])
            )
        return None
    
    def update_last_login(self):
        """Actualiza la fecha del último login"""
        query = "UPDATE usuarios SET ultimo_login = NOW() WHERE id_usuario = %s"
        DatabaseManager.execute_query(query, (self.id,), commit=True)
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """Obtiene un usuario por su ID"""
        query = "SELECT * FROM usuarios WHERE id_usuario = %s"
        user_data = DatabaseManager.execute_query(query, (user_id,), fetch_one=True)
        
        if user_data:
            return cls(
                user_id=user_data['id_usuario'],
                email=user_data['email'],
                user_type=user_data['tipo'],
                registration_date=user_data['fecha_registro'],
                last_login=user_data['ultimo_login'],
                is_active=bool(user_data['activo'])
            )
        return None

class AthleteProfile:
    def __init__(
        self,
        athlete_id: int,
        user_id: int,
        full_name: str,
        birth_date: date,
        height: float,
        weight: float,
        sport: str,
        max_hr: Optional[int] = None,
        resting_hr: Optional[int] = None,
        coach_id: Optional[int] = None
    ):
        self.id = athlete_id
        self.user_id = user_id
        self.full_name = full_name
        self.birth_date = birth_date
        self.height = height
        self.weight = weight
        self.sport = sport
        self.max_hr = max_hr
        self.resting_hr = resting_hr
        self.coach_id = coach_id
    
    @property
    def age(self) -> int:
        """Calcula la edad del atleta"""
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @classmethod
    def get_by_user_id(cls, user_id: int) -> Optional['AthleteProfile']:
        """Obtiene el perfil de atleta por ID de usuario"""
        query = """
        SELECT * FROM perfiles_atletas 
        WHERE id_usuario = %s
        """
        data = DatabaseManager.execute_query(query, (user_id,), fetch_one=True)
        
        if data:
            return cls(
                athlete_id=data['id_atleta'],
                user_id=data['id_usuario'],
                full_name=data['nombre_completo'],
                birth_date=data['fecha_nacimiento'],
                height=data['altura'],
                weight=data['peso'],
                sport=data['deporte'],
                max_hr=data['frecuencia_cardiaca_maxima'],
                resting_hr=data['frecuencia_cardiaca_minima'],
                coach_id=data['id_entrenador']
            )
        return None
    
    def update_profile(
        self,
        height: Optional[float] = None,
        weight: Optional[float] = None,
        sport: Optional[str] = None,
        resting_hr: Optional[int] = None
    ) -> bool:
        """Actualiza los datos del perfil del atleta"""
        try:
            query = """
            UPDATE perfiles_atletas 
            SET altura = %s, peso = %s, deporte = %s, frecuencia_cardiaca_minima = %s
            WHERE id_atleta = %s
            """
            params = (
                height if height is not None else self.height,
                weight if weight is not None else self.weight,
                sport if sport is not None else self.sport,
                resting_hr if resting_hr is not None else self.resting_hr,
                self.id
            )
            DatabaseManager.execute_query(query, params, commit=True)
            
            # Actualizar propiedades si la actualización fue exitosa
            if height is not None:
                self.height = height
            if weight is not None:
                self.weight = weight
            if sport is not None:
                self.sport = sport
            if resting_hr is not None:
                self.resting_hr = resting_hr
            
            return True
        except Exception as e:
            logger.error(f"Error updating athlete profile: {e}")
            return False
    
    def get_workouts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene los entrenamientos asignados al atleta"""
        query = """
        SELECT 
            aa.id_asignacion,
            e.id_entrenamiento,
            e.titulo,
            e.descripcion,
            e.duracion_estimada,
            e.nivel_dificultad,
            aa.fecha_asignacion,
            aa.fecha_completado,
            aa.estado,
            aa.feedback,
            aa.calificacion,
            pe.nombre_completo AS nombre_entrenador
        FROM 
            asignaciones_atletas aa
        JOIN 
            entrenamientos e ON aa.id_entrenamiento = e.id_entrenamiento
        JOIN 
            perfiles_entrenadores pe ON e.id_entrenador = pe.id_entrenador
        WHERE 
            aa.id_atleta = %s
            {}
        ORDER BY 
            aa.fecha_asignacion DESC
        """.format("AND aa.estado = %s" if status else "")
        
        params = (self.id,) if not status else (self.id, status)
        return DatabaseManager.execute_query(query, params)

class CoachProfile:
    def __init__(
        self,
        coach_id: int,
        user_id: int,
        full_name: str,
        birth_date: date,
        specialty: str,
        experience: str
    ):
        self.id = coach_id
        self.user_id = user_id
        self.full_name = full_name
        self.birth_date = birth_date
        self.specialty = specialty
        self.experience = experience
    
    @property
    def age(self) -> int:
        """Calcula la edad del entrenador"""
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @classmethod
    def get_by_user_id(cls, user_id: int) -> Optional['CoachProfile']:
        """Obtiene el perfil de entrenador por ID de usuario"""
        query = """
        SELECT * FROM perfiles_entrenadores 
        WHERE id_usuario = %s
        """
        data = DatabaseManager.execute_query(query, (user_id,), fetch_one=True)
        
        if data:
            return cls(
                coach_id=data['id_entrenador'],
                user_id=data['id_usuario'],
                full_name=data['nombre_completo'],
                birth_date=data['fecha_nacimiento'],
                specialty=data['especialidad'],
                experience=data['experiencia']
            )
        return None
    
    def get_assigned_athletes(self) -> List[Dict[str, Any]]:
        """Obtiene los atletas asignados a este entrenador"""
        query = """
        SELECT 
            pa.id_atleta,
            pa.nombre_completo,
            pa.fecha_nacimiento,
            pa.altura,
            pa.peso,
            pa.deporte,
            pa.frecuencia_cardiaca_maxima,
            pa.frecuencia_cardiaca_minima,
            u.email
        FROM 
            perfiles_atletas pa
        JOIN 
            usuarios u ON pa.id_usuario = u.id_usuario
        WHERE 
            pa.id_entrenador = %s AND u.activo = TRUE
        """
        return DatabaseManager.execute_query(query, (self.id,))
    
    def create_workout(
        self,
        title: str,
        description: str,
        estimated_duration: int,
        difficulty: str
    ) -> Optional['Workout']:
        """Crea un nuevo entrenamiento"""
        return Workout.create(self.id, title, description, estimated_duration, difficulty)
    
    def get_created_workouts(self) -> List[Dict[str, Any]]:
        """Obtiene los entrenamientos creados por este entrenador"""
        query = """
        SELECT 
            e.*,
            COUNT(aa.id_asignacion) AS asignaciones
        FROM 
            entrenamientos e
        LEFT JOIN 
            asignaciones_atletas aa ON e.id_entrenamiento = aa.id_entrenamiento
        WHERE 
            e.id_entrenador = %s
        GROUP BY 
            e.id_entrenamiento
        ORDER BY 
            e.fecha_creacion DESC
        """
        return DatabaseManager.execute_query(query, (self.id,))

class Exercise:
    def __init__(
        self,
        exercise_id: int,
        name: str,
        description: str,
        exercise_type: str,
        instructions: str,
        video_url: Optional[str] = None
    ):
        self.id = exercise_id
        self.name = name
        self.description = description
        self.type = exercise_type
        self.instructions = instructions
        self.video_url = video_url
    
    @classmethod
    def get_all(cls, exercise_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene todos los ejercicios, opcionalmente filtrados por tipo"""
        query = "SELECT * FROM ejercicios"
        params = None
        
        if exercise_type:
            query += " WHERE tipo = %s"
            params = (exercise_type,)
        
        query += " ORDER BY nombre"
        return DatabaseManager.execute_query(query, params)
    
    @classmethod
    def get_by_id(cls, exercise_id: int) -> Optional['Exercise']:
        """Obtiene un ejercicio por su ID"""
        query = "SELECT * FROM ejercicios WHERE id_ejercicio = %s"
        data = DatabaseManager.execute_query(query, (exercise_id,), fetch_one=True)
        
        if data:
            return cls(
                exercise_id=data['id_ejercicio'],
                name=data['nombre'],
                description=data['descripcion'],
                exercise_type=data['tipo'],
                instructions=data['instrucciones'],
                video_url=data['video_url']
            )
        return None

class Workout:
    def __init__(
        self,
        workout_id: int,
        coach_id: int,
        title: str,
        description: str,
        estimated_duration: int,
        difficulty: str,
        creation_date: datetime,
        exercises: Optional[List[Dict[str, Any]]] = None
    ):
        self.id = workout_id
        self.coach_id = coach_id
        self.title = title
        self.description = description
        self.estimated_duration = estimated_duration
        self.difficulty = difficulty
        self.creation_date = creation_date
        self.exercises = exercises or []
    
    @classmethod
    def create(
        cls,
        coach_id: int,
        title: str,
        description: str,
        estimated_duration: int,
        difficulty: str
    ) -> Optional['Workout']:
        """Crea un nuevo entrenamiento"""
        query = """
        INSERT INTO entrenamientos 
        (id_entrenador, titulo, descripcion, duracion_estimada, nivel_dificultad)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            DatabaseManager.execute_query(
                query,
                (coach_id, title, description, estimated_duration, difficulty),
                commit=True
            )
            
            # Obtener el ID del entrenamiento recién creado
            query = "SELECT LAST_INSERT_ID() AS id"
            result = DatabaseManager.execute_query(query, fetch_one=True)
            
            if result:
                return cls.get_by_id(result['id'])
            return None
        except Exception as e:
            logger.error(f"Error creating workout: {e}")
            return None
    
    @classmethod
    def get_by_id(cls, workout_id: int) -> Optional['Workout']:
        """Obtiene un entrenamiento por su ID con sus ejercicios"""
        # Obtener datos básicos del entrenamiento
        query = """
        SELECT * FROM entrenamientos 
        WHERE id_entrenamiento = %s
        """
        data = DatabaseManager.execute_query(query, (workout_id,), fetch_one=True)
        
        if not data:
            return None
        
        # Obtener ejercicios asociados
        exercises_query = """
        SELECT 
            ee.*,
            e.nombre AS nombre_ejercicio,
            e.descripcion AS descripcion_ejercicio,
            e.tipo AS tipo_ejercicio
        FROM 
            entrenamiento_ejercicios ee
        JOIN 
            ejercicios e ON ee.id_ejercicio = e.id_ejercicio
        WHERE 
            ee.id_entrenamiento = %s
        ORDER BY 
            ee.orden
        """
        exercises = DatabaseManager.execute_query(exercises_query, (workout_id,))
        
        return cls(
            workout_id=data['id_entrenamiento'],
            coach_id=data['id_entrenador'],
            title=data['titulo'],
            description=data['descripcion'],
            estimated_duration=data['duracion_estimada'],
            difficulty=data['nivel_dificultad'],
            creation_date=data['fecha_creacion'],
            exercises=exercises
        )
    
    def assign_to_athlete(self, athlete_id: int) -> bool:
        """Asigna este entrenamiento a un atleta"""
        query = """
        INSERT INTO asignaciones_atletas 
        (id_atleta, id_entrenamiento, estado)
        VALUES (%s, %s, 'pendiente')
        ON DUPLICATE KEY UPDATE estado = 'pendiente'
        """
        try:
            DatabaseManager.execute_query(
                query,
                (athlete_id, self.id),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Error assigning workout to athlete: {e}")
            return False
    
    def add_exercise(
        self,
        exercise_id: int,
        sets: Optional[int] = None,
        reps: Optional[int] = None,
        duration: Optional[int] = None,
        order: int = 1,
        rest: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Añade un ejercicio al entrenamiento"""
        query = """
        INSERT INTO entrenamiento_ejercicios 
        (id_entrenamiento, id_ejercicio, series, repeticiones, duracion, orden, descanso, notas)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            DatabaseManager.execute_query(
                query,
                (self.id, exercise_id, sets, reps, duration, order, rest, notes),
                commit=True
            )
            return True
        except Exception as e:
            logger.error(f"Error adding exercise to workout: {e}")
            return False

class WorkoutAssignment:
    def __init__(
        self,
        assignment_id: int,
        workout_id: int,
        athlete_id: int,
        assignment_date: datetime,
        status: str,
        completion_date: Optional[datetime] = None,
        feedback: Optional[str] = None,
        rating: Optional[int] = None
    ):
        self.id = assignment_id
        self.workout_id = workout_id
        self.athlete_id = athlete_id
        self.assignment_date = assignment_date
        self.status = status
        self.completion_date = completion_date
        self.feedback = feedback
        self.rating = rating
    
    @classmethod
    def get_by_id(cls, assignment_id: int) -> Optional['WorkoutAssignment']:
        """Obtiene una asignación por su ID"""
        query = """
        SELECT * FROM asignaciones_atletas 
        WHERE id_asignacion = %s
        """
        data = DatabaseManager.execute_query(query, (assignment_id,), fetch_one=True)
        
        if data:
            return cls(
                assignment_id=data['id_asignacion'],
                workout_id=data['id_entrenamiento'],
                athlete_id=data['id_atleta'],
                assignment_date=data['fecha_asignacion'],
                status=data['estado'],
                completion_date=data['fecha_completado'],
                feedback=data['feedback'],
                rating=data['calificacion']
            )
        return None
    
    def update_status(self, new_status: str) -> bool:
        """Actualiza el estado de la asignación"""
        query = """
        UPDATE asignaciones_atletas 
        SET estado = %s
        WHERE id_asignacion = %s
        """
        try:
            DatabaseManager.execute_query(
                query,
                (new_status, self.id),
                commit=True
            )
            self.status = new_status
            return True
        except Exception as e:
            logger.error(f"Error updating assignment status: {e}")
            return False
    
    def complete(self, feedback: Optional[str] = None, rating: Optional[int] = None) -> bool:
        """Marca la asignación como completada"""
        query = """
        UPDATE asignaciones_atletas 
        SET estado = 'completado', 
            fecha_completado = NOW(),
            feedback = %s,
            calificacion = %s
        WHERE id_asignacion = %s
        """
        try:
            DatabaseManager.execute_query(
                query,
                (feedback, rating, self.id),
                commit=True
            )
            self.status = 'completado'
            self.completion_date = datetime.now()
            self.feedback = feedback
            self.rating = rating
            return True
        except Exception as e:
            logger.error(f"Error completing workout assignment: {e}")
            return False