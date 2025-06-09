# -*- coding: utf-8 -*-
import os
import io
import base64
import uuid
from datetime import datetime
from flask import Flask, request, render_template_string, send_file, redirect, url_for, abort
from weasyprint import HTML, CSS

app = Flask(__name__)
app.debug = True  # Debug aan voor foutmeldingen tijdens development
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
    'en': {
        'title': 'Quick Invoice',
        'invoice_number': 'Invoice Number',
        'date': 'Date',
        'invoice_to': 'Invoice To:',
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
    },
    # Voeg hier je andere talen toe zoals je al had...
}

def get_translation():
    lang = request.args.get('lang', 'nl').lower()
    if lang not in translations:
        lang = 'nl'
    return translations[lang], lang

@app.route('/', methods=['GET'])
def index():
    t, lang = get_translation()
    return render_template_string(INDEX_HTML, t=t, lang=lang)

@app.route('/generate', methods=['POST'])
def generate_pdf():
    try:
        t, lang = get_translation()

        factuurnummer = request.form.get('factuurnummer')
        bedrijfsnaam = request.form.get('bedrijfsnaam')
        straat = request.form.get('straat')
        postcode = request.form.get('postcode')
        plaats = request.form.get('plaats')
        land = request.form.get('land')
        kvk = request.form.get('kvk')
        btw = request.form.get('btw')
        iban = request.form.get('iban')

        klantnaam = request.form.get('klantnaam')
        klant_straat = request.form.get('klant_straat')
        klant_postcode = request.form.get('klant_postcode')
        klant_plaats = request.form.get('klant_plaats')
        klant_land = request.form.get('klant_land')

        diensten = []
        index = 0
        while f'dienst_{index}' in request.form:
            dienst = request.form.get(f'dienst_{index}')
            try:
                aantal = int(request.form.get(f'aantal_{index}', 1))
            except:
                aantal = 1
            try:
                prijs = float(request.form.get(f'prijs_{index}', 0))
            except:
                prijs = 0.0
            try:
                btw_percentage = float(request.form.get(f'btw_{index}', 21))
            except:
                btw_percentage = 21
            diensten.append((dienst, aantal, prijs, btw_percentage))
            index += 1

        logo_file = request.files.get('logo')
        logo_data = None
        if logo_file and logo_file.filename:
            logo_data = base64.b64encode(logo_file.read()).decode('utf-8')

        handtekening_data = request.form.get('handtekening')

        html_invoice = render_template_string(PDF_HTML,
                                              t=t,
                                              factuurnummer=factuurnummer,
                                              bedrijfsnaam=bedrijfsnaam,
                                              straat=straat,
                                              postcode=postcode,
                                              plaats=plaats,
                                              land=land,
                                              kvk=kvk,
                                              btw=btw,
                                              iban=iban,
                                              klantnaam=klantnaam,
                                              klant_straat=klant_straat,
                                              klant_postcode=klant_postcode,
                                              klant_plaats=klant_plaats,
                                              klant_land=klant_land,
                                              diensten=diensten,
                                              logo_data=logo_data,
                                              handtekening_data=handtekening_data,
                                              lang=lang)

        pdf_file = HTML(string=html_invoice).write_pdf(stylesheets=[CSS(string=PDF_CSS)])

        pdf_id = str(uuid.uuid4())
        pdf_storage[pdf_id] = pdf_file

        return redirect(url_for('serve_pdf', pdf_id=pdf_id, lang=lang))
    except Exception as e:
        import traceback
        traceback.print_exc()
        abort(500, description=f"Fout bij verwerken van factuur: {e}")

@app.route('/pdf/<pdf_id>', methods=['GET'])
def serve_pdf(pdf_id):
    pdf_data = pdf_storage.get(pdf_id)
    if not pdf_data:
        abort(404)
    lang = request.args.get('lang', 'nl')
    return send_file(io.BytesIO(pdf_data),
                     mimetype='application/pdf',
                     as_attachment=False,
                     download_name='factuur.pdf')

@app.context_processor
def inject_now():
    return {'now': datetime.today().strftime('%d-%m-%Y')}

# Vervang hieronder door jouw originele INDEX_HTML, PDF_HTML en PDF_CSS strings

