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
        commit: bool = False
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Ejecuta una consulta SQL y devuelve los resultados
        
        Args:
            query: Consulta SQL
            params: Parámetros para la consulta
            fetch_one: Si True, devuelve solo un registro
            commit: Si True, hace commit de la transacción
            
        Returns:
            Resultados de la consulta (dict, list o None)
        """
        conn = None
        cursor = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(query, params or ())
            
            if commit:
                conn.commit()
                return None
            
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            
            return result
        except Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
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

# Funciones de compatibilidad
def init_db():
    DatabaseManager.initialize_pool()
    return DatabaseManager.get_connection()

def close_db(conn):
    if conn:
        conn.close()