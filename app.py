# -*- coding: utf-8 -*-
import os
import io
import base64
import uuid
from datetime import datetime
from flask import Flask, request, send_file, render_template_string, abort, redirect, url_for
from fpdf import FPDF

app = Flask(__name__)

pdf_storage = {}

translations = {
    'nl': {
        'title': 'Snelfactuurtje',
        'invoice_number': 'Factuurnummer',
        'date': 'Datum',
        'invoice_to': 'Factuur aan:',
        'description': 'Omschrijving',
        'quantity': 'Aantal',
        'price': 'Prijs',
        'vat_percent': 'BTW%',
        'amount': 'Bedrag',
        'subtotal': 'Subtotaal (excl. BTW):',
        'total_vat': 'Totaal BTW:',
        'total': 'Totaal (incl. BTW):',
        'greeting': 'Met vriendelijke groet,',
        'signature': 'Handtekening:',
        'company_info': 'Bedrijfsgegevens',
        'client_info': 'Klantgegevens',
        'service': 'Dienst',
        'price_per_unit': 'Prijs per stuk',
        'add_service': 'Dienst toevoegen',
        'signature_label': 'Handtekening',
        'clear_signature': 'Handtekening wissen',
        'download_invoice': 'Factuur Openen',
        'save_company': 'Bedrijfsgegevens opslaan',
        'clear_company': 'Bedrijfsgegevens wissen',
        'upload_logo': 'Upload jouw logo (optioneel)',
        'street': 'Straat en huisnummer',
        'postcode': 'Postcode',
        'city': 'Plaats',
        'country': 'Land',
        'kvk': 'KvK-nummer',
        'vat': 'BTW-nummer',
        'iban': 'IBAN-nummer',
        'client_name': 'Klantnaam',
        'language': 'Taal',
        'company_name': 'Bedrijfsnaam',
    },
    # Voeg hier andere talen toe, minimaal Engels:
    'en': {
        'title': 'Quick Invoice',
        'invoice_number': 'Invoice Number',
        'date': 'Date',
        'invoice_to': 'Invoice to:',
        'description': 'Description',
        'quantity': 'Quantity',
        'price': 'Price',
        'vat_percent': 'VAT%',
        'amount': 'Amount',
        'subtotal': 'Subtotal (excl. VAT):',
        'total_vat': 'Total VAT:',
        'total': 'Total (incl. VAT):',
        'greeting': 'Kind regards,',
        'signature': 'Signature:',
        'company_info': 'Company Information',
        'client_info': 'Client Information',
        'service': 'Service',
        'price_per_unit': 'Price per Unit',
        'add_service': 'Add Service',
        'signature_label': 'Signature',
        'clear_signature': 'Clear Signature',
        'download_invoice': 'Open Invoice',
        'save_company': 'Save Company Info',
        'clear_company': 'Clear Company Info',
        'upload_logo': 'Upload your logo (optional)',
        'street': 'Street and Number',
        'postcode': 'Postal Code',
        'city': 'City',
        'country': 'Country',
        'kvk': 'Chamber of Commerce Number',
        'vat': 'VAT Number',
        'iban': 'IBAN Number',
        'client_name': 'Client Name',
        'language': 'Language',
        'company_name': 'Company Name',
    }
}

