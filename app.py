import streamlit as st
import pandas as pd
from connexion import get_connection
from datetime import datetime

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================
import os

# ============================================
# CONFIGURATION PWA
# ============================================
pwa_html = """
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#4f8cff">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="BioMed Maintenance">
<link rel="apple-touch-icon" href="icon-192.png">
"""

st.markdown(pwa_html, unsafe_allow_html=True)
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
    
    cursor.execute("SELECT criticite, service FROM equipements WHERE id = %s", (equipement_id,))
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
        WHERE equipement_id = %s AND date_creation > DATE_SUB(NOW(), INTERVAL 7 DAY)
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
    equipement_lower = equipement_nom.lower()
    
    if 'pression' in description_lower or 'dialyse' in equipement_lower:
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
    
    if 'alarme' in description_lower or 'fréquente' in description_lower:
        solutions.append({
            'cause': 'Paramètres incorrects',
            'action': 'Vérifier les réglages et recalibrer',
            'documentation': 'Manuel technique section 5'
        })
    
    if 'affichage' in description_lower or 'écran' in description_lower:
        solutions.append({
            'cause': "Problème d'affichage",
            'action': "Redémarrer l'équipement et vérifier les connexions",
            'documentation': 'Guide dépannage écran'
        })
    
    if not solutions:
        solutions.append({
            'cause': 'Cause non identifiée',
            'action': 'Effectuer un diagnostic complet',
            'documentation': 'Contacter le support technique'
        })
    
    return solutions

