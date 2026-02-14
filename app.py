import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import io
import gspread 
from datetime import datetime, timedelta

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
        # --- NUOVE FUNZIONI PER GOOGLE SHEETS (IL CERVELLO) ---

def get_google_sheet():
    """Questa funzione apre la porta del tuo Foglio Google"""
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        # Apre il file 'feel_storico_invii' e il foglio chiamato 'Log'
        sh = gc.open("feel_storico_invii").worksheet("Log")
        return sh
    except:
        return None

def verifica_duplicato_followup(identificativo):
    sheet = get_google_sheet()
    if not sheet: return False
    try:
        records = sheet.get_all_records()
        if not records: return False
        
        df_log = pd.DataFrame(records)
        # Rendiamo tutto minuscolo e senza spazi per non sbagliare
        df_log.columns = df_log.columns.str.strip().str.lower()
        
        # Puliamo i dati nel foglio
        df_log['email'] = df_log['email'].astype(str).str.strip().str.lower()
        df_log['targa'] = df_log['targa'].astype(str).str.strip().str.upper()
        
        identificativo_pulito = str(identificativo).strip().lower()
        
        # Filtro 14 giorni
        df_log['data_invio'] = pd.to_datetime(df_log['data_invio']).dt.date
        limite = (datetime.now() - timedelta(days=60)).date()
        
        duplicati = df_log[
            ((df_log['email'] == identificativo_pulito) | (df_log['targa'] == identificativo_pulito.upper())) & 
            (df_log['data_invio'] > limite) &
            (df_log['tipo_campagna'] == 'Follow-up Post Intervento')
        ]
        return not duplicati.empty
    except Exception as e:
        st.error(f"Errore controllo duplicati: {e}")
        return False


def registra_invio_storico(email, targa, tipo):
    """Questa funzione scrive i dati dell'invio sul foglio Google con messaggi di errore"""
    sheet = get_google_sheet()
    if sheet:
        try:
            # Aggiunge una riga con: Data, Email, Targa, Tipo Campagna
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d"), 
                str(email).strip(), 
                str(targa).strip(), 
                str(tipo)
            ])
            # Se vuoi una conferma visiva mentre invii, scommenta la riga sotto:
            # st.toast(f"Tracciato su Sheets: {email}")
        except Exception as e:
            st.error(f"❌ Errore tecnico nella scrittura su Google Sheets: {e}")
    else:
        st.error("⚠️ Feel non riesce a connettersi al Foglio Google. Verifica il nome del file o i permessi delle API.")

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
    oggetto_default = "⚠️ Scadenza Revisione Ministeriale - Officine Fiore"
    # Messaggio in corretto italiano con tutti i campi richiesti
    testo_default = (
        "Gentile [Nome],\n\n"
        "da un controllo nei nostri archivi, le ricordiamo che il Suo veicolo [Tipo] "
        "targato [Targa] ha la revisione in scadenza entro la fine del mese prossimo.\n\n"
        "Considerando che l'ultimo intervento risulta effettuato in data [Data_Ultima], "
        "Le suggeriamo di contattarci al più presto per fissare un appuntamento ed evitando sanzioni e fermi macchina.\n\n"
        "Restiamo a Sua completa disposizione.\n\n"
        "Cordiali saluti,\nOfficine Fiore"
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

    if st.button(f"AVVIA INVIO MASSIVO ({len(df)} email)", key="btn_invio_finale_stabile"):
        progresso = st.progress(0.0)
        status_text = st.empty()
        
        risultati_campagna = [] 
        successi = 0
        totale = len(df)
        
        for idx, (i, riga) in enumerate(df.iterrows()):
            nome_cliente = str(riga['nome']) if 'nome' in riga else "Cliente"
            email_cliente = str(riga['email']).strip() if 'email' in riga else ""
            targa_veicolo = str(riga['targa']) if 'targa' in riga else "N.D."
            tipo_veicolo = str(riga['tipo']) if 'tipo' in riga else "veicolo"
            
            try:
                data_ultima = riga['ultima_revisione'].strftime('%d/%m/%Y')
            except:
                data_ultima = "N.D."
              # --- INIZIO NUOVO PEZZO: CONTROLLO ANTI-DUPLICATO ---  
            gia_inviato = False
            if tipo_campagna == "Follow-up Post Intervento":
                if verifica_duplicato_followup(email_cliente) or verifica_duplicato_followup(targa_veicolo):
                    gia_inviato = True

            if gia_inviato:
                stato_invio = "⏭️ Saltato (Già inviato <14gg)"
                risultati_campagna.append({
                    "Cliente": nome_cliente,
                    "Email": email_cliente,
                    "Targa": targa_veicolo,
                    "Esito": stato_invio,
                    "Orario": datetime.now().strftime("%H:%M:%S")
                })
                continue # Salta tutto il resto e passa al prossimo cliente
                # --- FINE NUOVO PEZZO: CONTROLLO ANTI-DUPLICATO ---
            
            # Validazione base: l'email deve contenere @ e .
            stato_invio = "❌ Fallito"
            if "@" in email_cliente and "." in email_cliente:
                messaggio_personalizzato = corpo_mail.replace("[Nome]", nome_cliente)\
                                                     .replace("[Targa]", targa_veicolo)\
                                                     .replace("[Tipo]", tipo_veicolo)\
                                                     .replace("[Data_Ultima]", data_ultima)
                
                if invia_email(email_cliente, oggetto, messaggio_personalizzato):
                    successi += 1
                    stato_invio = "✅ Inviata"
                    # --- REGISTRAZIONE NELLO STORICO ---
                    registra_invio_storico(email_cliente, targa_veicolo, tipo_campagna)
            else:
                stato_invio = "⚠️ Email Errata/Mancante"

            risultati_campagna.append({
                "Cliente": nome_cliente,
                "Email": email_cliente,
                "Targa": targa_veicolo,
                "Esito": stato_invio,
                "Orario": datetime.now().strftime("%H:%M:%S")
            })
            
            # Aggiornamento barra progresso
            percentuale = min((idx + 1) / totale, 1.0)
            progresso.progress(percentuale)
            status_text.text(f"Stato: {stato_invio} a {email_cliente}... ({idx+1}/{totale})")
            time.sleep(1)

        st.success(f"✅ Campagna completata! Successi: {successi} su {totale}")
        
        # --- GENERAZIONE REPORT ---
        df_report = pd.DataFrame(risultati_campagna)
        
        errori = df_report[df_report["Esito"] != "✅ Inviata"]
        if not errori.empty:
            st.warning(f"Attenzione: {len(errori)} invii non sono andati a buon fine.")
            st.dataframe(errori)

        try:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_report.to_excel(writer, index=False, sheet_name='Report')
            
            st.download_button(
                label="📥 Scarica Report Esiti (Excel)",
                data=buffer.getvalue(),
                file_name=f"Report_Feel_{datetime.now().strftime('%d-%m')}.xlsx",
                mime="application/vnd.ms-excel"
            )
        except Exception as e:
            st.error(f"Errore nella generazione del report: {e}")

else:
    st.info("⬆️ Scegli la campagna qui sopra e poi carica il file Excel dalla barra laterale per vedere i contatti.")