INDEX_HTML = ''' 
<!doctype html>
<html lang="{{ lang }}" dir="{{ 'rtl' if lang == 'ar' else 'ltr' }}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{ t.title }}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap&subset=arabic" rel="stylesheet" />
<style>
  body {
    background: linear-gradient(135deg, #e0f7fa 0%, #ffffff 100%);
    font-family: 'Poppins', sans-serif;
    margin: 0; padding: 20px;
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    direction: {{ 'rtl' if lang == 'ar' else 'ltr' }};
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
  }
  .container {
    width: 100%; max-width: 900px;
    background: white;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  }
  h1 {text-align: center; color: #007bff; margin-bottom: 30px;}
  form {display: flex; flex-direction: column; gap: 20px;}
  .block {padding: 20px; border-radius: 12px; margin-bottom: 20px; background-color: #f9f9f9;}
  .bedrijf {background-color: #e6f2ff;}
  .klant {background-color: #fff3e6;}
  label {
    display: block;
    margin-top: 10px;
    font-weight: 500;
    font-size: 14px;
    color: #555;
  }
  input, select {
    width: 100%;
    padding: 12px;
    margin-top: 5px;
    border-radius: 8px;
    border: 1px solid #ccc;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
    font-size: 14px;
    box-sizing: border-box;
  }
  .dienst-block {
    border: 1px solid #ccc;
    padding: 15px;
    border-radius: 12px;
    margin-top: 15px;
    background-color: #f9f9f9;
    position: relative;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  }
  .remove-btn {
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
  }
  button {
    padding: 15px;
    border: none;
    border-radius: 30px;
    background-color: #007bff;
    color: white;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.3s;
  }
  button:hover {
    background-color: #0056b3;
  }
  .button-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 15px;
  }
  canvas {
    border: 2px solid #ccc;
    border-radius: 8px;
    margin-top: 10px;
    width: 100%;
    height: 200px;
  }
  .form-grid {
    display: block;
  }
  @media (min-width: 768px) {
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
  }
  .language-select {
    margin-bottom: 20px;
    font-size: 14px;
    text-align: left;
  }
</style>
</head>
<body>
  <div class="container">
    <form id="languageForm" class="language-select" method="GET" action="/">
      <label for="langSelect">{{ t.language }}:</label>
      <select id="langSelect" name="lang" onchange="document.getElementById('languageForm').submit()">
        {% for code, _ in translations.items() %}
        <option value="{{ code }}" {% if lang == code %}selected{% endif %}>{{ code.upper() }}</option>
        {% endfor %}
        <option value="nl" {% if lang == 'nl' %}selected{% endif %}>Nederlands</option>
        <option value="de" {% if lang == 'de' %}selected{% endif %}>Deutsch</option>
        <option value="fr" {% if lang == 'fr' %}selected{% endif %}>Français</option>
        <option value="es" {% if lang == 'es' %}selected{% endif %}>Español</option>
        <option value="pt" {% if lang == 'pt' %}selected{% endif %}>Português</option>
        <option value="sv" {% if lang == 'sv' %}selected{% endif %}>Svenska</option>
        <option value="tr" {% if lang == 'tr' %}selected{% endif %}>Türkçe</option>
        <option value="it" {% if lang == 'it' %}selected{% endif %}>Italiano</option>
        <option value="ar" {% if lang == 'ar' %}selected{% endif %}>العربية</option>
        <option value="en" {% if lang == 'en' %}selected{% endif %}>English</option>
      </select>
    </form>

    <h1>{{ t.title }}</h1>
    <form method="POST" action="/generate?lang={{ lang }}" enctype="multipart/form-data" id="invoiceForm">
      <label>{{ t.invoice_number }}:</label>
      <input name="factuurnummer" placeholder="Bijv. FACT-2025-001" required />

      <div class="form-grid">
        <div class="block bedrijf">
          <h2>{{ t.company_info }}</h2>
          <label>{{ t.company_name }}:</label>
          <input name="bedrijfsnaam" required />
          <label>{{ t.street }}:</label>
          <input name="straat" required />
          <label>{{ t.postcode }}:</label>
          <input name="postcode" required />
          <label>{{ t.city }}:</label>
          <input name="plaats" required />
          <label>{{ t.country }}:</label>
          <input name="land" required />
          <label>{{ t.kvk }}:</label>
          <input name="kvk" required />
          <label>{{ t.vat }}:</label>
          <input name="btw" required />
          <label>{{ t.iban }}:</label>
          <input name="iban" required />
          <label>{{ t.upload_logo }}:</label>
          <input type="file" name="logo" />

          <div class="button-group">
            <button type="button" onclick="saveCompanyInfo()">{{ t.save_company }}</button>
            <button type="button" onclick="clearCompanyInfo()">{{ t.clear_company }}</button>
          </div>
        </div>

        <div class="block klant">
          <h2>{{ t.client_info }}</h2>
          <label>{{ t.client_name }}:</label>
          <input name="klantnaam" required />
          <label>{{ t.street }}:</label>
          <input name="klant_straat" required />
          <label>{{ t.postcode }}:</label>
          <input name="klant_postcode" required />
          <label>{{ t.city }}:</label>
          <input name="klant_plaats" required />
          <label>{{ t.country }}:</label>
          <input name="klant_land" required />
        </div>
      </div>

      <div id="diensten"></div>
      <button type="button" onclick="voegDienstToe()">{{ t.add_service }}</button>

      <h2>{{ t.signature_label }}</h2>
      <canvas id="signature-pad"></canvas>
      <button type="button" onclick="clearSignature()">{{ t.clear_signature }}</button>
      <input type="hidden" id="handtekening" name="handtekening" />

      <button type="submit">{{ t.download_invoice }}</button>
    </form>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>
  <script>
    let dienstIndex = 0;
    function voegDienstToe() {
      const container = document.getElementById('diensten');
      const div = document.createElement('div');
      div.className = 'dienst-block';
      div.innerHTML = `
        <button type='button' class='remove-btn' onclick='this.parentNode.remove()'>×</button>
        <label>{{ t.service }}:</label>
        <input name='dienst_${dienstIndex}' required />
        <label>{{ t.quantity }}:</label>
        <input name='aantal_${dienstIndex}' type='number' required />
        <label>{{ t.price_per_unit }}:</label>
        <input name='prijs_${dienstIndex}' type='number' step='0.01' required />
        <label>{{ t.vat_percent }}:</label>
        <select name='btw_${dienstIndex}'>
          <option value='0'>0%</option>
          <option value='9'>9%</option>
          <option value='21' selected>21%</option>
        </select>
      `;
      container.appendChild(div);
      dienstIndex++;
    }

    var canvas = document.getElementById('signature-pad');
    var signaturePad;

    function resizeCanvas() {
      if (!signaturePad) return;
      const data = signaturePad.toData();
      const ratio = Math.max(window.devicePixelRatio || 1, 1);
      canvas.width = canvas.offsetWidth * ratio;
      canvas.height = canvas.offsetHeight * ratio;
      canvas.getContext('2d').scale(ratio, ratio);
      signaturePad.clear();
      signaturePad.fromData(data);
    }

    window.addEventListener('resize', resizeCanvas);

    window.onload = function () {
      signaturePad = new SignaturePad(canvas);
      resizeCanvas();
      loadCompanyInfo();
    };

    function saveSignature() {
      if (!signaturePad.isEmpty()) {
        var dataURL = signaturePad.toDataURL();
        document.getElementById('handtekening').value = dataURL;
      }
    }

    function clearSignature() {
      signaturePad.clear();
    }

    function saveCompanyInfo() {
      const fields = ['bedrijfsnaam', 'straat', 'postcode', 'plaats', 'land', 'kvk', 'btw', 'iban'];
      fields.forEach((field) => {
        const value = document.querySelector(`[name="${field}"]`).value;
        localStorage.setItem(field, value);
      });
      alert('{{ t.save_company }}!');
    }

    function loadCompanyInfo() {
      const fields = ['bedrijfsnaam', 'straat', 'postcode', 'plaats', 'land', 'kvk', 'btw', 'iban'];
      fields.forEach((field) => {
        const saved = localStorage.getItem(field);
        if (saved) {
          document.querySelector(`[name="${field}"]`).value = saved;
        }
      });
    }

    function clearCompanyInfo() {
      const fields = ['bedrijfsnaam', 'straat', 'postcode', 'plaats', 'land', 'kvk', 'btw', 'iban'];
      fields.forEach((field) => {
        localStorage.removeItem(field);
        document.querySelector(`[name="${field}"]`).value = '';
      });
      alert('{{ t.clear_company }}!');
    }

    document.getElementById('invoiceForm').addEventListener('submit', function (e) {
      saveSignature();
    });
  </script>
</body>
</html>
'''

