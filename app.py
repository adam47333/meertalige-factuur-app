# -*- coding: utf-8 -*-
import os
import io
import base64
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, send_file, redirect, url_for, abort
from weasyprint import HTML, CSS

app = Flask(__name__)
pdf_storage = {}

@app.template_filter('decimalcomma')
def decimal_comma_filter(value):
    return str(value).replace('.', ',')

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
        'language_name': 'Nederlands',
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
        'language_name': 'English',
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
        'language_name': 'العربية',
    }
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

        subtotal = 0.0
        total_vat = 0.0
        for dienst, aantal, prijs, btw_pct in diensten:
            excl = aantal * prijs
            vat_amount = excl * btw_pct / 100
            subtotal += excl
            total_vat += vat_amount
        total = subtotal + total_vat

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
                                              subtotal=subtotal,
                                              total_vat=total_vat,
                                              total=total,
                                              logo_data=logo_data,
                                              handtekening_data=handtekening_data,
                                              lang=lang,
                                              enumerate=enumerate)

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
                     as_attachment=True,
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
  body {
    background:
      radial-gradient(circle at 25% 40%, rgba(255, 179, 71, 0.4), transparent 60%),
      radial-gradient(circle at 70% 70%, rgba(100, 149, 237, 0.4), transparent 55%);
    background-repeat: no-repeat;
    background-size: cover;
    background-attachment: fixed;
    font-family: 'Poppins', sans-serif;
    color: #264653;
    margin: 0; padding: 20px;
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    direction: {{ 'rtl' if lang == 'ar' else 'ltr' }};
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
  }

  .container {
    width: 100%; max-width: 900px;
    background: rgba(255, 255, 255, 0.9);
    padding: 40px 50px;
    border-radius: 25px;
    box-shadow:
      0 10px 25px rgba(0, 0, 0, 0.12);
    border: 1px solid rgba(38, 70, 83, 0.2);
  }

  h1 {
    text-align: center;
    color: #264653;
    margin-bottom: 40px;
    font-weight: 700;
    letter-spacing: 2px;
    font-size: 2.8rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .block {
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    background-color: #f4f9f9;
    border: 1px solid #a2d2ff;
  }
  .bedrijf {
    background-color: #f4f9f9;
  }
  .klant {
    background-color: #f4f9f9;
  }

  label {
    display: block;
    margin-top: 10px;
    font-weight: 600;
    font-size: 14px;
    color: #264653;
  }

  input, select {
    width: 100%;
    padding: 14px 18px;
    margin-top: 6px;
    border-radius: 10px;
    border: 1.5px solid #a2d2ff;
    background: #e8f0f8;
    color: #264653;
    font-size: 16px;
    box-sizing: border-box;
    transition: all 0.3s ease;
    box-shadow: inset 0 0 8px rgba(162, 210, 255, 0.5);
  }

  input::placeholder {
    color: #a2d2ff;
    opacity: 0.8;
  }

  input:focus, select:focus {
    outline: none;
    border-color: #ffb347;
    box-shadow: 0 0 10px #ffb347;
    background: #fff7e6;
    color: #264653;
    filter: none !important;
    text-indent: 0 !important;
  }

  /* Blur alleen op klant inputs/selects */
  .klant input.blurred, .klant select.blurred {
    filter: blur(3px);
    opacity: 0.7;
    color: #264653;
    user-select: none;
    cursor: default;
  }

  .dienst-block {
    border: 1px solid #a2d2ff;
    padding: 15px;
    border-radius: 12px;
    margin-top: 15px;
    background-color: #f4f9f9;
    position: relative;
    box-shadow: none;
  }

  .remove-btn {
    position: absolute;
    top: 10px;
    {% if lang == 'ar' %}
      left: 10px;
    {% else %}
      right: 10px;
    {% endif %}
    background-color: #ffb347;
    color: white;
    border: none;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    cursor: pointer;
    font-size: 20px;
    line-height: 30px;
    text-align: center;
    padding: 0;
    user-select: none;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  button {
    padding: 15px;
    border: none;
    border-radius: 25px;
    background-color: #264653;
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s;
  }

  button:hover {
    background-color: #1b2c32;
  }

  .button-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 15px;
  }

  canvas {
    border: 2px solid #264653;
    border-radius: 8px;
    margin-top: 10px;
    width: 100%;
    height: 200px;
    background-color: #e8f0f8;
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
        {% for key, val in translations.items() %}
          <option value="{{key}}" {% if lang == key %}selected{% endif %}>{{ val.language_name }}</option>
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
      <button type='button' class='remove-btn' onclick='this.parentNode.remove()' aria-label="Remove service">×</button>
      <label>{{ t.service }}:</label>
      <input name='dienst_${dienstIndex}' required />
      <label>{{ t.quantity }}:</label>
      <input name='aantal_${dienstIndex}' type='number' min="1" value="1" required />
      <label>{{ t.price_per_unit }}:</label>
      <input name='prijs_${dienstIndex}' type='number' step='0.01' min="0" value="0.00" required />
      <label>{{ t.vat_percent }}:</label>
      <select name='btw_${dienstIndex}'>
        <option value='0'>0%</option>
        <option value='9'>9%</option>
        <option value='21' selected>21%</option>
      </select>
    `;
    container.appendChild(div);
    dienstIndex++;
    applyBlurEffectToInputs(div);
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
    applyBlurEffectToInputs(document);
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

  function applyBlurEffectToInputs(root) {
    const klantInputs = root.querySelectorAll('.klant input, .klant select');
    klantInputs.forEach(input => {
      if (!input._blurListenersAdded) {
        input.addEventListener('blur', () => {
          if(input.value.trim() !== '') {
            input.classList.add('blurred');
          }
        });
        input.addEventListener('focus', () => {
          input.classList.remove('blurred');
        });
        if(input.value.trim() !== '') {
          input.classList.add('blurred');
        }
        input._blurListenersAdded = true;
      }
    });
  }
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
    font-family: "Arial", sans-serif;
    font-size: 12pt;
    direction: {{ 'rtl' if lang == 'ar' else 'ltr' }};
    color: #000;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    flex-direction: {{ 'row-reverse' if lang == 'ar' else 'row' }};
  }
  .logo {
    max-width: 180px;
  }
  .company-details {
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
    font-size: 10pt;
    line-height: 1.4;
  }
  .client-details {
    margin-bottom: 30px;
    font-size: 11pt;
    line-height: 1.4;
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
  }
  .invoice-info {
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
    font-size: 10pt;
    margin-bottom: 30px;
  }
  h1 {
    font-size: 20pt;
    margin-bottom: 15px;
    text-align: center;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11pt;
    margin-bottom: 20px;
    direction: {{ 'rtl' if lang == 'ar' else 'ltr' }};
  }
  th, td {
    border-bottom: 1px solid #ccc;
    padding: 8px 10px;
  }
  th {
    font-weight: bold;
    border-bottom: 2px solid #000;
  }
  th.left, td.left {
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
  }
  th.right, td.right {
    text-align: {{ 'left' if lang == 'ar' else 'right' }};
  }
  tfoot td {
    border: none;
    padding-top: 10px;
    font-weight: bold;
  }
  .totals-table {
    width: 300px;
    margin-left: {{ '0' if lang == 'ar' else 'auto' }};
    margin-right: {{ 'auto' if lang == 'ar' else '0' }};
    border-collapse: collapse;
    font-size: 11pt;
  }
  .totals-table td {
    padding: 6px 10px;
  }
  .totals-table tr.total-row td {
    border-top: 2px solid #000;
    font-weight: bold;
  }
</style>
</head>
<body>
  <div class="header">
    {% if logo_data %}
      <img src="data:image/png;base64,{{ logo_data }}" class="logo" />
    {% else %}
      <div><strong>{{ bedrijfsnaam }}</strong></div>
    {% endif %}
    <div class="company-details">
      <div>{{ bedrijfsnaam }}</div>
      <div>{{ straat }}</div>
      <div>{{ postcode }} {{ plaats }}</div>
      <div>{{ land }}</div>
      <div>KvK: {{ kvk }}</div>
      <div>BTW: {{ btw }}</div>
      <div>IBAN: {{ iban }}</div>
    </div>
  </div>

  <div class="client-details">
    <strong>{{ klantnaam }}</strong><br />
    {{ klant_straat }}<br />
    {{ klant_postcode }} {{ klant_plaats }}<br />
    {{ klant_land }}
  </div>

  <div class="invoice-info">
    <div><strong>{{ t.invoice_number }}:</strong> {{ factuurnummer }}</div>
    <div><strong>{{ t.date }}:</strong> {{ now }}</div>
    <div><strong>Vervaldatum:</strong> {{ (datetime.strptime(now, '%d-%m-%Y') + timedelta(days=30)).strftime('%d-%m-%Y') }}</div>
  </div>

  <h1>FACTUUR</h1>

  <table>
    <thead>
      <tr>
        <th class="left" style="width:5%;">#</th>
        <th class="left" style="width:45%;">{{ t.description }}</th>
        <th class="right" style="width:15%;">{{ t.price }}</th>
        <th class="right" style="width:15%;">{{ t.quantity }}</th>
        <th class="right" style="width:20%;">{{ t.amount }}</th>
        <th class="right" style="width:10%;">{{ t.vat_percent }}</th>
      </tr>
    </thead>
    <tbody>
      {% for i, (dienst, aantal, prijs, btw_pct) in enumerate(diensten, start=1) %}
        {% set excl = aantal * prijs %}
        {% set vat_amount = excl * btw_pct / 100 %}
        {% set incl = excl + vat_amount %}
        <tr>
          <td class="left">{{ i }}</td>
          <td class="left">{{ dienst }}</td>
          <td class="right">€ {{ '%.2f'|format(prijs)|replace('.', ',') }}</td>
          <td class="right">{{ aantal }}</td>
          <td class="right">€ {{ '%.2f'|format(incl)|replace('.', ',') }}</td>
          <td class="right">{{ btw_pct }}%</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>

  <table class="totals-table">
    <tr>
      <td>{{ t.subtotal }}</td>
      <td class="right">€ {{ '%.2f'|format(subtotal)|replace('.', ',') }}</td>
    </tr>
    <tr>
      <td>{{ t.total_vat }}</td>
      <td class="right">€ {{ '%.2f'|format(total_vat)|replace('.', ',') }}</td>
    </tr>
    <tr class="total-row">
      <td>{{ t.total }}</td>
      <td class="right">€ {{ '%.2f'|format(total)|replace('.', ',') }}</td>
    </tr>
  </table>

</body>
</html>
'''

PDF_CSS = '''
@page { size: A4; margin: 30px; }
body {
  font-family: "Arial", sans-serif;
  font-size: 12pt;
}
'''

@app.context_processor
def inject_now():
    return {
        'now': datetime.today().strftime('%d-%m-%Y'),
        'datetime': datetime,
        'timedelta': timedelta,
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
