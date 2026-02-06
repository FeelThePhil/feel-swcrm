import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Configurazione Pagina
st.set_page_config(page_title="Feel - CRM Officina", layout="wide")

# --- CREDENZIALI (Spostale qui) ---
EMAIL_MITTENTE = "feel.swcrm@gmail.com"
PASSWORD_APP = "nsal fqko nwff idue" 

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
    st.subheader("🚀 Configura Campagna Email")
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_campagna = st.selectbox("Seleziona Tipo di Messaggio", 
                                    ["Follow-up Lead", "Reminder Revisione", "Info Nuovi Servizi"])
    
    # Testo preimpostato in base alla scelta
    if tipo_campagna == "Follow-up Lead":
        oggetto_default = "Hai ancora bisogno di assistenza per la tua auto?"
        testo_default = "Ciao [Nome],\n\nti scriviamo dall'Officina perché abbiamo visto che eri interessato ai nostri servizi. Hai ancora bisogno di supporto o vuoi fissare un appuntamento?\n\nA presto, il team di Feel."
    else:
        oggetto_default = "Scadenza Revisione imminente"
        testo_default = "Ciao [Nome],\nti ricordiamo che la revisione per la tua vettura è in scadenza.\nContattaci per prenotare."

    with col2:
        oggetto = st.text_input("Oggetto Email", oggetto_default)

    corpo_mail = st.text_area("Messaggio (usa [Nome] per personalizzare)", testo_default, height=150)

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
            time.sleep(0.5) # Piccola pausa per evitare spam filter

        st.success(f"✅ Campagna completata! Inviate con successo {successi} su {len(df)} email.")
else:
    st.info("Per iniziare, carica il file Excel dei tuoi lead dalla barra laterale sinistra.")
