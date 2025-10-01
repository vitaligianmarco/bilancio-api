from flask import Flask, request, jsonify
import base64
import io
import csv
import xml.etree.ElementTree as ET
import pdfplumber

app = Flask(__name__)

@app.route('/', methods=['POST'])
def parse_file():
    data = request.get_json()
    filename = data.get('filename', '')
    filetype = data.get('filetype', '')
    file_base64 = data.get('base64', '')

    try:
        file_bytes = base64.b64decode(file_base64)
    except Exception as e:
        return jsonify({"error": "Decodifica fallita", "message": str(e)}), 400

    def bytes_to_filelike(b: bytes):
        return io.BytesIO(b)

    if filename.lower().endswith('.csv') or filetype == 'text/csv':
        text = file_bytes.decode('utf-8', errors='ignore')
        reader = csv.DictReader(io.StringIO(text))
        row = next(reader, None)
        if not row:
            return jsonify({"error": "CSV vuoto"}), 400
        ricavi = float(row.get('ricavi', 0))
        costo_venduto = float(row.get('costo_venduto', 0))
        costo_lavoro = float(row.get('costo_lavoro', 0))
        valore_aggiunto = ricavi - costo_venduto
        mol = valore_aggiunto - costo_lavoro
        return jsonify({
            "conto_economico": {
                "ricavi": ricavi,
                "costo_venduto": costo_venduto,
                "costo_lavoro": costo_lavoro,
                "valore_aggiunto": valore_aggiunto,
                "MOL": mol
            }
        })

    if filename.lower().endswith('.xml') or filetype in ('application/xml', 'text/xml'):
        try:
            root = ET.fromstring(file_bytes)
        except Exception as e:
            return jsonify({"error": "Parsing XML fallito", "message": str(e)}), 400

        ricavi = float(root.findtext('.//Ricavi') or 0)
        costo_venduto = float(root.findtext('.//CostoVenduto') or 0)
        costo_lavoro = float(root.findtext('.//CostoLavoro') or 0)
        valore_aggiunto = ricavi - costo_venduto
        mol = valore_aggiunto - costo_lavoro
        return jsonify({
            "conto_economico": {
                "ricavi": ricavi,
                "costo_venduto": costo_venduto,
                "costo_lavoro": costo_lavoro,
                "valore_aggiunto": valore_aggiunto,
                "MOL": mol
            }
        })

    if filename.lower().endswith('.pdf') or filetype == 'application/pdf':
        try:
            file_obj = bytes_to_filelike(file_bytes)
            with pdfplumber.open(file_obj) as pdf:
                testo = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        testo += page_text + "\n"
        except Exception as e:
            return jsonify({"error": "Parsing PDF fallito", "message": str(e)}), 400

        ricavi = 0
        costo_venduto = 0
        costo_lavoro = 0
        for riga in testo.splitlines():
            r = riga.lower()
            if "ricavi" in r:
                try:
                    val = float(''.join(ch for ch in r if (ch.isdigit() or ch in ",.")))
                    ricavi = val
                except:
                    pass
            if "venduto" in r or "costo" in r:
                try:
                    val = float(''.join(ch for ch in r if (ch.isdigit() or ch in ",.")))
                    costo_venduto = val
                except:
                    pass
            if "lavoro" in r:
                try:
                    val = float(''.join(ch for ch in r if (ch.isdigit() or ch in ",.")))
                    costo_lavoro = val
                except:
                    pass

        valore_aggiunto = ricavi - costo_venduto
        mol = valore_aggiunto - costo_lavoro

        return jsonify({
            "conto_economico": {
                "ricavi": ricavi,
                "costo_venduto": costo_venduto,
                "costo_lavoro": costo_lavoro,
                "valore_aggiunto": valore_aggiunto,
                "MOL": mol
            }
        })

    return jsonify({"error": "Formato non supportato", "filename": filename, "filetype": filetype}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