class FactuurPDF(FPDF):
    def __init__(self, logo_stream=None, t=None):
        super().__init__()
        self.logo_stream = logo_stream
        self.t = t or translations['nl']
        # Voeg fonts toe (zorg dat fonts map bestaat en bevat deze bestanden!)
        self.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'fonts/DejaVuSans-Bold.ttf', uni=True)
        self.set_font('DejaVu', '', 11)

    def header_custom(self, bedrijfsnaam, straat, postcode, plaats, land, kvk, btw, iban):
        if self.logo_stream:
            try:
                self.logo_stream.seek(0)
                temp_logo_path = 'temp_logo.png'
                with open(temp_logo_path, 'wb') as f:
                    f.write(self.logo_stream.read())
                self.image(temp_logo_path, x=10, y=8, w=40)
                os.remove(temp_logo_path)
            except Exception as e:
                print(f"Fout bij laden van logo: {e}")
        self.set_font('DejaVu', 'B', 16)
        self.cell(0, 10, bedrijfsnaam, ln=True, align='R')
        self.set_font('DejaVu', '', 11)
        self.cell(0, 8, straat, ln=True, align='R')
        self.cell(0, 8, f"{postcode} {plaats}", ln=True, align='R')
        self.cell(0, 8, land, ln=True, align='R')
        self.cell(0, 8, f"KvK: {kvk} | BTW: {btw}", ln=True, align='R')
        self.cell(0, 8, f"IBAN: {iban}", ln=True, align='R')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)

    def factuur_body(self, factuurnummer, klantnaam, klant_straat, klant_postcode, klant_plaats, klant_land, diensten, bedrijfsnaam, handtekening_stream=None):
        t = self.t
        self.set_font('DejaVu', '', 11)
        self.cell(0, 8, f"{t['invoice_number']}: {factuurnummer}", ln=True)
        self.cell(0, 8, f"{t['date']}: {datetime.today().strftime('%d-%m-%Y')}", ln=True)
        self.ln(5)
        self.set_font('DejaVu', 'B', 12)
        self.cell(0, 8, t['invoice_to'], ln=True)
        self.set_font('DejaVu', '', 11)
        self.cell(0, 8, klantnaam, ln=True)
        self.cell(0, 8, klant_straat, ln=True)
        self.cell(0, 8, f"{klant_postcode} {klant_plaats}", ln=True)
        self.cell(0, 8, klant_land, ln=True)
        self.ln(10)

        self.set_fill_color(230, 230, 250)
        self.set_font('DejaVu', 'B', 11)
        self.cell(80, 10, t['description'], border=1, align='C', fill=True)
        self.cell(20, 10, t['quantity'], border=1, align='C', fill=True)
        self.cell(30, 10, t['price'], border=1, align='C', fill=True)
        self.cell(20, 10, t['vat_percent'], border=1, align='C', fill=True)
        self.cell(30, 10, t['amount'], border=1, align='C', fill=True)
        self.ln()

        self.set_font('DejaVu', '', 11)
        subtotaal = 0
        totaal_btw = 0
        for dienst, aantal, prijs, btw_percentage in diensten:
            bedrag_excl = aantal * prijs
            btw_bedrag = bedrag_excl * (btw_percentage / 100)
            bedrag_incl = bedrag_excl + btw_bedrag
            self.cell(80, 10, dienst, border=1)
            self.cell(20, 10, str(aantal), border=1, align='C')
            self.cell(30, 10, f"{prijs:.2f}", border=1, align='R')
            self.cell(20, 10, f"{btw_percentage}%", border=1, align='C')
            self.cell(30, 10, f"{bedrag_incl:.2f}", border=1, align='R')
            self.ln()
            subtotaal += bedrag_excl
            totaal_btw += btw_bedrag

        totaal = subtotaal + totaal_btw
        self.ln(5)
        self.set_font('DejaVu', 'B', 12)
        self.cell(150, 10, t['subtotal'], align='R')
        self.cell(30, 10, f"{subtotaal:.2f} EUR", ln=True, align='R')
        self.cell(150, 10, t['total_vat'], align='R')
        self.cell(30, 10, f"{totaal_btw:.2f} EUR", ln=True, align='R')
        self.cell(150, 10, t['total'], align='R')
        self.cell(30, 10, f"{totaal:.2f} EUR", ln=True, align='R')
        self.ln(20)
        self.set_font('DejaVu', '', 11)
        self.cell(0, 8, t['greeting'], ln=True)
        self.cell(0, 8, bedrijfsnaam, ln=True)

        if handtekening_stream:
            if self.get_y() > 250:
                self.add_page()
            self.ln(20)
            self.cell(0, 8, t['signature'], ln=True)
            temp_handtekening_path = 'temp_handtekening.png'
            with open(temp_handtekening_path, 'wb') as f:
                f.write(handtekening_stream.getbuffer())
            self.image(temp_handtekening_path, x=10, y=self.get_y(), w=80)
            os.remove(temp_handtekening_path)

