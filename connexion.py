import sqlite3
import os
import streamlit as st

def get_connection():
    """Retourne une connexion SQLite compatible Streamlit Cloud"""
    
    # Sur Streamlit Cloud, utiliser un dossier temporaire
    if os.path.exists('/mount'):
        # Utiliser /tmp qui est accessible en écriture
        data_dir = '/tmp/biomed_data'
    else:
        # Environnement local
        data_dir = 'data'
    
    # Créer le dossier s'il n'existe pas
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    except:
        # Si erreur, utiliser /tmp directement
        data_dir = '/tmp'
    
    db_path = os.path.join(data_dir, 'database.db')
    
    # Initialiser la base si elle n'existe pas
    init_database(db_path)
    
    return sqlite3.connect(db_path, check_same_thread=False)

def init_database(db_path):
    """Initialise la base de données"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier si les tables existent déjà
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='utilisateurs'")
    if cursor.fetchone():
        conn.close()
        return
    
    # Table utilisateurs
    cursor.execute('''
    CREATE TABLE utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        email TEXT UNIQUE,
        mot_de_passe TEXT,
        role TEXT
    )
    ''')
    
    # Table equipements
    cursor.execute('''
    CREATE TABLE equipements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        nom TEXT,
        service TEXT,
        criticite INTEGER
    )
    ''')
    
    # Table pannes
    cursor.execute('''
    CREATE TABLE pannes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipement_id INTEGER,
        declare_par INTEGER,
        description TEXT,
        niveau_urgence TEXT,
        statut TEXT,
        score_priorite INTEGER,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table interventions
    cursor.execute('''
    CREATE TABLE interventions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        panne_id INTEGER,
        technicien_id INTEGER,
        progression INTEGER,
        debut_intervention TIMESTAMP,
        fin_intervention TIMESTAMP,
        commentaire TEXT
    )
    ''')
    
    # Insertion des données de test
    cursor.execute("INSERT INTO utilisateurs (nom, email, mot_de_passe, role) VALUES ('Admin Systeme', 'admin@hopital.ma', 'admin123', 'admin')")
    cursor.execute("INSERT INTO utilisateurs (nom, email, mot_de_passe, role) VALUES ('Ahmed Benali', 'ahmed.benali@hopital.ma', 'tech123', 'technicien')")
    cursor.execute("INSERT INTO utilisateurs (nom, email, mot_de_passe, role) VALUES ('Service Dialyse', 'dialyse@hopital.ma', 'service123', 'service')")
    
    cursor.execute("INSERT INTO equipements (code, nom, service, criticite) VALUES ('HD-01', 'Machine hémodialyse', 'Dialyse', 9)")
    cursor.execute("INSERT INTO equipements (code, nom, service, criticite) VALUES ('RESP-01', 'Respirateur', 'Urgence', 10)")
    cursor.execute("INSERT INTO equipements (code, nom, service, criticite) VALUES ('ECG-01', 'ECG', 'Cardiologie', 7)")
    
    conn.commit()
    conn.close()