def get_badge(score):
    """Retourne le badge HTML pour un score"""
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
with st.sidebar:
    st.header("🔐 Authentification")
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, role FROM utilisateurs WHERE email = %s AND mot_de_passe = %s", (email, password))
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
    
    # ===== FILTRE PAR SERVICE =====
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Filtres")
    
    cursor.execute("SELECT DISTINCT service FROM equipements")
    services_list = cursor.fetchall()
    services_options = ["Tous les services"] + [s[0] for s in services_list]
    service_filter = st.sidebar.selectbox("🏥 Service", services_options)
    
    # ===== MENU =====
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "Déclarer une panne", "Solutions", "Mes interventions", "Statistiques", "Historique équipements"])
    
    # ========== DASHBOARD ==========
    if menu == "Dashboard":
        cursor.execute("SELECT COUNT(*) FROM pannes")
        total_pannes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pannes WHERE statut IN ('nouvelle', 'prise_en_charge', 'en_cours')")
        en_cours = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pannes WHERE score_priorite >= 15 AND statut != 'resolue'")
        critiques = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM interventions WHERE DATE(debut_intervention) = CURDATE()")
        interventions = cursor.fetchone()[0]
        
        # En-tête gradient
        st.markdown(
            f"""
            <div style="background: linear-gradient(120deg, #4f8cff 0%, #c471ed 100%);
                padding: 2rem 2rem;
                border-radius: 32px;
                margin-bottom: 1.8rem;
                box-shadow: 0 6px 36px 0 #3d175c20;">
                <span style="font-weight: 500; color: #ecf1ff; font-size:1rem;">
                    👋 Bienvenue, <strong>{st.session_state.get('user_name', '')}</strong> !
                </span>
                <h1 style="color: #fff; margin: 0.3rem 0 0 0; font-size:2.2rem; font-weight: 700;">
                    📊 Tableau de bord
                </h1>
                <p style="color: #f2eaff; margin: 0.2rem 0 0 0; font-size:1rem;">
                    Suivi en temps réel des équipements biomédicaux
                </p>
            </div>
            """, unsafe_allow_html=True
        )
        
        # Cartes statistiques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 20px; padding: 1.2rem; text-align: center;">
                <div style="font-size: 2rem;">📋</div>
                <div style="font-size: 2rem; font-weight: bold; color: white;">{total_pannes}</div>
                <div style="color: #e0d4ff;">Pannes totales</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
                border-radius: 20px; padding: 1.2rem; text-align: center;">
                <div style="font-size: 2rem;">🛠️</div>
                <div style="font-size: 2rem; font-weight: bold; color: white;">{en_cours}</div>
                <div style="color: #c8f0e0;">En cours</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
                border-radius: 20px; padding: 1.2rem; text-align: center;">
                <div style="font-size: 2rem;">🔥</div>
                <div style="font-size: 2rem; font-weight: bold; color: #5a3a00;">{critiques}</div>
                <div style="color: #8a6a20;">Critiques</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #536976 0%, #292e49 100%);
                border-radius: 20px; padding: 1.2rem; text-align: center;">
                <div style="font-size: 2rem;">👨‍🔧</div>
                <div style="font-size: 2rem; font-weight: bold; color: white;">{interventions}</div>
                <div style="color: #b0c4de;">Interventions</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📋 Dernières pannes déclarées")
        
        # Liste des pannes avec filtre
        if service_filter == "Tous les services":
            cursor.execute("""
                SELECT p.id, e.code, e.nom, p.description, p.score_priorite, p.statut, p.date_creation
                FROM pannes p
                JOIN equipements e ON p.equipement_id = e.id
                ORDER BY p.date_creation DESC
                LIMIT 10
            """)
        else:
            cursor.execute("""
                SELECT p.id, e.code, e.nom, p.description, p.score_priorite, p.statut, p.date_creation
                FROM pannes p
                JOIN equipements e ON p.equipement_id = e.id
                WHERE e.service = %s
                ORDER BY p.date_creation DESC
                LIMIT 10
            """, (service_filter,))
        pannes = cursor.fetchall()
        
        for panne in pannes:
            score = panne[4]
            if score >= 15:
                bg_badge = "#dc3545"
                icon = "🔴"
                niveau = "CRITIQUE"
            elif score >= 10:
                bg_badge = "#fd7e14"
                icon = "🟠"
                niveau = "ÉLEVÉ"
            elif score >= 5:
                bg_badge = "#ffc107"
                icon = "🟡"
                niveau = "MOYEN"
            else:
                bg_badge = "#28a745"
                icon = "🟢"
                niveau = "FAIBLE"
            
            st.markdown(f"""
            <div style="background: #f8f9fa; border-radius: 15px; padding: 0.8rem 1rem; margin-bottom: 0.7rem; border-left: 5px solid {bg_badge};">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="font-weight: bold;">{icon} {panne[1]} - {panne[2]}</span>
                        <span style="background: {bg_badge}; color: white; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.7rem; margin-left: 0.5rem;">{niveau}</span>
                    </div>
                    <div>
                        <span style="color: #888; font-size: 0.75rem;">{panne[6]}</span>
                        <span style="background: #e9ecef; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.7rem; margin-left: 0.5rem;">{panne[5]}</span>
                    </div>
                </div>
                <p style="margin: 0.5rem 0 0 0; color: #555; font-size: 0.85rem;">{panne[3][:90]}...</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ========== DÉCLARER UNE PANNE ==========
    elif menu == "Déclarer une panne":
        st.subheader("➕ Déclarer une nouvelle panne")
        
        cursor.execute("SELECT id, code, nom FROM equipements")
        equipements = cursor.fetchall()
        equipement_choice = st.selectbox("Équipement", equipements, format_func=lambda x: f"{x[1]} - {x[2]}")
        
        description = st.text_area("Description du problème", height=150)
        photo = st.file_uploader("📷 Photo (optionnel)", type=["jpg", "png", "jpeg"])
        niveau_urgence = st.selectbox("Niveau d'urgence", ["Faible", "Moyen", "Elevé", "Critique"])
        
        if st.button("Déclarer la panne"):
            score = calculer_score_priorite(equipement_choice[0], description, niveau_urgence, conn)
            
            # Sauvegarde de la photo
            photo_path = None
            if photo:
                import os
                if not os.path.exists("photos"):
                    os.makedirs("photos")
                photo_path = f"photos/panne_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                with open(photo_path, "wb") as f:
                    f.write(photo.getbuffer())
            
            cursor.execute("""
                INSERT INTO pannes (equipement_id, declare_par, description, niveau_urgence, statut, score_priorite)
                VALUES (%s, %s, %s, %s, %s, %s)
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
                        st.write(f"**Action recommandée :** {sol['action']}")
                        st.write(f"**Documentation :** {sol['documentation']}")
                        
                        if st.button(f"Appliquer cette solution", key=f"sol_{i}"):
                            st.success("✅ Solution enregistrée dans l'historique !")
        else:
            st.info("Aucune panne en attente de résolution")
    
    # ========== MES INTERVENTIONS ==========
    elif menu == "Mes interventions":
        st.subheader("🛠️ Mes interventions")
        
        if st.session_state["user_role"] == "technicien":
            tab1, tab2 = st.tabs(["📋 En cours", "✅ Terminées"])
            
            with tab1:
                st.markdown("### Interventions à traiter")
                cursor.execute("""
                    SELECT p.id, e.code, e.nom, p.description, p.score_priorite
                    FROM pannes p
                    JOIN equipements e ON p.equipement_id = e.id
                    WHERE p.statut IN ('nouvelle', 'prise_en_charge')
                    ORDER BY p.score_priorite DESC
                """)
                pannes_a_traiter = cursor.fetchall()
                
                if pannes_a_traiter:
                    for panne in pannes_a_traiter:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            score = panne[4]
                            if score >= 15:
                                st.markdown("🔴 **CRITIQUE**")
                            elif score >= 10:
                                st.markdown("🟠 **ÉLEVÉ**")
                            elif score >= 5:
                                st.markdown("🟡 **MOYEN**")
                            else:
                                st.markdown("🟢 **FAIBLE**")
                            st.write(f"**{panne[1]}** - {panne[2]}")
                            st.write(f"{panne[3][:100]}...")
                        with col2:
                            if st.button(f"📌 Prendre en charge", key=f"take_{panne[0]}"):
                                cursor.execute("""
                                    INSERT INTO interventions (panne_id, technicien_id, debut_intervention, progression)
                                    VALUES (%s, %s, NOW(), 0)
                                """, (panne[0], st.session_state["user_id"]))
                                cursor.execute("UPDATE pannes SET statut = 'prise_en_charge' WHERE id = %s", (panne[0],))
                                conn.commit()
                                st.success(f"Intervention démarrée !")
                                st.rerun()
                        st.divider()
                else:
                    st.info("Aucune panne à traiter")
                
                st.markdown("### Interventions en cours")
                cursor.execute("""
                    SELECT i.id, e.code, e.nom, p.description, i.progression
                    FROM interventions i
                    JOIN pannes p ON i.panne_id = p.id
                    JOIN equipements e ON p.equipement_id = e.id
                    WHERE i.technicien_id = %s AND i.fin_intervention IS NULL
                """, (st.session_state["user_id"],))
                interventions_cours = cursor.fetchall()
                
                if interventions_cours:
                    for interv in interventions_cours:
                        with st.expander(f"🔄 {interv[1]} - {interv[2]} (Progression: {interv[4]}%)"):
                            st.progress(interv[4] / 100)
                            nouvelle_progression = st.slider("Progression", 0, 100, interv[4], key=f"prog_{interv[0]}")
                            if nouvelle_progression != interv[4]:
                                cursor.execute("UPDATE interventions SET progression = %s WHERE id = %s", (nouvelle_progression, interv[0]))
                                conn.commit()
                                st.rerun()
                            commentaire = st.text_area("Commentaire", key=f"comm_{interv[0]}")
                            if st.button("📝 Mettre à jour", key=f"update_{interv[0]}"):
                                if commentaire:
                                    cursor.execute("UPDATE interventions SET commentaire = %s WHERE id = %s", (commentaire, interv[0]))
                                    conn.commit()
                                    st.success("Commentaire ajouté !")
                            if nouvelle_progression >= 100:
                                if st.button("✅ Terminer", key=f"finish_{interv[0]}"):
                                    cursor.execute("UPDATE interventions SET fin_intervention = NOW(), progression = 100 WHERE id = %s", (interv[0],))
                                    cursor.execute("UPDATE pannes SET statut = 'resolue' WHERE id = %s", (interv[2],))
                                    conn.commit()
                                    st.success("Intervention terminée !")
                                    st.rerun()
                else:
                    st.info("Aucune intervention en cours")
            
            with tab2:
                st.markdown("### Interventions terminées")
                cursor.execute("""
                    SELECT e.code, e.nom, p.description, i.fin_intervention, i.commentaire
                    FROM interventions i
                    JOIN pannes p ON i.panne_id = p.id
                    JOIN equipements e ON p.equipement_id = e.id
                    WHERE i.technicien_id = %s AND i.fin_intervention IS NOT NULL
                    ORDER BY i.fin_intervention DESC
                    LIMIT 20
                """, (st.session_state["user_id"],))
                interventions_terminees = cursor.fetchall()
                
                if interventions_terminees:
                    for interv in interventions_terminees:
                        with st.expander(f"✅ {interv[0]} - {interv[1]}"):
                            st.write(f"**Problème :** {interv[2][:150]}...")
                            st.write(f"**Terminée le :** {interv[3]}")
                            st.write(f"**Commentaire :** {interv[4] if interv[4] else 'Aucun'}")
                else:
                    st.info("Aucune intervention terminée")
        else:
            st.warning("⚠️ Section réservée aux techniciens")
            
            # Consultation pour autres rôles
            st.markdown("### 📋 Suivi des interventions")
            cursor.execute("""
                SELECT e.code, e.nom, p.description, i.progression, u.nom
                FROM interventions i
                JOIN pannes p ON i.panne_id = p.id
                JOIN equipements e ON p.equipement_id = e.id
                JOIN utilisateurs u ON i.technicien_id = u.id
                WHERE i.fin_intervention IS NULL
                ORDER BY p.score_priorite DESC
            """)
            interventions_globales = cursor.fetchall()
            
            for interv in interventions_globales:
                st.write(f"**{interv[0]}** - {interv[1]}")
                st.write(f"👨‍🔧 {interv[4]} | 📊 Progression: {interv[3]}%")
                st.progress(interv[3] / 100)
                st.divider()
    
    # ========== STATISTIQUES ==========
    elif menu == "Statistiques":
        st.subheader("📊 Statistiques des pannes")
        
        # Export CSV
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📥 Exporter CSV"):
                import io
                df_all = pd.read_sql("SELECT * FROM pannes", conn)
                csv = df_all.to_csv(index=False)
                st.download_button("📥 Télécharger", csv, "rapport_pannes.csv", "text/csv")
        
        with col1:
            cursor.execute("""
                SELECT e.service, COUNT(*) as total
                FROM pannes p
                JOIN equipements e ON p.equipement_id = e.id
                GROUP BY e.service
            """)
            df_services = pd.DataFrame(cursor.fetchall(), columns=["Service", "Total"])
            if not df_services.empty:
                st.bar_chart(df_services.set_index("Service"))
        
        # Évolution
        st.subheader("📈 Évolution des pannes (30 jours)")
        cursor.execute("""
            SELECT DATE(date_creation) as jour, COUNT(*) as nombre
            FROM pannes
            WHERE date_creation > DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(date_creation)
            ORDER BY jour
        """)
        evolution = cursor.fetchall()
        if evolution:
            df_evolution = pd.DataFrame(evolution, columns=["Date", "Nombre"])
            st.line_chart(df_evolution.set_index("Date"))
        
        # Pannes par priorité
        st.subheader("📊 Pannes par priorité")
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN score_priorite >= 15 THEN 'Critique'
                    WHEN score_priorite >= 10 THEN 'Elevé'
                    WHEN score_priorite >= 5 THEN 'Moyen'
                    ELSE 'Faible'
                END as niveau,
                COUNT(*) as total
            FROM pannes
            GROUP BY niveau
        """)
        df_priorites = pd.DataFrame(cursor.fetchall(), columns=["Niveau", "Total"])
        if not df_priorites.empty:
            st.dataframe(df_priorites, use_container_width=True)
        
        # Classement des services
        st.subheader("🏆 Classement des services")
        cursor.execute("""
            SELECT e.service, COUNT(*) as pannes, ROUND(AVG(p.score_priorite),1) as score_moyen
            FROM pannes p
            JOIN equipements e ON p.equipement_id = e.id
            GROUP BY e.service
            ORDER BY pannes DESC
        """)
        df_classement = pd.DataFrame(cursor.fetchall(), columns=["Service", "Pannes", "Score moyen"])
        if not df_classement.empty:
            st.dataframe(df_classement, use_container_width=True)
    
    # ========== HISTORIQUE ÉQUIPEMENTS ==========
    elif menu == "Historique équipements":
        st.subheader("📋 Historique des équipements")
        
        cursor.execute("SELECT id, code, nom, service FROM equipements")
        equipements_list = cursor.fetchall()
        
        equip_choice = st.selectbox("Choisir un équipement", equipements_list, format_func=lambda x: f"{x[1]} - {x[2]}")
        
        if equip_choice:
            st.markdown(f"### {equip_choice[1]} - {equip_choice[2]}")
            st.write(f"**Service :** {equip_choice[3]}")
            
            cursor.execute("""
                SELECT p.date_creation, p.description, p.score_priorite, p.statut
                FROM pannes p
                WHERE p.equipement_id = %s
                ORDER BY p.date_creation DESC
                LIMIT 20
            """, (equip_choice[0],))
            historique = cursor.fetchall()
            
            if historique:
                df_hist = pd.DataFrame(historique, columns=["Date", "Problème", "Score", "Statut"])
                st.dataframe(df_hist, use_container_width=True)
            else:
                st.info("Aucun historique pour cet équipement")
    
    conn.close()

else:
    st.info("👈 Veuillez vous connecter via le menu de gauche")