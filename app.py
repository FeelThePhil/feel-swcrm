import streamlit as st
import pandas as pd
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import gspread 
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(
    page_title="Feel - Gestione Officina",
    page_icon="😈",
    layout="wide",
    initial_sidebar_state="expanded" 
)

import streamlit.components.v1 as components

st.markdown("""
    <style>
    header[data-testid="stHeader"], .stAppDeployButton, #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }
    .main .block-container {
        padding-top: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

components.html(
    """
    <script>
    const removeElements = () => {
        const badges = window.parent.document.querySelectorAll('[data-testid="stStatusWidget"], [data-testid="stToolbar"], #viewerBadge');
        badges.forEach(el => el.style.display = 'none');
        const toolbar = window.parent.document.querySelector('div[data-testid="stToolbar"]');
        if (toolbar) toolbar.style.display = 'none';
    };
    removeElements();
    setInterval(removeElements, 1000);
    </script>
    """,
    height=0,
    width=0,
)

def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            logo_url = "https://officinefiore.it/wp-content/uploads/2025/05/logo-fiore.svg" 
            st.markdown(f'<div style="text-align: center;"><img src="{logo_url}" width="200"></div>', unsafe_allow_html=True)
            st.title("Accesso Riservato Feel")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Entra"):
                if username == st.secrets["USER_LOGIN"] and password == st.secrets["USER_PASSWORD"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("Credenziali non valide")
        return False
    return True

if not check_password():
    st.stop()

# --- CUORE DI FEEL ---
logo_url = "https://officinefiore.it/wp-content/uploads/2025/05/logo-fiore.svg" 
st.markdown(f'<div style="text-align: center;"><img src="{logo_url}" width="200"></div>', unsafe_allow_html=True)
st.title("Benvenuto nel cuore di Feel")

EMAIL_MITTENTE = "feel.swcrm@gmail.com"
PASSWORD_APP = st.secrets["EMAIL_PASSWORD"] 

def invia_email(destinatario, oggetto, messaggio):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"OFFICINE FIORE IVECO <{EMAIL_MITTENTE}>"
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

def get_google_sheet():
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open("feel_storico_invii").worksheet("Log")
        return sh
    except:
        return None

def verifica_presenza_storico(identificativo, tipo_attuale):
    sheet = get_google_sheet()
    if not sheet: return False
    try:
        records = sheet.get_all_records()
        if not records: return False
        df_log = pd.DataFrame(records)
        df_log.columns = df_log.columns.str.strip().str.lower()
        identificativo_pulito = str(identificativo).strip().lower()
        df_log['data_invio'] = pd.to_datetime(df_log['data_invio'], errors='coerce').dt.date
        limite = (datetime.now() - timedelta(days=60)).date()
        duplicati = df_log[
            ((df_log['email'].str.lower() == identificativo_pulito) | 
             (df_log['targa'].str.lower() == identificativo_pulito)) & 
            (df_log['tipo_campagna'] == tipo_attuale) &
            (df_log['data_invio'] > limite)
        ]
        return not duplicati.empty
    except:
        return False

def registra_invio_storico(email, targa, tipo):
    sheet = get_google_sheet()
    if sheet:
        try:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d"), str(email).strip(), str(targa).strip(), str(tipo)])
            time.sleep(1.2)
        except Exception as e:
            st.error(f"❌ Errore tecnico nella scrittura su Google Sheets: {e}")

st.title("🛡️ Feel - Gestione Lead & Comunicazioni")
st.markdown("---")
st.subheader("🚀 1. Scegli la Campagna")
col1, col2 = st.columns(2)

with col1:
    tipo_campagna = st.selectbox("Cosa vuoi fare oggi?", ["Revisione", "Recensione Post-Revisione", "Follow-up Post Intervento", "Comunicazione Generica"], key="selezione_tipo_campagna")

if tipo_campagna == "Revisione":
    oggetto_default = "⚠️ Scadenza Revisione Ministeriale - Officine Fiore"
    testo_default = ("Gentile [Nome],\n\nda un controllo nei nostri archivi, le ricordiamo che il Suo veicolo [Tipo] "
                     "targato [Targa] ha la revisione in scadenza entro la fine del mese prossimo.\n\n"
                     "Considerando che l'ultimo intervento risulta effettuato in data [Data_Ultima], "
                     "Le suggeriamo di contattarci al più presto per fissare un appuntamento ed evitando sanzioni e fermi macchina.\n\n"
                     "Restiamo a Sua completa disposizione.\n\nCordiali saluti,\nOfficine Fiore")
elif tipo_campagna == "Recensione Post-Revisione":
    oggetto_default = "✅ Revisione Regolare: il Suo veicolo [Targa] è pronto"
    testo_default = (
        "Gentile [Nome],\n\n"
        "il Suo veicolo [Targa] ha superato la revisione con ESITO REGOLARE! ✅\n\n"
        "Le pratiche sono già state trasmesse al Portale dell'Automobilista.\n\n"
        "Se è soddisfatto del nostro servizio, ci lascerebbe una recensione veloce su Google? Bastano 20 secondi e per noi è un aiuto prezioso.\n\n"
        "⭐️ RECENSISCI QUI:\n"
        " https://g.page/r/CWAYAR1IJMI2EBM/review \n\n"
        "Grazie per la fiducia e buon viaggio con Officine Fiore!"
    )
elif tipo_campagna == "Follow-up Post Intervento":
    oggetto_default = "Tutto bene con il tuo veicolo? - Officine Fiore"
    testo_default = (
        "Ciao [Nome],\n\n"
        "sono passati pochi giorni dall'intervento sul tuo mezzo [Targa].\n"
        "Volevamo solo assicurarci che sia tutto a posto e che tu sia soddisfatto.\n\n"
        "Ti rubiamo solo 30 secondi (promesso!) per 3 domande veloci. Ci aiuti a migliorare?\n\n"
        "👉 CLICCA QUI PER IL SONDAGGIO:\n"
        " https://forms.gle/VV6o9LsZ7ipDFcAX8 \n\n"
        "Grazie per la tua fiducia,\n"
        "Il Team di Officine Fiore"
    )
else:
    oggetto_default = "Novità dall'Officina"
    testo_default = "Ciao [Nome],\n\nvolevamo informarti sulle nostre ultime novità per la tua auto [Targa]. Passa a trovarci!"

testo_default += "\n\n---\nP.S. Abbiamo rinnovato la nostra casa online! Passa a trovarci su www.officinefiore.it per scoprire tutte le novità e i nostri servizi specializzati."

with col2:
    oggetto = st.text_input("Oggetto Email", oggetto_default)
corpo_mail = st.text_area("Personalizza il messaggio (usa [Nome] e [Targa])", testo_default, height=180)

st.markdown("---")
st.sidebar.header("📂 Carica Dati")
file_caricato = st.sidebar.file_uploader("Carica Excel Lead per questa campagna", type=['xlsx'])

if file_caricato:
    df = pd.read_excel(file_caricato)
    df.columns = df.columns.str.strip().str.lower()
    if tipo_campagna == "Revisione":
        if 'ultima_revisione' in df.columns:
            df['ultima_revisione'] = pd.to_datetime(df['ultima_revisione'])
            mese_target = (datetime.now() + relativedelta(months=1)).month
            df = df[df['ultima_revisione'].dt.month == mese_target].copy()
            st.success(f"🎯 Filtro Revisioni: Estratti {len(df)} veicoli.")
        else:
            st.error("Manca la colonna 'ultima_revisione'.")
            st.stop()
    
    st.write("### 📋 Lista Lead Pronti")
    st.dataframe(df, use_container_width=True, height=400) 

    if st.button(f"AVVIA INVIO MASSIVO ({len(df)} email)", key="btn_invio_finale_stabile"):
        progresso = st.progress(0.0)
        status_text = st.empty()
        risultati_campagna = [] 
        successi = 0
        totale = len(df)
        gia_elaborati_in_questa_sessione = set()
        
        for idx, (i, riga) in enumerate(df.iterrows()):
            nome_cliente = str(riga['nome']) if 'nome' in riga else "Cliente"
            email_cliente = str(riga['email']).strip().lower() if 'email' in riga else ""
            targa_veicolo = str(riga['targa']).strip().upper() if 'targa' in riga else "N.D."
            tipo_veicolo = str(riga['tipo']) if 'tipo' in riga else "veicolo"
            data_ultima = riga['ultima_revisione'].strftime('%d/%m/%Y') if 'ultima_revisione' in riga else "N.D."
            
            gia_inviato = False
            if email_cliente in gia_elaborati_in_questa_sessione or targa_veicolo in gia_elaborati_in_questa_sessione:
                gia_inviato = True
                motivo_salto = "⏭️ Saltato (Duplicato in Excel)"
            elif tipo_campagna != "Comunicazione Generica" and (verifica_presenza_storico(email_cliente, tipo_campagna) or verifica_presenza_storico(targa_veicolo, tipo_campagna)):
                gia_inviato = True
                motivo_salto = "⏭️ Saltato (Già inviato <60gg)"

            if gia_inviato:
                risultati_campagna.append({"Cliente": nome_cliente, "Email": email_cliente, "Targa": targa_veicolo, "Esito": motivo_salto, "Orario": datetime.now().strftime("%H:%M:%S")})
                continue 

            if "@" in email_cliente and "." in email_cliente:
                
                oggetto_p = oggetto.replace("[Targa]", targa_veicolo).replace("[Nome]", nome_cliente)
                
                
                msg_p = corpo_mail.replace("[Nome]", nome_cliente).replace("[Targa]", targa_veicolo).replace("[Tipo]", tipo_veicolo).replace("[Data_Ultima]", data_ultima)
                
                
                if invia_email(email_cliente, oggetto_p, msg_p):
                    successi += 1
                    stato_invio = "✅ Inviata"
                    registra_invio_storico(email_cliente, targa_veicolo, tipo_campagna)
                    gia_elaborati_in_questa_sessione.add(email_cliente)
                    gia_elaborati_in_questa_sessione.add(targa_veicolo)
                else: stato_invio = "❌ Errore SMTP"
            else: stato_invio = "⚠️ Email Errata"

            risultati_campagna.append({"Cliente": nome_cliente, "Email": email_cliente, "Targa": targa_veicolo, "Esito": stato_invio, "Orario": datetime.now().strftime("%H:%M:%S")})
            progresso.progress(min((idx + 1) / totale, 1.0))
            status_text.text(f"Stato: {stato_invio} a {email_cliente}... ({idx+1}/{totale})")
            time.sleep(1.8)

        st.success(f"✅ Campagna completata! Successi: {successi} su {totale}")
        df_report = pd.DataFrame(risultati_campagna)
        st.dataframe(df_report)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_report.to_excel(writer, index=False, sheet_name='Report')
        st.download_button(label="📥 Scarica Report", data=buffer.getvalue(), file_name=f"Report_Feel_{datetime.now().strftime('%d-%m')}.xlsx", mime="application/vnd.ms-excel")
else:
    st.info("⬆️ Scegli la campagna e carica il file Excel.")
# --- SEZIONE ANALISI PERFORMANCE  ---
st.write("") 
st.write("") 
st.divider()
st.header("📊 Pannello Analisi Comunicazioni")

# Funzione rapida per caricare i dati per le statistiche
sheet_stat = get_google_sheet()
if sheet_stat:
    try:
        records_stat = sheet_stat.get_all_records()
        if records_stat:
            df_stats_log = pd.DataFrame(records_stat)
            
            # 1. Conteggio invii per tipo
            conteggi = df_stats_log['tipo_campagna'].value_counts()
            invii_followup = conteggi.get("Follow-up Post Intervento", 0)
            invii_recensioni = conteggi.get("Recensione Post-Revisione", 0)

            # 2. Input manuale risultati
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                risposte_form = st.number_input("Compilazioni Google Form ricevute:", min_value=0, value=14, help="Inserisci il numero di risposte che vedi sul pannello Google Form")
            with col_in2:
                nuove_recensioni = st.number_input("Nuove Recensioni Google ottenute:", min_value=0, value=0, help="Inserisci quante nuove recensioni hai ricevuto da quando hai iniziato")

            # 3. Visualizzazione Metriche
            st.write("### Risultati e Conversioni")
            m1, m2, m3 = st.columns(3)
            
            with m1:
                st.metric("Mail Follow-up", invii_followup)
                if invii_followup > 0:
                    perc_f = (risposte_form / invii_followup) * 100
                    st.write(f"🎯 Efficacia: **{perc_f:.1f}%**")
            
            with m2:
                st.metric("Richieste Recensione", invii_recensioni)
                if invii_recensioni > 0:
                    perc_r = (nuove_recensioni / invii_recensioni) * 100
                    st.write(f"🎯 Efficacia: **{perc_r:.1f}%**")
                    
            with m3:
                st.metric("Totale Database Feel", len(df_stats_log))
                st.write("Righe totali nel Log")

            # Messaggio di incoraggiamento
            if invii_followup > 0 and (risposte_form / invii_followup) > 0.10:
                st.balloons()
                st.success("Complimenti! Il tuo tasso di risposta è superiore al 10%, un ottimo risultato per l'officina!")
        else:
            st.warning("Il file di log è vuoto. Inizia a inviare per vedere le statistiche.")
    except Exception as e:
        st.error(f"Non è stato possibile caricare le statistiche: {e}")
else:
    st.error("Connessione al file di log fallita. Controlla le credenziali Google.")

# --- SEZIONE VERSIONING  ---



st.write("<br>" * 10, unsafe_allow_html=True) 
st.divider()


with st.expander("📜 Technical Release Notes (Build History)"):
    st.markdown("""
        **Current Build:** `V1.7 `
        
        ---
        **Cronologia Sviluppo:**
        * **V1.7 (Bug Fix)** - Risolto mancato rimpiazzo segnaposto `[Targa]` nell'oggetto email e allineamento case-sensitivity statistiche.
        * **V1.6 (Marketing & UX)** - Ottimizzazione copywriting, integrazione link sito `officinefiore.it` e fix case-sensitivity selettore campagne.
        * **V1.5 (UX & Celebration)** - Implementazione modulo **Analisi Comunicazioni** campagna *Richiesta Recensione* e triggering effetti particellari.
        * **V1.4 (Security & Integrity)** - Messa in sicurezza dei file di Log e hardening della scrittura su Database per prevenire corruzioni dati.
        * **V1.3 (API Debugging)** - Refactoring del modulo SMTP/Gmail: risoluzione conflitti di autenticazione e gestione eccezioni API.
        * **V1.2 (Log & Persistence)** - Implementazione del sistema di Log storico per il tracciamento univoco degli invii e prevenzione ridondanze.
        * **V1.1 (Core Architecture)** - Sviluppo dei template dinamici per le campagne (*Revisione*, *Follow-up*) e mappatura variabili `[Nome]` / `[Targa]`.
        * **V1.0 (Infrastructure)** - Setup ambiente su GitHub, configurazione Database SQLite e interfacciamento iniziale con le API Google.
        
        ---
        *Made with ❤️ for Officine Fiore*
    """)