PDF_HTML = '''
<!DOCTYPE html>
<html lang="{{ lang }}" dir="{{ 'rtl' if lang == 'ar' else 'ltr' }}">
<head>
<meta charset="UTF-8" />
<style>
  @page { size: A4; margin: 30px; }
  body {
    font-family: "Noto Sans", "Arial Unicode MS", Arial, sans-serif;
    font-size: 12pt;
    direction: {{ 'rtl' if lang == 'ar' else 'ltr' }};
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
  }
  .header {
    border-bottom: 2px solid #007bff;
    padding-bottom: 10px;
    margin-bottom: 20px;
    overflow: auto;
  }
  .logo {
    max-width: 150px;
    float: left;
  }
  .company-details {
    float: right;
    text-align: right;
  }
  .invoice-title {
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 20px;
    clear: both;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
  }
  th {
    background-color: #e6f2ff;
    text-align: center;
  }
  .totals td {
    border: none;
  }
  .signature {
    margin-top: 50px;
  }
  .signature img {
    max-width: 200px;
    height: auto;
  }
</style>
</head>
<body>
  <div class="header">
    {% if logo_data %}
      <img src="data:image/png;base64,{{ logo_data }}" class="logo" />
    {% endif %}
    <div class="company-details">
      <div><strong>{{ bedrijfsnaam }}</strong></div>
      <div>{{ straat }}</div>
      <div>{{ postcode }} {{ plaats }}</div>
      <div>{{ land }}</div>
      <div>KvK: {{ kvk }} | BTW: {{ btw }}</div>
      <div>IBAN: {{ iban }}</div>
    </div>
  </div>

  <div class="invoice-title">{{ t.invoice_number }}: {{ factuurnummer }}</div>
  <div>{{ t.date }}: {{ now }}</div>

  <h3>{{ t.invoice_to }}</h3>
  <div>{{ klantnaam }}</div>
  <div>{{ klant_straat }}</div>
  <div>{{ klant_postcode }} {{ klant_plaats }}</div>
  <div>{{ klant_land }}</div>

  <table>
    <thead>
      <tr>
        <th>{{ t.description }}</th>
        <th>{{ t.quantity }}</th>
        <th>{{ t.price }}</th>
        <th>{{ t.vat_percent }}</th>
        <th>{{ t.amount }}</th>
      </tr>
    </thead>
    <tbody>
      {% set subtotal = 0 %}
      {% set total_vat = 0 %}
      {% for dienst, aantal, prijs, btw_pct in diensten %}
        {% set excl = aantal * prijs %}
        {% set vat_amount = excl * btw_pct / 100 %}
        {% set incl = excl + vat_amount %}
        <tr>
          <td>{{ dienst }}</td>
          <td style="text-align:center;">{{ aantal }}</td>
          <td style="text-align:right;">{{ "%.2f"|format(prijs) }}</td>
          <td style="text-align:center;">{{ btw_pct }}%</td>
          <td style="text-align:right;">{{ "%.2f"|format(incl) }}</td>
        </tr>
        {% set subtotal = subtotal + excl %}
        {% set total_vat = total_vat + vat_amount %}
      {% endfor %}
    </tbody>
  </table>

  <table class="totals" style="width: 300px; float: right;">
    <tr><td><strong>{{ t.subtotal }}</strong></td><td style="text-align:right;">{{ "%.2f"|format(subtotal) }} EUR</td></tr>
    <tr><td><strong>{{ t.total_vat }}</strong></td><td style="text-align:right;">{{ "%.2f"|format(total_vat) }} EUR</td></tr>
    <tr><td><strong>{{ t.total }}</strong></td><td style="text-align:right;">{{ "%.2f"|format(subtotal + total_vat) }} EUR</td></tr>
  </table>

  <div style="clear: both;"></div>

  <div class="greeting" style="margin-top: 50px;">
    {{ t.greeting }}<br />
    {{ bedrijfsnaam }}
  </div>

  {% if handtekening_data %}
  <div class="signature">
    <div><strong>{{ t.signature }}</strong></div>
    <img src="{{ handtekening_data }}" alt="Signature" />
  </div>
  {% endif %}
</body>
</html>
'''

PDF_CSS = '''
@page { size: A4; margin: 30px; }
body {
  font-family: "Noto Sans", "Arial Unicode MS", Arial, sans-serif;
  font-size: 12pt;
}
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
