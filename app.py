import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Configurazione Pagina
st.set_page_config(page_title="Feel - CRM Officina", layout="wide")

# Codice per nascondere il menu e la barra superiore di Streamlit
import streamlit.components.v1 as components

# 1. CSS per nascondere header e menu (quello che già facevamo)
st.markdown("""
    <style>
    header[data-testid="stHeader"], .stAppDeployButton, #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }
    /* Rimuove lo spazio bianco in alto */
    .main .block-container {
        padding-top: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. JAVASCRIPT per eliminare le icone in basso (GitHub e Streamlit Badge)
components.html(
    """
    <script>
    const removeElements = () => {
        // Cerca i badge e la toolbar in basso
        const badges = window.parent.document.querySelectorAll('[data-testid="stStatusWidget"], [data-testid="stToolbar"], #viewerBadge');
        badges.forEach(el => el.style.display = 'none');
        
        // Cerca specificamente le icone di GitHub e Hosted
        const toolbar = window.parent.document.querySelector('div[data-testid="stToolbar"]');
        if (toolbar) toolbar.style.display = 'none';
    };
    
    // Esegue il comando subito e poi ogni secondo per sicurezza
    removeElements();
    setInterval(removeElements, 1000);
    </script>
    """,
    height=0,
    width=0,
)

import streamlit as st

# Funzione per il controllo accesso
def check_password():
    if "password_correct" not in st.session_state:
        # Centriamo il contenuto per un'estetica impeccabile
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # INSERISCI QUI IL TUO LINK
            logo_url = "https://officinefiore.it/wp-content/uploads/2025/05/logo-fiore.svg" 
            
            # Usiamo HTML per visualizzare l'SVG in modo perfetto
            st.markdown(
                f'<div style="text-align: center;"><img src="{logo_url}" width="200"></div>', 
                unsafe_allow_html=True
            )
            
            st.title("Accesso Riservato Feel")
            
            # Campi di input
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Entra"):
                if (username == st.secrets["USER_LOGIN"] and 
                    password == st.secrets["USER_PASSWORD"]):
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Credenziali non valide")
        return False
    return True

# Applichiamo il blocco prima di tutto il resto
if not check_password():
    st.stop()

# --- DA QUI IN POI INCOMA IL TUO CODICE ATTUALE (IL CUORE DI FEEL) ---
st.title("Benvenuto nel cuore di Feel")
# ... tutto il resto del tuo codice ...

# --- CREDENZIALI (Spostale qui) ---
EMAIL_MITTENTE = "feel.swcrm@gmail.com"
PASSWORD_APP = st.secrets["EMAIL_PASSWORD"] 

# --- FUNZIONE INVIO EMAIL ---
def invia_email(destinatario, oggetto, messaggio):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_MITTENTE
        msg['To'] = destinatario
        msg['Subject'] = oggetto
        
        msg.attach(MIMEText(messaggio, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_MITTENTE, PASSWORD_APP)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- INTERFACCIA ---
st.title("🛡️ Feel - Gestione Lead & Comunicazioni")
st.markdown("---")

# 1. Caricamento Database
st.sidebar.header("📂 Carica Dati")
file_caricato = st.sidebar.file_uploader("Carica Excel Lead", type=['xlsx'])

if file_caricato:
    df = pd.read_excel(file_caricato)
    
    # 2. Selezione Campagna
    st.subheader("🚀 Configura Campagna")
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_campagna = st.selectbox("Seleziona il tipo di invio", 
                                    ["Revisione", "Follow-up Post Intervento", "Comunicazione Generica"])
    
    # Logica dei testi preimpostati
    if tipo_campagna == "Revisione":
        oggetto_default = "⚠️ Scadenza Revisione imminente - Officina"
        testo_default = "Ciao [Nome],\nti ricordiamo che la revisione della tua auto è in scadenza questo mese.\n\nContattaci al più presto per fissare un appuntamento ed evitare sanzioni.\n\nA presto!"
    
    elif tipo_campagna == "Follow-up Post Intervento":
        oggetto_default = "Tutto bene con la tua auto?"
        testo_default = "Ciao [Nome],\n\nè passato qualche giorno dall'ultimo intervento. Volevamo assicurarci che tutto sia perfetto e che tu sia soddisfatto del lavoro svolto.\n\nPer qualsiasi cosa, siamo a tua disposizione!"
    
    else: # Comunicazione Generica
        oggetto_default = "Novità dall'Officina"
        testo_default = "Ciao [Nome],\n\nvolevamo informarti sulle nostre ultime novità e promozioni dedicate alla cura della tua auto.\n\nPassa a trovarci!"

    with col2:
        oggetto = st.text_input("Oggetto Email", oggetto_default)

    corpo_mail = st.text_area("Messaggio (usa [Nome] per personalizzare)", testo_default, height=180)
    

    # 3. Anteprima e Invio
    st.write("### 📋 Lista Lead Rilevati")
    st.dataframe(df.head()) # Mostra i primi 5 per controllo

    if st.button(f"AVVIA INVIO MASSIVO ({len(df)} email)"):
        progresso = st.progress(0)
        status_text = st.empty()
        successi = 0
        
        for i, riga in df.iterrows():
            # Personalizza il messaggio col nome
            messaggio_personalizzato = corpo_mail.replace("[Nome]", str(riga['Nome']))
            
            # Invio reale
            risultato = invia_email(riga['Email'], oggetto, messaggio_personalizzato)
            
            if risultato:
                successi += 1
            
            # Aggiorna barra progresso
            percentuale = (i + 1) / len(df)
            progresso.progress(percentuale)
            status_text.text(f"Inviando a {riga['Email']}... ({i+1}/{len(df)})")
            time.sleep(1) # Piccola pausa per evitare spam filter

        st.success(f"✅ Campagna completata! Inviate con successo {successi} su {len(df)} email.")
else:
    st.info("Per iniziare, carica il file Excel dei tuoi lead dalla barra laterale sinistra.")
