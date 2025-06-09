# -*- coding: utf-8 -*-
import os
import io
import base64
import uuid
from datetime import datetime
from flask import Flask, request, render_template_string, send_file, redirect, url_for, abort
from weasyprint import HTML, CSS

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
    'ar': {
        'title': 'فاتورة سريعة',
        'invoice_number': 'رقم الفاتورة',
        'date': 'التاريخ',
        'invoice_to': 'الفاتورة إلى:',
        'description': 'الوصف',
        'quantity': 'الكمية',
        'price': 'السعر',
        'vat_percent': 'ضريبة القيمة المضافة%',
        'amount': 'المبلغ',
        'subtotal': 'المجموع الفرعي (بدون ضريبة):',
        'total_vat': 'إجمالي ضريبة القيمة المضافة:',
        'total': 'الإجمالي (شامل الضريبة):',
        'greeting': 'مع أطيب التحيات،',
        'signature': 'التوقيع:',
        'company_info': 'بيانات الشركة',
        'client_info': 'بيانات العميل',
        'service': 'الخدمة',
        'price_per_unit': 'السعر للوحدة',
        'add_service': 'إضافة خدمة',
        'signature_label': 'التوقيع',
        'clear_signature': 'مسح التوقيع',
        'download_invoice': 'فتح الفاتورة',
        'save_company': 'حفظ بيانات الشركة',
        'clear_company': 'مسح بيانات الشركة',
        'upload_logo': 'تحميل شعارك (اختياري)',
        'street': 'الشارع ورقم المنزل',
        'postcode': 'الرمز البريدي',
        'city': 'المدينة',
        'country': 'الدولة',
        'kvk': 'رقم السجل التجاري',
        'vat': 'رقم الضريبة',
        'iban': 'رقم الحساب البنكي الدولي',
        'client_name': 'اسم العميل',
        'language': 'اللغة',
        'company_name': 'اسم الشركة',
    },
    # Je kunt hier de andere talen toevoegen zoals voorheen...
}

def get_translation():
    lang = request.args.get('lang', 'nl').lower()
    if lang not in translations:
        lang = 'nl'
    return translations[lang], lang

@app.route('/', methods=['GET'])
def index():
    t, lang = get_translation()
    return render_template_string(INDEX_HTML, t=t, lang=lang, translations=translations)

@app.route('/generate', methods=['POST'])
def generate_pdf():
    try:
        t, lang = get_translation()

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
        abort(400, description=f"Fout bij verwerken van factuur: {e}")

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

INDEX_HTML = '''
<!doctype html>
<html lang="{{ lang }}" dir="{{ 'rtl' if lang == 'ar' else 'ltr' }}">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{ t.title }}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins&display=swap&subset=arabic" rel="stylesheet" />
<style>
  /* Aurora style background */
  body {
    margin: 0; padding: 20px;
    min-height: 100vh;
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    background-size: 600% 600%;
    animation: aurora 20s ease infinite;
    display: flex; align-items: center; justify-content: center;
    direction: {{ 'rtl' if lang == 'ar' else 'ltr' }};
    color: #e0f7fa;
  }
  @keyframes aurora {
    0%{background-position:0% 50%}
    50%{background-position:100% 50%}
    100%{background-position:0% 50%}
  }

  .container {
    background: rgba(255,255,255,0.95);
    border-radius: 15px;
    padding: 30px;
    max-width: 900px;
    width: 100%;
    box-shadow: 0 0 20px rgba(0, 128, 128, 0.6);
    color: #004d40;
  }

  h1 {
    text-align: center;
    color: #00695c;
    margin-bottom: 30px;
    font-weight: 700;
    text-shadow: 0 0 5px #004d40;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 20px;
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

  .block {
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    background: #e0f2f1;
    box-shadow: 0 2px 8px rgba(0, 77, 64, 0.1);
  }
  .bedrijf {
    background: #b2dfdb;
  }
  .klant {
    background: #80cbc4;
  }

  label {
    display: block;
    margin-top: 10px;
    font-weight: 600;
    font-size: 15px;
    color: #004d40;
  }

  input, select {
    width: 100%;
    padding: 12px 15px;
    margin-top: 5px;
    border-radius: 10px;
    border: 1.5px solid #004d40;
    font-size: 15px;
    box-sizing: border-box;
    transition: all 0.3s ease;
  }
  input:focus, select:focus {
    outline: none;
    border-color: #00796b;
    box-shadow: 0 0 10px #004d40a0;
    background-color: #e0f2f1;
  }

  .dienst-block {
    border: 1px solid #004d40;
    padding: 15px;
    border-radius: 12px;
    margin-top: 15px;
    background: #b2dfdb;
    position: relative;
    box-shadow: 0 2px 6px rgba(0,77,64,0.2);
  }

  .remove-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    background-color: #d32f2f;
    color: white;
    border: none;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    cursor: pointer;
    font-size: 18px;
    line-height: 28px;
    text-align: center;
    font-weight: bold;
    transition: background-color 0.3s ease;
  }
  .remove-btn:hover {
    background-color: #9a0007;
  }

  button {
    background: linear-gradient(135deg, #00796b, #004d40);
    border: none;
    border-radius: 30px;
    color: #e0f2f1;
    cursor: pointer;
    font-size: 16px;
    font-weight: 700;
    padding: 15px;
    transition: background 0.3s ease;
  }
  button:hover {
    background: linear-gradient(135deg, #004d40, #00796b);
  }

  .button-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 15px;
  }

  canvas {
    border: 2px solid #004d40;
    border-radius: 10px;
    margin-top: 10px;
    width: 100%;
    height: 200px;
    background: #e0f2f1;
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
        {% for key, val in translations.items() %}
          <option value="{{ key }}" {% if lang == key %}selected{% endif %}>{{ val.language if val.language else val.title }}</option>
        {% endfor %}
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
        <input name='aantal_${dienstIndex}' type='number' min='1' required />
        <label>{{ t.price_per_unit }}:</label>
        <input name='prijs_${dienstIndex}' type='number' step='0.01' min='0' required />
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
    border-bottom: 2px solid #00796b;
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
    color: #004d40;
  }
  .invoice-title {
    font-size: 18pt;
    font-weight: bold;
    margin-bottom: 20px;
    clear: both;
    color: #00796b;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    color: #004d40;
  }
  th, td {
    border: 1px solid #004d40;
    padding: 8px;
  }
  th {
    background-color: #b2dfdb;
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

  <div class="greeting" style="margin-top: 50px; color: #004d40;">
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

@app.context_processor
def inject_now():
    return {'now': datetime.today().strftime('%d-%m-%Y')}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
