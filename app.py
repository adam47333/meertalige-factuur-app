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
    'de': {
        'title': 'Schnellrechnung',
        'invoice_number': 'Rechnungsnummer',
        'date': 'Datum',
        'invoice_to': 'Rechnung an:',
        'description': 'Beschreibung',
        'quantity': 'Menge',
        'price': 'Preis',
        'vat_percent': 'MwSt%',
        'amount': 'Betrag',
        'subtotal': 'Zwischensumme (exkl. MwSt):',
        'total_vat': 'Gesamt MwSt:',
        'total': 'Gesamt (inkl. MwSt):',
        'greeting': 'Mit freundlichen Grüßen,',
        'signature': 'Unterschrift:',
        'company_info': 'Firmendaten',
        'client_info': 'Kundendaten',
        'service': 'Dienstleistung',
        'price_per_unit': 'Preis pro Einheit',
        'add_service': 'Dienst hinzufügen',
        'signature_label': 'Unterschrift',
        'clear_signature': 'Unterschrift löschen',
        'download_invoice': 'Rechnung öffnen',
        'save_company': 'Firmendaten speichern',
        'clear_company': 'Firmendaten löschen',
        'upload_logo': 'Logo hochladen (optional)',
        'street': 'Straße und Hausnummer',
        'postcode': 'Postleitzahl',
        'city': 'Stadt',
        'country': 'Land',
        'kvk': 'Handelsregisternummer',
        'vat': 'USt-IdNr.',
        'iban': 'IBAN',
        'client_name': 'Kundenname',
        'language': 'Sprache',
        'company_name': 'Firmenname',
    },
    'fr': {
        'title': 'Facture rapide',
        'invoice_number': 'Numéro de facture',
        'date': 'Date',
        'invoice_to': 'Facture à :',
        'description': 'Description',
        'quantity': 'Quantité',
        'price': 'Prix',
        'vat_percent': 'TVA%',
        'amount': 'Montant',
        'subtotal': 'Sous-total (HT):',
        'total_vat': 'Total TVA:',
        'total': 'Total (TTC):',
        'greeting': 'Cordialement,',
        'signature': 'Signature :',
        'company_info': 'Informations sur l\'entreprise',
        'client_info': 'Informations sur le client',
        'service': 'Service',
        'price_per_unit': 'Prix unitaire',
        'add_service': 'Ajouter un service',
        'signature_label': 'Signature',
        'clear_signature': 'Effacer la signature',
        'download_invoice': 'Ouvrir la facture',
        'save_company': 'Enregistrer les informations de l\'entreprise',
        'clear_company': 'Effacer les informations de l\'entreprise',
        'upload_logo': 'Télécharger votre logo (optionnel)',
        'street': 'Rue et numéro',
        'postcode': 'Code postal',
        'city': 'Ville',
        'country': 'Pays',
        'kvk': 'Numéro de registre du commerce',
        'vat': 'Numéro de TVA',
        'iban': 'IBAN',
        'client_name': 'Nom du client',
        'language': 'Langue',
        'company_name': 'Nom de l\'entreprise',
    },
    'es': {
        'title': 'Factura rápida',
        'invoice_number': 'Número de factura',
        'date': 'Fecha',
        'invoice_to': 'Factura para:',
        'description': 'Descripción',
        'quantity': 'Cantidad',
        'price': 'Precio',
        'vat_percent': 'IVA%',
        'amount': 'Importe',
        'subtotal': 'Subtotal (sin IVA):',
        'total_vat': 'Total IVA:',
        'total': 'Total (con IVA):',
        'greeting': 'Saludos cordiales,',
        'signature': 'Firma:',
        'company_info': 'Datos de la empresa',
        'client_info': 'Datos del cliente',
        'service': 'Servicio',
        'price_per_unit': 'Precio por unidad',
        'add_service': 'Agregar servicio',
        'signature_label': 'Firma',
        'clear_signature': 'Borrar firma',
        'download_invoice': 'Abrir factura',
        'save_company': 'Guardar datos de la empresa',
        'clear_company': 'Borrar datos de la empresa',
        'upload_logo': 'Subir logo (opcional)',
        'street': 'Calle y número',
        'postcode': 'Código postal',
        'city': 'Ciudad',
        'country': 'País',
        'kvk': 'Número de registro mercantil',
        'vat': 'Número de IVA',
        'iban': 'IBAN',
        'client_name': 'Nombre del cliente',
        'language': 'Idioma',
        'company_name': 'Nombre de la empresa',
    },
    'pt': {
        'title': 'Fatura rápida',
        'invoice_number': 'Número da fatura',
        'date': 'Data',
        'invoice_to': 'Fatura para:',
        'description': 'Descrição',
        'quantity': 'Quantidade',
        'price': 'Preço',
        'vat_percent': 'IVA%',
        'amount': 'Valor',
        'subtotal': 'Subtotal (sem IVA):',
        'total_vat': 'Total IVA:',
        'total': 'Total (com IVA):',
        'greeting': 'Atenciosamente,',
        'signature': 'Assinatura:',
        'company_info': 'Informações da empresa',
        'client_info': 'Informações do cliente',
        'service': 'Serviço',
        'price_per_unit': 'Preço por unidade',
        'add_service': 'Adicionar serviço',
        'signature_label': 'Assinatura',
        'clear_signature': 'Limpar assinatura',
        'download_invoice': 'Abrir fatura',
        'save_company': 'Salvar informações da empresa',
        'clear_company': 'Limpar informações da empresa',
        'upload_logo': 'Carregar logo (opcional)',
        'street': 'Rua e número',
        'postcode': 'Código postal',
        'city': 'Cidade',
        'country': 'País',
        'kvk': 'Número de registro comercial',
        'vat': 'Número de IVA',
        'iban': 'IBAN',
        'client_name': 'Nome do cliente',
        'language': 'Idioma',
        'company_name': 'Nome da empresa',
    },
    'sv': {
        'title': 'Snabbfaktura',
        'invoice_number': 'Fakturanummer',
        'date': 'Datum',
        'invoice_to': 'Faktura till:',
        'description': 'Beskrivning',
        'quantity': 'Antal',
        'price': 'Pris',
        'vat_percent': 'Moms%',
        'amount': 'Belopp',
        'subtotal': 'Delsumma (exkl. moms):',
        'total_vat': 'Total moms:',
        'total': 'Totalt (inkl. moms):',
        'greeting': 'Med vänliga hälsningar,',
        'signature': 'Signatur:',
        'company_info': 'Företagsuppgifter',
        'client_info': 'Kunduppgifter',
        'service': 'Tjänst',
        'price_per_unit': 'Pris per enhet',
        'add_service': 'Lägg till tjänst',
        'signature_label': 'Signatur',
        'clear_signature': 'Rensa signatur',
        'download_invoice': 'Öppna faktura',
        'save_company': 'Spara företagsuppgifter',
        'clear_company': 'Rensa företagsuppgifter',
        'upload_logo': 'Ladda upp din logotyp (valfritt)',
        'street': 'Gata och nummer',
        'postcode': 'Postnummer',
        'city': 'Stad',
        'country': 'Land',
        'kvk': 'Organisationsnummer',
        'vat': 'Momsnummer',
        'iban': 'IBAN',
        'client_name': 'Kundnamn',
        'language': 'Språk',
        'company_name': 'Företagsnamn',
    },
    'tr': {
        'title': 'Hızlı Fatura',
        'invoice_number': 'Fatura Numarası',
        'date': 'Tarih',
        'invoice_to': 'Fatura Alıcısı:',
        'description': 'Açıklama',
        'quantity': 'Miktar',
        'price': 'Fiyat',
        'vat_percent': 'KDV%',
        'amount': 'Tutar',
        'subtotal': 'Ara Toplam (KDV Hariç):',
        'total_vat': 'Toplam KDV:',
        'total': 'Toplam (KDV Dahil):',
        'greeting': 'Saygılarımla,',
        'signature': 'İmza:',
        'company_info': 'Şirket Bilgileri',
        'client_info': 'Müşteri Bilgileri',
        'service': 'Hizmet',
        'price_per_unit': 'Birim Fiyat',
        'add_service': 'Hizmet Ekle',
        'signature_label': 'İmza',
        'clear_signature': 'İmza Temizle',
        'download_invoice': 'Faturayı Aç',
        'save_company': 'Şirket Bilgilerini Kaydet',
        'clear_company': 'Şirket Bilgilerini Temizle',
        'upload_logo': 'Logonuzu Yükleyin (isteğe bağlı)',
        'street': 'Sokak ve Numara',
        'postcode': 'Posta Kodu',
        'city': 'Şehir',
        'country': 'Ülke',
        'kvk': 'Ticaret Sicil Numarası',
        'vat': 'KDV Numarası',
        'iban': 'IBAN',
        'client_name': 'Müşteri Adı',
        'language': 'Dil',
        'company_name': 'Şirket Adı',
    },
    'it': {
        'title': 'Fattura veloce',
        'invoice_number': 'Numero fattura',
        'date': 'Data',
        'invoice_to': 'Fattura a:',
        'description': 'Descrizione',
        'quantity': 'Quantità',
        'price': 'Prezzo',
        'vat_percent': 'IVA%',
        'amount': 'Importo',
        'subtotal': 'Totale parziale (escl. IVA):',
        'total_vat': 'Totale IVA:',
        'total': 'Totale (incl. IVA):',
        'greeting': 'Cordiali saluti,',
        'signature': 'Firma:',
        'company_info': 'Informazioni sull\'azienda',
        'client_info': 'Informazioni cliente',
        'service': 'Servizio',
        'price_per_unit': 'Prezzo per unità',
        'add_service': 'Aggiungi servizio',
        'signature_label': 'Firma',
        'clear_signature': 'Cancella firma',
        'download_invoice': 'Apri fattura',
        'save_company': 'Salva informazioni azienda',
        'clear_company': 'Cancella informazioni azienda',
        'upload_logo': 'Carica logo (opzionale)',
        'street': 'Via e numero',
        'postcode': 'CAP',
        'city': 'Città',
        'country': 'Paese',
        'kvk': 'Numero di registrazione',
        'vat': 'Partita IVA',
        'iban': 'IBAN',
        'client_name': 'Nome cliente',
        'language': 'Lingua',
        'company_name': 'Nome azienda',
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
    return render_template_string(INDEX_HTML, t=t, lang=lang)

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

        # Berekeningen voor totaal
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
    background: linear-gradient(135deg, #d0f0ea 0%, #e8f6f3 100%);
    font-family: 'Poppins', sans-serif;
    color: #2e4a45;
    margin: 0; padding: 20px;
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    direction: {{ 'rtl' if lang == 'ar' else 'ltr' }};
    text-align: {{ 'right' if lang == 'ar' else 'left' }};
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-size: cover;
  }

  .container {
    width: 100%; max-width: 900px;
    background: rgba(255, 255, 255, 0.85);
    padding: 40px 50px;
    border-radius: 25px;
    box-shadow:
      0 4px 30px rgba(0, 0, 0, 0.1),
      inset 0 0 40px rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(46, 74, 69, 0.3);
  }

  h1 {
    text-align: center;
    color: #3a7d7d;
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
    background-color: #dff4f2;
    border: 1px solid #a9d5d1;
    box-shadow: none;
  }
  .bedrijf {
    background-color: #dff4f2;
  }
  .klant {
    background-color: #dff4f2;
  }

  label {
    display: block;
    margin-top: 10px;
    font-weight: 600;
    font-size: 14px;
    color: #2e4a45;
  }

  input, select {
    width: 100%;
    padding: 14px 18px;
    margin-top: 6px;
    border-radius: 10px;
    border: 1.5px solid #a9d5d1;
    background: #f0fbfa;
    color: #2e4a45;
    font-size: 16px;
    box-sizing: border-box;
    transition: all 0.3s ease;
    box-shadow: inset 0 0 8px rgba(169, 213, 209, 0.6);
  }

  input::placeholder {
    color: #a9d5d1;
    opacity: 0.8;
  }

  input:focus, select:focus {
    outline: none;
    border-color: #3a7d7d;
    box-shadow: 0 0 8px #3a7d7d;
    background: #e0f7f6;
    color: #1e3d3c;
    filter: none !important;
    text-indent: 0 !important;
  }

  /* Blur alleen op klant inputs/selects */
  .klant input.blurred, .klant select.blurred {
    filter: blur(3px);
    opacity: 0.7;
    color: #2e4a45;
    text-indent: 0;
    user-select: none;
  }

  .dienst-block {
    border: 1px solid #a9d5d1;
    padding: 15px;
    border-radius: 12px;
    margin-top: 15px;
    background-color: #dff4f2;
    position: relative;
    box-shadow: none;
  }

  .remove-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    background-color: #3a7d7d;
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
    border-radius: 25px;
    background-color: #3a7d7d;
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s;
  }

  button:hover {
    background-color: #2a5e5e;
  }

  .button-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 15px;
  }

  canvas {
    border: 2px solid #3a7d7d;
    border-radius: 8px;
    margin-top: 10px;
    width: 100%;
    height: 200px;
    background-color: #e0f7f6;
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
      {% endfor %}
    </tbody>
  </table>

  <table class="totals" style="width: 300px; float: right;">
    <tr><td><strong>{{ t.subtotal }}</strong></td><td style="text-align:right;">{{ "%.2f"|format(subtotal) }} EUR</td></tr>
    <tr><td><strong>{{ t.total_vat }}</strong></td><td style="text-align:right;">{{ "%.2f"|format(total_vat) }} EUR</td></tr>
    <tr><td><strong>{{ t.total }}</strong></td><td style="text-align:right;">{{ "%.2f"|format(total) }} EUR</td></tr>
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

@app.context_processor
def inject_now():
    return {'now': datetime.today().strftime('%d-%m-%Y')}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
