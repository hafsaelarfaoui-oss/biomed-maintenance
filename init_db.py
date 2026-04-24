import sqlite3
import os

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

# Tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    email TEXT UNIQUE,
    mot_de_passe TEXT,
    role TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS equipements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    nom TEXT,
    service TEXT,
    criticite INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS pannes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipement_id INTEGER,
    declare_par INTEGER,
    description TEXT,
    niveau_urgence TEXT,
    photo TEXT,
    statut TEXT,
    score_priorite INTEGER,
    date_creation TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    panne_id INTEGER,
    technicien_id INTEGER,
    description TEXT,
    solution_utilisee TEXT,
    progression INTEGER,
    debut_intervention TIMESTAMP,
    fin_intervention TIMESTAMP,
    commentaire TEXT
)
''')

# Données de test
cursor.execute("INSERT OR IGNORE INTO utilisateurs (id, nom, email, mot_de_passe, role) VALUES (1, 'Admin', 'admin@hopital.ma', 'admin123', 'admin')")
cursor.execute("INSERT OR IGNORE INTO utilisateurs (id, nom, email, mot_de_passe, role) VALUES (2, 'Ahmed Benali', 'ahmed.benali@hopital.ma', 'tech123', 'technicien')")
cursor.execute("INSERT OR IGNORE INTO utilisateurs (id, nom, email, mot_de_passe, role) VALUES (3, 'Service Dialyse', 'dialyse@hopital.ma', 'service123', 'service')")

cursor.execute("INSERT OR IGNORE INTO equipements (id, code, nom, service, criticite) VALUES (1, 'HD-01', 'Machine hémodialyse', 'Dialyse', 9)")
cursor.execute("INSERT OR IGNORE INTO equipements (id, code, nom, service, criticite) VALUES (2, 'RESP-01', 'Respirateur', 'Urgence', 10)")
cursor.execute("INSERT OR IGNORE INTO equipements (id, code, nom, service, criticite) VALUES (3, 'ECG-01', 'ECG', 'Cardiologie', 7)")

conn.commit()
conn.close()
print("Base de données créée avec succès !")