def get_translation():
    lang = request.args.get('lang', 'nl').lower()
    if lang not in translations:
        lang = 'nl'
    return translations[lang], lang

@app.route('/', methods=['GET'])
def index():
    t, lang = get_translation()
    html_content = f'''
<!doctype html>
<html lang="{lang}" {'dir="rtl"' if lang == 'ar' else ''}>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{t["title"]}</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap" rel="stylesheet" />
  <style>
    body {{
      background: linear-gradient(135deg, #e0f7fa 0%, #ffffff 100%);
      font-family: 'Poppins', sans-serif;
      margin: 0; padding: 20px;
      min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      {'direction: rtl;' if lang == 'ar' else ''}
    }}
    .container {{
      width: 100%; max-width: 900px;
      background: white;
      padding: 30px;
      border-radius: 15px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }}
    h1 {{text-align: center; color: #007bff; margin-bottom: 30px;}}
    form {{display: flex; flex-direction: column; gap: 20px;}}
    .block {{padding: 20px; border-radius: 12px; margin-bottom: 20px; background-color: #f9f9f9;}}
    .bedrijf {{background-color: #e6f2ff;}}
    .klant {{background-color: #fff3e6;}}
    label {{
      display: block;
      margin-top: 10px;
      font-weight: 500;
      font-size: 14px;
      color: #555;
      {'text-align: right;' if lang == 'ar' else ''}
    }}
    input, select {{
      width: 100%;
      padding: 12px;
      margin-top: 5px;
      border-radius: 8px;
      border: 1px solid #ccc;
      box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
      font-size: 14px;
      box-sizing: border-box;
      {'direction: rtl; text-align: right;' if lang == 'ar' else ''}
    }}
    .dienst-block {{
      border: 1px solid #ccc;
      padding: 15px;
      border-radius: 12px;
      margin-top: 15px;
      background-color: #f9f9f9;
      position: relative;
      box-shadow: 0 2px 6px rgba(0,0,0,0.05);
      {'direction: rtl;' if lang == 'ar' else ''}
    }}
    .remove-btn {{
      position: absolute;
      top: 10px;
      right: 10px;
      background-color: red;
      color: white;
      border: none;
      border-radius: 50%;
      width: 30px;
      height: 30px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      {'right: auto; left: 10px;' if lang == 'ar' else ''}
    }}
    button {{
      padding: 15px;
      border: none;
      border-radius: 30px;
      background-color: #007bff;
      color: white;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      transition: background 0.3s;
    }}
    button:hover {{
      background-color: #0056b3;
    }}
    .button-group {{
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: 15px;
    }}
    canvas {{
      border: 2px solid #ccc;
      border-radius: 8px;
      margin-top: 10px;
      width: 100%;
      height: 200px;
      {'direction: ltr;' if lang == 'ar' else ''}
    }}
    .form-grid {{
      display: block;
    }}
    @media (min-width: 768px) {{
      .form-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
      }}
    }}
    .language-select {{
      margin-bottom: 20px;
      font-size: 14px;
      text-align: {'right' if lang == 'ar' else 'left'};
    }}
  </style>
</head>
<body>
  <div class="container">
    <form id="languageForm" class="language-select" method="GET" action="/">
      <label for="langSelect">{t["language"]}:</label>
      <select id="langSelect" name="lang" onchange="document.getElementById('languageForm').submit()">
        <option value="nl" {'selected' if lang == 'nl' else ''}>Nederlands</option>
        <option value="de" {'selected' if lang == 'de' else ''}>Deutsch</option>
        <option value="fr" {'selected' if lang == 'fr' else ''}>Français</option>
        <option value="it" {'selected' if lang == 'it' else ''}>Italiano</option>
        <option value="es" {'selected' if lang == 'es' else ''}>Español</option>
        <option value="pt" {'selected' if lang == 'pt' else ''}>Português</option>
        <option value="ja" {'selected' if lang == 'ja' else ''}>日本語</option>
        <option value="zh" {'selected' if lang == 'zh' else ''}>中文</option>
        <option value="ar" {'selected' if lang == 'ar' else ''}>العربية</option>
        <option value="en" {'selected' if lang == 'en' else ''}>English</option>
      </select>
    </form>

    <h1>{t["title"]}</h1>
    <form method="POST" action="/generate?lang={lang}" enctype="multipart/form-data" id="invoiceForm">
      <label>{t["invoice_number"]}:</label>
      <input name="factuurnummer" placeholder="Bijv. FACT-2025-001" required />

      <div class="form-grid">
        <div class="block bedrijf">
          <h2>{t["company_info"]}</h2>
          <label>{t["company_name"]}:</label>
          <input name="bedrijfsnaam" required />
          <label>{t["street"]}:</label>
          <input name="straat" required />
          <label>{t["postcode"]}:</label>
          <input name="postcode" required />
          <label>{t["city"]}:</label>
          <input name="plaats" required />
          <label>{t["country"]}:</label>
          <input name="land" required />
          <label>{t["kvk"]}:</label>
          <input name="kvk" required />
          <label>{t["vat"]}:</label>
          <input name="btw" required />
          <label>{t["iban"]}:</label>
          <input name="iban" required />
          <label>{t["upload_logo"]}:</label>
          <input type="file" name="logo" />

          <div class="button-group">
            <button type="button" onclick="saveCompanyInfo()">{t["save_company"]}</button>
            <button type="button" onclick="clearCompanyInfo()">{t["clear_company"]}</button>
          </div>
        </div>

        <div class="block klant">
          <h2>{t["client_info"]}</h2>
          <label>{t["client_name"]}:</label>
          <input name="klantnaam" required />
          <label>{t["street"]}:</label>
          <input name="klant_straat" required />
          <label>{t["postcode"]}:</label>
          <input name="klant_postcode" required />
          <label>{t["city"]}:</label>
          <input name="klant_plaats" required />
          <label>{t["country"]}:</label>
          <input name="klant_land" required />
        </div>
      </div>

      <div id="diensten"></div>
      <button type="button" onclick="voegDienstToe()">{t["add_service"]}</button>

      <h2>{t["signature_label"]}</h2>
      <canvas id="signature-pad"></canvas>
      <button type="button" onclick="clearSignature()">{t["clear_signature"]}</button>
      <input type="hidden" id="handtekening" name="handtekening" />

      <button type="submit">{t["download_invoice"]}</button>
    </form>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>
  <script>
    let dienstIndex = 0;
    function voegDienstToe() {{
      const container = document.getElementById('diensten');
      const div = document.createElement('div');
      div.className = 'dienst-block';
      div.innerHTML = `
        <button type='button' class='remove-btn' onclick='this.parentNode.remove()'>×</button>
        <label>{t["service"]}:</label>
        <input name='dienst_${{dienstIndex}}' required />
        <label>{t["quantity"]}:</label>
        <input name='aantal_${{dienstIndex}}' type='number' required />
        <label>{t["price_per_unit"]}:</label>
        <input name='prijs_${{dienstIndex}}' type='number' step='0.01' required />
        <label>{t["vat_percent"]}:</label>
        <select name='btw_${{dienstIndex}}'>
          <option value='0'>0%</option>
          <option value='9'>9%</option>
          <option value='21' selected>21%</option>
        </select>
      `;
      container.appendChild(div);
      dienstIndex++;
    }}

    var canvas = document.getElementById('signature-pad');
    var signaturePad;

    function resizeCanvas() {{
      if (!signaturePad) return;
      const data = signaturePad.toData();
      const ratio = Math.max(window.devicePixelRatio || 1, 1);
      canvas.width = canvas.offsetWidth * ratio;
      canvas.height = canvas.offsetHeight * ratio;
      canvas.getContext('2d').scale(ratio, ratio);
      signaturePad.clear();
      signaturePad.fromData(data);
    }}

    window.addEventListener('resize', resizeCanvas);

    window.onload = function () {{
      signaturePad = new SignaturePad(canvas);
      resizeCanvas();
      loadCompanyInfo();
    }};

    function saveSignature() {{
      if (!signaturePad.isEmpty()) {{
        var dataURL = signaturePad.toDataURL();
        document.getElementById('handtekening').value = dataURL;
      }}
    }}

    function clearSignature() {{
      signaturePad.clear();
    }}

    function saveCompanyInfo() {{
      const fields = ['bedrijfsnaam', 'straat', 'postcode', 'plaats', 'land', 'kvk', 'btw', 'iban'];
      fields.forEach((field) => {{
        const value = document.querySelector(`[name="${{field}}"]`).value;
        localStorage.setItem(field, value);
      }});
      alert('{t["save_company"]}!');
    }}

    function loadCompanyInfo() {{
      const fields = ['bedrijfsnaam', 'straat', 'postcode', 'plaats', 'land', 'kvk', 'btw', 'iban'];
      fields.forEach((field) => {{
        const saved = localStorage.getItem(field);
        if (saved) {{
          document.querySelector(`[name="${{field}}"]`).value = saved;
        }}
      }});
    }}

    function clearCompanyInfo() {{
      const fields = ['bedrijfsnaam', 'straat', 'postcode', 'plaats', 'land', 'kvk', 'btw', 'iban'];
      fields.forEach((field) => {{
        localStorage.removeItem(field);
        document.querySelector(`[name="${{field}}"]`).value = '';
      }});
      alert('{t["clear_company"]}!');
    }}

    document.getElementById('invoiceForm').addEventListener('submit', function (e) {{
      saveSignature();
    }});
  </script>
</body>
</html>
'''
    return render_template_string(html_content)

