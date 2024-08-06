import streamlit as st
import xml.etree.ElementTree as ET
import requests
import json
import logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_xml_invoice(xml_content):
    root = ET.fromstring(xml_content)
    
    def find_element(parent, tag):
        for elem in parent.iter():
            if elem.tag.endswith(tag):
                return elem
        return None

    def find_all_elements(parent, tag):
        return [elem for elem in parent.iter() if elem.tag.endswith(tag)]

    descriptions = []
    for line in find_all_elements(root, 'DettaglioLinee'):
        prezzo_totale_elem = find_element(line, 'PrezzoTotale')
        if prezzo_totale_elem is not None:
            prezzo_totale = float(prezzo_totale_elem.text)
            if prezzo_totale > 0:
                descrizione_elem = find_element(line, 'Descrizione')
                if descrizione_elem is not None:
                    descriptions.append(descrizione_elem.text)
    
    return descriptions

def call_api(description, attivita_svolta):
    url = "http://143.198.98.88/v1/chat-messages"
    headers = {
        "Authorization": "Bearer app-nyABMEXuDbSHGLbc9yxTF4z5",
        "Content-Type": "application/json"
    }
    payload = {
        "user": "ContAI",
        "query": f"Descrizioni linee fattura:\n{description}",
        "inputs": {"attivita_svolta": attivita_svolta},
        "response_mode": "blocking"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Solleva un'eccezione per risposte HTTP non riuscite
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Errore nella chiamata API: {e}")
        return None

def extract_conti_possibili(api_response):
    if api_response is None:
        return []

    logger.info(f"Risposta API ricevuta: {api_response}")

    try:
        if 'answer' in api_response:
            answer = json.loads(api_response['answer'])
            return answer.get('conti_possibili', [])
        else:
            logger.warning("Chiave 'answer' non trovata nella risposta API")
            return []
    except json.JSONDecodeError as e:
        logger.error(f"Errore nel parsing JSON della risposta API: {e}")
        return []
    except Exception as e:
        logger.error(f"Errore inaspettato nell'elaborazione della risposta API: {e}")
        return []

def main():
    st.title("Analisi Descrizioni Fatture XML")
    
    attivita_svolta = st.text_input("Inserisci la tua attività svolta:")
    
    uploaded_files = st.file_uploader("Carica le fatture XML", accept_multiple_files=True, type=['xml'])
    
    if uploaded_files and attivita_svolta:
        for uploaded_file in uploaded_files:
            st.write(f"Analisi della fattura: {uploaded_file.name}")
            
            xml_content = uploaded_file.read().decode('utf-8')
            descriptions = parse_xml_invoice(xml_content)
            
            if descriptions:
                st.subheader("Analisi delle fatture")
                for description in descriptions:
                    st.write(f"Descrizione linea fattura: {description}")
                    
                    api_response = call_api(description, attivita_svolta)
                    if api_response:
                        conti_possibili = extract_conti_possibili(api_response)
                        
                        if conti_possibili:
                            st.write("Conti possibili individuati:")
                            for conto in conti_possibili:
                                st.write(f"- Numero conto: {conto['numero_conto']}, Descrizione: {conto['descrizione']}")
                        else:
                            st.write("Nessun conto possibile trovato per questa descrizione.")
                    else:
                        st.write("Errore nella chiamata API. Controlla i log per maggiori dettagli.")
                    
                    st.write("---")
            else:
                st.write("Nessuna linea con importo > 0 trovata in questa fattura.")
            
            st.write("===== Fine dell'analisi di questa fattura =====")

if __name__ == "__main__":
    main()