import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import io

st.set_page_config(
    page_title="Feel - Gestione Officina",
    page_icon="😈",
    layout="wide",
    initial_sidebar_state="expanded" 
)

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
logo_url = "https://officinefiore.it/wp-content/uploads/2025/05/logo-fiore.svg" 

st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="{logo_url}" width="200">
    </div>
    """,
    unsafe_allow_html=True
)
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
        msg['Reply-To'] = "segreteria@officinefiore.it"
        
        msg.attach(MIMEText(messaggio, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_MITTENTE, PASSWORD_APP)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- NUOVA INTERFACCIA ORDINATA ---
st.title("🛡️ Feel - Gestione Lead & Comunicazioni")
st.markdown("---")

# 1. SELEZIONE CAMPAGNA (Spostata PRIMA del caricamento)
st.subheader("🚀 1. Scegli la Campagna")
col1, col2 = st.columns(2)

with col1:
    tipo_campagna = st.selectbox(
        "Cosa vuoi fare oggi?", 
        ["Revisione", "Follow-up Post Intervento", "Comunicazione Generica"],
        key="selezione_tipo_campagna"
    )

# Logica dei testi preimpostati (si aggiornano subito)
if tipo_campagna == "Revisione":
    oggetto_default = "⚠️ Scadenza Revisione Ministeriale - Officina Fiore"
    # Messaggio in corretto italiano con tutti i campi richiesti
    testo_default = (
        "Gentile [Nome],\n\n"
        "da un controllo nei nostri archivi, le ricordiamo che il Suo veicolo [Tipo] "
        "targato [Targa] ha la revisione in scadenza entro la fine del mese prossimo.\n\n"
        "Considerando che l'ultimo intervento risulta effettuato in data [Data_Ultima], "
        "Le suggeriamo di contattarci al più presto per fissare un appuntamento ed evitare sanzioni.\n\n"
        "Restiamo a Sua completa disposizione.\n\n"
        "Cordiali saluti,\nOfficina Fiore"
    )
elif tipo_campagna == "Follow-up Post Intervento":
    oggetto_default = "Tutto bene con la tua auto?"
    testo_default = "Ciao [Nome],\n\nè passato qualche giorno dall'ultimo intervento sulla tua auto [Targa]. Volevamo assicurarci che tu sia soddisfatto.\n\nA disposizione!"
else:
    oggetto_default = "Novità dall'Officina"
    testo_default = "Ciao [Nome],\n\nvolevamo informarti sulle nostre ultime novità per la tua auto [Targa]. Passa a trovarci!"

with col2:
    oggetto = st.text_input("Oggetto Email", oggetto_default)

corpo_mail = st.text_area("Personalizza il messaggio (usa [Nome] e [Targa])", testo_default, height=180)

st.markdown("---")

# 2. CARICAMENTO DATI (Solo dopo aver deciso la campagna)
st.sidebar.header("📂 Carica Dati")
file_caricato = st.sidebar.file_uploader("Carica Excel Lead per questa campagna", type=['xlsx'])

if file_caricato:
    df = pd.read_excel(file_caricato)
    df.columns = df.columns.str.strip().str.lower()

    # --- LOGICA PIGNOLA SOLO PER REVISIONE ---
    if tipo_campagna == "Revisione":
        if 'ultima_revisione' in df.columns:
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            # Convertiamo la colonna in formato data
            df['ultima_revisione'] = pd.to_datetime(df['ultima_revisione'])
            
            # Calcoliamo il mese target: Oggi (Febbraio) + 1 mese = Marzo
            oggi = datetime.now()
            mese_target = (oggi + relativedelta(months=1)).month
            
            # FILTRO: Prendiamo tutti quelli che hanno fatto la revisione nel mese target, 
            # a prescindere dall'anno (così becchiamo le scadenze cicliche)
            df = df[df['ultima_revisione'].dt.month == mese_target].copy()
            
            st.success(f"🎯 Filtro Revisioni: Estratti {len(df)} veicoli che scadono nel mese {mese_target}")
        else:
            st.error("Attenzione: Per la campagna Revisione serve la colonna 'ultima_revisione' nell'Excel.")
            st.stop() # Blocca l'invio se mancano i dati fondamentali
    
    # 3. Anteprima e Invio
    st.write("### 📋 Lista Lead Pronti per l'invio")
    st.dataframe(df, use_container_width=True, height=400) 

    # ... (sopra c'è la tabella st.dataframe)

    # SOSTITUISCI DA QUI
    if st.button(f"AVVIA INVIO MASSIVO ({len(df)} email)", key="btn_invio_report"):
        progresso = st.progress(0)
        status_text = st.empty()
        
        risultati_campagna = [] 
        successi = 0
        
        for i, riga in df.iterrows():
            nome_cliente = str(riga['nome']) if 'nome' in riga else "Cliente"
            email_cliente = riga['email'] if 'email' in riga else None
            targa_veicolo = str(riga['targa']) if 'targa' in riga else "N.D."
            tipo_veicolo = str(riga['tipo']) if 'tipo' in riga else "veicolo"
            
            # Gestione data per il messaggio
            try:
                data_ultima = riga['ultima_revisione'].strftime('%d/%m/%Y')
            except:
                data_ultima = "N.D."
            
            stato_invio = "❌ Fallito"
            if email_cliente and str(email_cliente).strip() != "nan":
                messaggio_personalizzato = corpo_mail.replace("[Nome]", nome_cliente)\
                                                     .replace("[Targa]", targa_veicolo)\
                                                     .replace("[Tipo]", tipo_veicolo)\
                                                     .replace("[Data_Ultima]", data_ultima)
                
                if invia_email(email_cliente, oggetto, messaggio_personalizzato):
                    successi += 1
                    stato_invio = "✅ Inviata"
            else:
                stato_invio = "⚠️ Email Mancante"

            risultati_campagna.append({
                "Cliente": nome_cliente,
                "Email": email_cliente,
                "Targa": targa_veicolo,
                "Esito": stato_invio,
                "Orario": datetime.now().strftime("%H:%M:%S")
            })
            
            percentuale = (i + 1) / len(df)
            progresso.progress(percentuale)
            status_text.text(f"Stato: {stato_invio} a {email_cliente}... ({i+1}/{len(df)})")
            time.sleep(1)

        st.success(f"✅ Campagna completata! Successi: {successi} su {len(df)}")
        
        # Generazione Excel in memoria
        df_report = pd.DataFrame(risultati_campagna)
        
        # Tabella veloce degli errori a schermo
        errori = df_report[df_report["Esito"] != "✅ Inviata"]
        if not errori.empty:
            st.warning(f"Ci sono stati {len(errori)} problemi durante l'invio.")
            st.dataframe(errori)

        # Creazione del file Excel per il download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_report.to_excel(writer, index=False, sheet_name='Report_Invio')
        
        st.download_button(
            label="📥 Scarica Report Completo (Excel)",
            data=buffer.getvalue(),
            file_name=f"Report_Invio_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    # A QUI
    
        
else:
    st.info("⬆️ Scegli la campagna qui sopra e poi carica il file Excel dalla barra laterale per vedere i contatti.")