@app.route('/generate', methods=['POST'])
def generate_pdf():
    try:
        factuurnummer = request.form['factuurnummer']
        bedrijfsnaam = request.form['bedrijfsnaam']
        straat = request.form['straat']
        postcode = request.form['postcode']
        plaats = request.form['plaats']
        land = request.form['land']
        kvk = request.form['kvk']
        btw = request.form['btw']
        iban = request.form['iban']

        klantnaam = request.form['klantnaam']
        klant_straat = request.form['klant_straat']
        klant_postcode = request.form['klant_postcode']
        klant_plaats = request.form['klant_plaats']
        klant_land = request.form['klant_land']

        diensten = []
        index = 0
        while f'dienst_{index}' in request.form:
            dienst = request.form.get(f'dienst_{index}')
            aantal = int(request.form.get(f'aantal_{index}', 1))
            prijs = float(request.form.get(f'prijs_{index}', 0))
            btw_percentage = float(request.form.get(f'btw_{index}', 21))
            diensten.append((dienst, aantal, prijs, btw_percentage))
            index += 1

        logo_file = request.files.get('logo')
        logo_stream = None
        if logo_file and logo_file.filename:
            logo_stream = io.BytesIO(logo_file.read())
            logo_stream.seek(0)

        handtekening_data = request.form.get('handtekening')
        handtekening_stream = None
        if handtekening_data and handtekening_data.startswith("data:image/png;base64,"):
            header, encoded = handtekening_data.split(",", 1)
            handtekening_bytes = base64.b64decode(encoded)
            handtekening_stream = io.BytesIO(handtekening_bytes)

        t, lang = get_translation()

        pdf = FactuurPDF(logo_stream, t)
        pdf.add_page()
        pdf.header_custom(bedrijfsnaam, straat, postcode, plaats, land, kvk, btw, iban)
        pdf.factuur_body(factuurnummer, klantnaam, klant_straat, klant_postcode, klant_plaats, klant_land, diensten, bedrijfsnaam, handtekening_stream)

        pdf_data = pdf.output(dest='S').encode('utf-8')

        pdf_id = str(uuid.uuid4())
        pdf_storage[pdf_id] = pdf_data

        return redirect(url_for('serve_pdf', pdf_id=pdf_id))
    except Exception as e:
        abort(400, description=f"Fout bij verwerken van factuur: {e}")

@app.route('/pdf/<pdf_id>', methods=['GET'])
def serve_pdf(pdf_id):
    pdf_data = pdf_storage.get(pdf_id)
    if not pdf_data:
        abort(404)
    return send_file(
        io.BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=False,
        download_name='factuur.pdf'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
