import mysql.connector
from mysql.connector import Error, pooling
import bcrypt
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Union, Dict, List, Any

# Cargar variables de entorno
load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseManager:
    _connection_pool = None
    
    @classmethod
    def initialize_pool(cls):
        """Inicializa el pool de conexiones a la base de datos"""
        if cls._connection_pool is None:
            try:
                cls._connection_pool = pooling.MySQLConnectionPool(
                    pool_name="sportpro_pool",
                    pool_size=5,
                    host=os.getenv("DB_HOST", "localhost"),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", "aplicacion_deportiva"),
                    pool_reset_session=True
                )
                logger.info("Database connection pool created successfully")
            except Error as e:
                logger.error(f"Error creating database connection pool: {e}")
                raise
    
    @staticmethod
    def fetch_one(query: str, params: tuple) -> dict:
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        
    @classmethod
    def get_connection(cls):
        """Obtiene una conexión del pool"""
        if cls._connection_pool is None:
            cls.initialize_pool()
        return cls._connection_pool.get_connection()
    
    @classmethod
    def execute_query(
        cls,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        commit: bool = False,
        conn: Optional[Any] = None  # Nueva opción para conexión existente
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Ejecuta una consulta SQL y devuelve los resultados
    
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta
            fetch_one: Si True, devuelve solo un registro
            commit: Si True, hace commit de la transacción
            conn: Conexión existente (opcional). Si no se proporciona, se crea una nueva.
            
        Returns:
            Resultados de la consulta (dict, list o None)
        """
        cursor = None
        should_close_conn = False  # Determina si debemos cerrar la conexión al final
    
        try:
            # Si no se proporciona una conexión, obtenemos una nueva
            if conn is None:
                conn = cls.get_connection()
                should_close_conn = True
        
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
        
            # Solo hacemos commit si se solicita EXPLÍCITAMENTE y es una conexión nueva
            if commit and should_close_conn:
                conn.commit()
        
            # Si es una consulta de selección, retornamos resultados
            if fetch_one:
                return cursor.fetchone()
            elif query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE')):
                return cursor.fetchall()
        
            return None
        
        except Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            # Solo cerramos la conexión si la creamos nosotros
            if should_close_conn and conn:
                conn.close()
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Genera un hash seguro de la contraseña"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @classmethod
    def verify_password(cls, hashed_password: str, user_password: str) -> bool:
        """Verifica si la contraseña coincide con el hash"""
        return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @classmethod
    def close_pool(cls):
        """Cierra todas las conexiones del pool"""
        if cls._connection_pool:
            cls._connection_pool.close_all()
            logger.info("Database connection pool closed")

   #Nuevos metodos
    @classmethod
    def start_transaction(cls):
        """Inicia una transacción explícita"""
        conn = cls.get_connection()
        conn.autocommit = False  # Desactiva el autocommit
        return conn

    @classmethod
    def commit_transaction(cls, conn):
        """Confirma una transacción"""
        try:
            conn.commit()
        except Error as e:
            logger.error(f"Error committing transaction: {e}")
            raise
        finally:
            conn.close()

    @classmethod
    def rollback_transaction(cls, conn):
        """Revierte una transacción"""
        try:
            conn.rollback()
        except Error as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise
        finally:
            conn.close()

# Funciones de compatibilidad
def init_db():
    DatabaseManager.initialize_pool()
    return DatabaseManager.get_connection()

def close_db(conn):
    if conn:
        conn.close()