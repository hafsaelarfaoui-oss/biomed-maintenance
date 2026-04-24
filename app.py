import streamlit as st
import pandas as pd
from connexion import get_connection
from datetime import datetime
import os

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================
st.set_page_config(page_title="Gestion des pannes biomédicales", layout="wide")

# ============================================
# MODE SOMBRE
# ============================================
dark_mode = st.sidebar.toggle("🌙 Mode sombre", value=False)
if dark_mode:
    st.markdown("""
    <style>
        .stApp { background-color: #0e1117; color: #ffffff; }
        .stMarkdown, .stText, .stTitle { color: #ffffff; }
        .stSelectbox label, .stTextInput label, .stTextArea label { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# CSS PERSONNALISÉ
# ============================================
st.markdown("""
<style>
    .badge-critique {
        background-color: #dc3545;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
    }
    .badge-eleve {
        background-color: #fd7e14;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        display: inline-block;
    }
    .badge-moyen {
        background-color: #ffc107;
        color: black;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        display: inline-block;
    }
    .badge-faible {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FONCTIONS
# ============================================

def calculer_score_priorite(equipement_id, description, niveau_urgence, conn):
    """Calcule un score de priorité de 0 à 20"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT criticite, service FROM equipements WHERE id = ?", (equipement_id,))
    equipement = cursor.fetchone()
    criticite = equipement[0] if equipement else 5
    service = equipement[1] if equipement else ""
    
    services_critiques = ['Dialyse', 'Urgence', 'Bloc', 'Reanimation']
    bonus_service = 5 if service in services_critiques else 0
    
    niveaux = {'Faible': 0, 'Moyen': 2, 'Elevé': 4, 'Critique': 6}
    score_urgence = niveaux.get(niveau_urgence, 0)
    
    mots_critiques = {
        'patient': 3, 'danger': 5, 'urgence': 4, 'alarme': 2,
        'sang': 4, 'pression': 2, 'arrêt': 5, 'bloque': 3
    }
    description_lower = description.lower()
    bonus_mots = sum(score for mot, score in mots_critiques.items() if mot in description_lower)
    bonus_mots = min(bonus_mots, 5)
    
    cursor.execute("""
        SELECT COUNT(*) FROM pannes 
        WHERE equipement_id = ? AND date_creation > datetime('now', '-7 days')
    """, (equipement_id,))
    nb_pannes_recentes = cursor.fetchone()[0]
    bonus_repetition = 3 if nb_pannes_recentes >= 2 else 0
    
    score = criticite + bonus_service + score_urgence + bonus_mots + bonus_repetition
    score = min(score, 20)
    
    return score

def suggerer_solutions(description, equipement_nom):
    """Propose des solutions basées sur la description"""
    solutions = []
    description_lower = description.lower()
    
    if 'pression' in description_lower or 'dialyse' in description_lower:
        solutions.append({
            'cause': 'Pression veineuse élevée',
            'action': 'Vérifier le circuit sanguin et le filtre',
            'documentation': 'Guide hémodialyse - Chapitre 3'
        })
        solutions.append({
            'cause': 'Filtre obstrué',
            'action': 'Nettoyer ou remplacer le filtre',
            'documentation': 'Procédure maintenance N°42'
        })
    
    if 'alarme' in description_lower or 'frequente' in description_lower:
        solutions.append({
            'cause': 'Paramètres incorrects',
            'action': 'Vérifier les réglages et recalibrer',
            'documentation': 'Manuel technique section 5'
        })
    
    if not solutions:
        solutions.append({
            'cause': 'Cause non identifiée',
            'action': 'Effectuer un diagnostic complet',
            'documentation': 'Contacter le support technique'
        })
    
    return solutions

def get_badge(score):
    if score >= 15:
        return '<span class="badge-critique">🔴 CRITIQUE</span>'
    elif score >= 10:
        return '<span class="badge-eleve">🟠 ÉLEVÉ</span>'
    elif score >= 5:
        return '<span class="badge-moyen">🟡 MOYEN</span>'
    else:
        return '<span class="badge-faible">🟢 FAIBLE</span>'

# ============================================
# TITRE PRINCIPAL
# ============================================
st.title("🏥 Application de maintenance prédictive des équipements biomédicaux")

# ============================================
# SIDEBAR - CONNEXION
# ============================================
if "connected" not in st.session_state:
    st.session_state["connected"] = False

with st.sidebar:
    st.header("🔐 Authentification")
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, role FROM utilisateurs WHERE email = ? AND mot_de_passe = ?", (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            st.session_state["connected"] = True
            st.session_state["user_id"] = user[0]
            st.session_state["user_name"] = user[1]
            st.session_state["user_role"] = user[2]
            st.success(f"Bienvenue {user[1]} !")
            st.rerun()
        else:
            st.error("Email ou mot de passe incorrect")

# ============================================
# AFFICHAGE PRINCIPAL (SI CONNECTÉ)
# ============================================
if st.session_state.get("connected"):
    st.sidebar.success(f"Connecté en tant que {st.session_state['user_role']}")
    
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Filtre par service
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Filtres")
    
    cursor.execute("SELECT DISTINCT service FROM equipements")
    services_list = cursor.fetchall()
    services_options = ["Tous les services"] + [s[0] for s in services_list]
    service_filter = st.sidebar.selectbox("🏥 Service", services_options)
    
    # Menu
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "Déclarer une panne", "Solutions", "Statistiques"])
    
    # ========== DASHBOARD ==========
    if menu == "Dashboard":
        cursor.execute("SELECT COUNT(*) FROM pannes")
        total_pannes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pannes WHERE statut IN ('nouvelle', 'prise_en_charge', 'en_cours')")
        en_cours = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pannes WHERE score_priorite >= 15 AND statut != 'resolue'")
        critiques = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interventions WHERE date(debut_intervention) = date('now')")
        interventions = cursor.fetchone()[0]
        
        # En-tête
        st.markdown(f"""
        <div style="background: linear-gradient(120deg, #4f8cff 0%, #c471ed 100%); padding: 2rem; border-radius: 32px; margin-bottom: 1.8rem;">
            <span style="color: #ecf1ff;">👋 Bienvenue, <strong>{st.session_state.get('user_name', '')}</strong> !</span>
            <h1 style="color: white; margin: 0.3rem 0 0 0;">📊 Tableau de bord</h1>
            <p style="color: #f2eaff;">Suivi en temps réel des équipements biomédicaux</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Cartes
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📋 Pannes totales", total_pannes)
        col2.metric("🛠️ En cours", en_cours)
        col3.metric("🔥 Critiques", critiques)
        col4.metric("👨‍🔧 Interventions", interventions)
        
        st.markdown("---")
        st.subheader("📋 Dernières pannes déclarées")
        
        if service_filter == "Tous les services":
            cursor.execute("""
                SELECT e.code, e.nom, p.description, p.score_priorite, p.statut, p.date_creation
                FROM pannes p
                JOIN equipements e ON p.equipement_id = e.id
                ORDER BY p.date_creation DESC
                LIMIT 10
            """)
        else:
            cursor.execute("""
                SELECT e.code, e.nom, p.description, p.score_priorite, p.statut, p.date_creation
                FROM pannes p
                JOIN equipements e ON p.equipement_id = e.id
                WHERE e.service = ?
                ORDER BY p.date_creation DESC
                LIMIT 10
            """, (service_filter,))
        
        pannes = cursor.fetchall()
        for panne in pannes:
            badge = get_badge(panne[3])
            st.markdown(f"{badge} **{panne[0]}** - {panne[1]} : {panne[2][:80]}...")
    
    # ========== DÉCLARER UNE PANNE ==========
    elif menu == "Déclarer une panne":
        st.subheader("➕ Déclarer une nouvelle panne")
        
        cursor.execute("SELECT id, code, nom FROM equipements")
        equipements = cursor.fetchall()
        equipement_choice = st.selectbox("Équipement", equipements, format_func=lambda x: f"{x[1]} - {x[2]}")
        
        description = st.text_area("Description du problème", height=150)
        niveau_urgence = st.selectbox("Niveau d'urgence", ["Faible", "Moyen", "Elevé", "Critique"])
        
        if st.button("Déclarer la panne"):
            score = calculer_score_priorite(equipement_choice[0], description, niveau_urgence, conn)
            
            cursor.execute("""
                INSERT INTO pannes (equipement_id, declare_par, description, niveau_urgence, statut, score_priorite, date_creation)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (equipement_choice[0], st.session_state["user_id"], description, niveau_urgence, "nouvelle", score))
            conn.commit()
            
            badge = get_badge(score)
            st.success(f"✅ Panne déclarée ! Score de priorité : {score}/20 {badge}", unsafe_allow_html=True)
            st.rerun()
    
    # ========== SOLUTIONS ==========
    elif menu == "Solutions":
        st.subheader("💡 Suggestions de solutions")
        
        cursor.execute("""
            SELECT p.id, e.code, e.nom, p.description, p.score_priorite
            FROM pannes p
            JOIN equipements e ON p.equipement_id = e.id
            WHERE p.statut != 'resolue'
            ORDER BY p.score_priorite DESC
        """)
        pannes_non_resolues = cursor.fetchall()
        
        if pannes_non_resolues:
            panne_choice = st.selectbox(
                "Choisir une panne à analyser", 
                pannes_non_resolues,
                format_func=lambda x: f"[Score {x[4]}] {x[1]} - {x[2]}"
            )
            
            if panne_choice:
                solutions = suggerer_solutions(panne_choice[3], panne_choice[2])
                for i, sol in enumerate(solutions):
                    with st.expander(f"🔧 Solution {i+1} : {sol['cause']}"):
                        st.write(f"**Action :** {sol['action']}")
                        st.write(f"**Documentation :** {sol['documentation']}")
        else:
            st.info("Aucune panne en attente")
    
    # ========== STATISTIQUES ==========
    else:
        st.subheader("📊 Statistiques")
        
        cursor.execute("""
            SELECT e.service, COUNT(*) as total
            FROM pannes p
            JOIN equipements e ON p.equipement_id = e.id
            GROUP BY e.service
        """)
        df_services = pd.DataFrame(cursor.fetchall(), columns=["Service", "Total"])
        if not df_services.empty:
            st.bar_chart(df_services.set_index("Service"))
    
    conn.close()

else:
    st.info("👈 Veuillez vous connecter")
