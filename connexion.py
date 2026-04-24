import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mouad@2010",
        database="maintenance_preditive"
    )