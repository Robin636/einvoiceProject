# from datetime import datetime

# from timeit import template
# from tkinter import filedialog

import csv
import errno
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import timedelta
# from unittest.mock import right
from xml.etree.ElementTree import SubElement

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.urls import reverse_lazy
# import datetime
from django.utils import timezone
from django.views.generic import ListView, TemplateView, DetailView, UpdateView, DeleteView
from xhtml2pdf import pisa

from einvoice.forms import InvoiceForm, CustomerForm, ArticleForm, LanguageForm, AddressForm, TitleForm
from einvoice.models import Enterprise, Organisation, Customer, Invoice, Article, Editor, Bank, OrgFiles, Note, Text, \
  Unit, Address

# Create your views here.
class AboutView(TemplateView):
  template_name = 'einvoice/about.html'


def index(request, **kwargs):
  # show enterprise data always
  enterprise_list = Enterprise.objects.all()
  enterprise = enterprise_list[0]

  context = {
    'enterprise': enterprise,
  }
  user_id = request.user.id
  if user_id is not None:
    context = create_context_invoice(user_id=user_id, invoice_pk=0, customer_pk=0, article_pk=0)
    return render(request, 'einvoice/invoice_list.html', context)
  return render(request, 'base.html', context)



def invoice_send(request, pk):
  user_id = request.user.id
  editor = Editor.objects.get(author_id=user_id)
  organisation = Organisation.objects.get(id=editor.organisation_id)
  invoice = Invoice.objects.get(pk=pk)
  customer = Customer.objects.get(pk=invoice.customer_id)
  # context = create_context_invoice(user_id=request.user.id, invoice_pk=pk, customer_pk=customer.id, article_pk=0)

  pdfFileName = 'Re' + str(invoice.number) + '.pdf'
  path_pdf = os.path.join(settings.MEDIA_ROOT,
                      str('orgfiles/' + str(organisation.id) + '/Re' + str(invoice.number) + '.pdf'))
  if os.path.exists(path_pdf) == False:
    invoice_genPDF(request, pk)

  XMLFileName = 'ZUGFeRD-invoice.xml'
  path_xml = os.path.join(settings.MEDIA_ROOT,
                          str('orgfiles/' + str(organisation.id) + '/' + str(invoice.number) + '/' + 'ZUGFeRD-invoice.xml'))

  if invoice.date_genXML == None or invoice.date_genXML < invoice.date_genPDF:
    invoice_genXML(request, pk)
    # messages.info(request, "XML Datei wird erstellt.")

  subject = 'EIV-Datei(en) zur ' + str(invoice.type) + ' an ' + str(invoice.customer)

  # send_mail(
  #   "Subject",
  #   "Here is the message.",
  #   "send@rauner.de",
  #   ["monika@rauner.de"],
  # )

  from_email = settings.EMAIL_HOST_USER
  to = organisation.email

  if invoice.type == 'Rechnung' or invoice.type == 'Gutschrift':
    message_att = 'Anbei ' + pdfFileName + ' und ' + XMLFileName
    email = EmailMessage(subject, message_att, from_email, [to])
  else:
    message_att = 'Anbei ' + pdfFileName
    email = EmailMessage(subject, message_att, from_email, [to])

  # message_att = 'Hallo ' + customer.contact + ': Anbei ' + pdfFileName + ' und ' + XMLFileName
  # email = EmailMessage(subject, message_att, from_email, [to])
  # files = context['file_list']
  # path_pk = str(pk)

  try:
    # for file in files:
    #   path = os.path.join(settings.MEDIA_ROOT, str('orgfiles/' + path_pk + '/' + file.file_name))
    #   email.attach_file(path, mimetype=None)
    if invoice.type == 'Rechnung' or invoice.type == 'Gutschrift':
      email.attach_file(path_pdf, mimetype=None)
      email.attach_file(path_xml, mimetype=None)
    else:
      email.attach_file(path_pdf, mimetype=None)

    email.send()
    messages.success(request, "Datei(en) an " + str(to) + " wurden versandt")
    invoice.date_sentFiles = timezone.now()
    invoice.save()

  except:
    messages.error(request, "Datei(en) an " + str(to) +
                   " konnten nicht versandt werden!")

  context = create_context_invoice(user_id=request.user.id, invoice_pk=pk, customer_pk=customer.id, article_pk=0)
  return render(request, 'einvoice/invoice_list.html', context)


def invoice_genXML(request, pk):
  user_id = request.user.id
  invoice = Invoice.objects.get(pk=pk)
  note = Note.objects.get(language=invoice.language)
  editor = Editor.objects.get(author_id=user_id)
  organisation = Organisation.objects.get(id=editor.organisation_id)
  bank = Bank.objects.get(organisation_id=organisation.id)
  customer = Customer.objects.get(pk=invoice.customer_id)

  if invoice.type == 'Angebot' or invoice.type == 'Auftragsbestätigung':
    messages.info(request, "XML-Datei wird bei Angebot oder Auftragsbestätigung nicht erstellt.")
    context = create_context_invoice(user_id=user_id, invoice_pk=pk, customer_pk=customer.id, article_pk=0)
    return render(request, 'einvoice/invoice_list.html', context)

  # invoice.type BT-3
  DocumentCodeType = '380' # Handelsrechnung
  if invoice.type == 'Gutschrift': DocumentCodeType = '381'

  address_list = Address.objects.filter(customer_id=customer.id)
  bRA = False
  bLA = False
  if address_list.count() > 0:
    for address in address_list:
      if address.addr_type == 'Rechnungsadresse':
        bRA = True
      if address.addr_type == 'Lieferadresse':
        bLA = True

  if bRA == False:
      Address.objects.create(
        customer_id=customer.id,
        addr_type='Rechnungsadresse',
        title=customer.title,
        name=customer.name,
        address=customer.address,
        PLZ=customer.PLZ,
        city=customer.city,
        country=customer.country,
        country_ID=customer.country_ID,
        contact=customer.contact,
        phone=customer.phone,
        email=customer.email,
        credit_number=customer.credit_number,
      )
  if bLA == False:
      Address.objects.create(
        customer_id=customer.id,
        addr_type='Lieferadresse',
        title=customer.title,
        name=customer.name,
        address=customer.address,
        PLZ=customer.PLZ,
        city=customer.city,
        country=customer.country,
        country_ID=customer.country_ID,
        contact=customer.contact,
        phone=customer.phone,
        email=customer.email,
        credit_number=customer.credit_number,
      )
  invoice_address = Address.objects.get(customer_id=customer.id, addr_type='Rechnungsadresse')
  deliver_address = Address.objects.get(customer_id=customer.id, addr_type='Lieferadresse')
  context = create_context_invoice(user_id=user_id, invoice_pk=pk, customer_pk=customer.id, article_pk=0)

  Linersm = "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
  Lineqdt = "urn:un:unece:uncefact:data:standard:QualifiedDataType:100"
  Lineram = "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
  Linexs = "http://www.w3.org/2001/XMLSchema"
  Lineudt= "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100"

  LineDict = {
    'xmlns:rsm': Linersm,
    'xmlns:qdt': Lineqdt,
    'xmlns:ram': Lineram,
    'xmlns:xs': Linexs,
    'xmlns:udt': Lineudt
  }

  cii = ET.Element('rsm:CrossIndustryInvoice', attrib=LineDict)

  # BT-24
  edc = ET.SubElement(cii, 'rsm:ExchangedDocumentContext')
  gsdcp = ET.SubElement(edc, 'ram:GuidelineSpecifiedDocumentContextParameter')
  ET.SubElement(gsdcp, 'ram:ID').text = 'urn:cen.eu:en16931:2017'

  ed = ET.SubElement(cii, 'rsm:ExchangedDocument')

  ET.SubElement(ed, 'ram:ID').text = invoice.number
  ET.SubElement(ed, 'ram:Name').text = context['docTitle'] # 'RECHNUNG'
  ET.SubElement(ed, 'ram:TypeCode').text = DocumentCodeType # BT-3
  idt = ET.SubElement(ed, 'ram:IssueDateTime')
  date_gen = timezone.now()
  ET.SubElement(idt, 'udt:DateTimeString', format='102').text = date_gen.strftime('%Y%m%d') # BT-2

  in1 = ET.SubElement(ed, 'ram:IncludedNote')
  ET.SubElement(in1, 'ram:Content').text = 'Geschäftsführer: ' + organisation.manager
  ET.SubElement(in1, 'ram:SubjectCode').text = 'REG'

  in2 = ET.SubElement(ed, 'ram:IncludedNote')
  ET.SubElement(in2, 'ram:Content').text = note.eigentums_text
  ET.SubElement(in2, 'ram:SubjectCode').text = 'ABL'

  if invoice.language == 'DE':
    in3 = ET.SubElement(ed, 'ram:IncludedNote')
    ET.SubElement(in3, 'ram:Content').text = note.service_text + ' ' + str(invoice.service_sum) + ' EUR'
    ET.SubElement(in3, 'ram:SubjectCode').text = 'TXD'

  # in3 = ET.SubElement(ed, 'ram:IncludedNote')
  # ET.SubElement(in3, 'ram:Content').text = 'Handelsregister: ' + organisation.HRBno
  # ET.SubElement(in3, 'ram:SubjectCode').text = 'REG'
  #
  # in5 = ET.SubElement(ed, 'ram:IncludedNote')
  # ET.SubElement(in5, 'ram:Content').text = 'Amtsgericht: ' + organisation.court
  # ET.SubElement(in5, 'ram:SubjectCode').text = 'REG'
  #
  # in6 = ET.SubElement(ed, 'ram:IncludedNote')
  # ET.SubElement(in6, 'ram:Content').text = 'ZUGFeRD vers 2.4.0 (Extended)'
  # ET.SubElement(in6, 'ram:SubjectCode').text = 'ACB'

  # _________________________________Ende Kopfbereich

  sctt = ET.SubElement(cii, 'rsm:SupplyChainTradeTransaction')

  articles = Article.objects.filter(invoice_id=pk)
  positions = articles.exclude(category="2")
  position_list = sorted(positions, key=lambda item: item.pos)
  article_index = 1
  for article in position_list:
    isctli = ET.SubElement(sctt, 'ram:IncludedSupplyChainTradeLineItem')
    adld = ET.SubElement(isctli, 'ram:AssociatedDocumentLineDocument')
    ET.SubElement(adld, 'ram:LineID').text = str(article_index) # BT-126
    # ET.SubElement(adld, 'ram:LineID').text = str(article_index)  # BT-126

    stp = ET.SubElement(isctli, 'ram:SpecifiedTradeProduct')
    # ET.SubElement(stp, 'ram:GlobalID', schemeID='0160').text = str(organisation.id) + '00000' + str(article_index)
    # SAID = organisation.UStID[2:].replace(" ", "")
    ET.SubElement(stp, 'ram:SellerAssignedID').text = article.pos
    ET.SubElement(stp, 'ram:Name').text = article.description

    slta = ET.SubElement(isctli, 'ram:SpecifiedLineTradeAgreement') #BG-29

    # gpptp = ET.SubElement(slta, 'ram:GrossPriceProductTradePrice')
    # ET.SubElement(gpptp, 'ram:ChargeAmount').text = str(article.price)

    npptp = ET.SubElement(slta, 'ram:NetPriceProductTradePrice')
    ET.SubElement(npptp, 'ram:ChargeAmount').text = str(article.price)

    unitCode = 'H87'
    if article.unit == 'Std' or article.unit == 'h': unitCode = 'HUR'
    if article.unit == 'Stk' or article.unit == 'pcs' or article.unit == 'pce': unitCode = 'H87'
    if article.unit == 'Km' or article.unit == 'km': unitCode = 'HUR'
    ET.SubElement(npptp, 'ram:BasisQuantity', unitCode=unitCode).text = str(article.nofArticles)


    sltd = ET.SubElement(isctli, 'ram:SpecifiedLineTradeDelivery')
    ET.SubElement(sltd, 'ram:BilledQuantity', unitCode=unitCode).text = str(article.nofArticles)


    slts = ET.SubElement(isctli, 'ram:SpecifiedLineTradeSettlement')
    att = ET.SubElement(slts, 'ram:ApplicableTradeTax')
    ET.SubElement(att, 'ram:TypeCode').text = 'VAT'
    ET.SubElement(att, 'ram:CategoryCode').text = 'S'
    ET.SubElement(att, 'ram:RateApplicablePercent').text = str(article.tax_percentage)

    # stslms = ET.SubElement(slts, 'ram:SpecifiedTradeSettlementLineMonetarySummation')
    # ET.SubElement(stslms, 'ram:LineTotalAmount').text = str(article.price_pos)

    article_index = article_index + 1

  # _________________________________Ende Artikel

  ahta = ET.SubElement(sctt, 'ram:ApplicableHeaderTradeAgreement')

  # Verkäufer = organisation
  stp = ET.SubElement(ahta, 'ram:SellerTradeParty')
  ET.SubElement(stp, 'ram:ID').text = organisation.UStID
  ET.SubElement(stp, 'ram:GlobalID', schemeID='0088').text = customer.credit_number # vom Käufer erhaltene Nummer
  ET.SubElement(stp, 'ram:Name').text = organisation.name

  dtc = ET.SubElement(stp, 'ram:DefinedTradeContact')
  ET.SubElement(dtc, 'PersonName').text=organisation.manager
  tuc = ET.SubElement(dtc, 'ram:TelephoneUniversalCommunication')
  ET.SubElement(tuc, 'ram:CompleteNumber').text = organisation.phone

  semail = ET.SubElement(dtc, 'ram:EmailURIUniversalCommunication')
  ET.SubElement(semail, 'ram:URIID').text = organisation.email

  spta = ET.SubElement(stp, 'ram:PostalTradeAddress')
  ET.SubElement(spta, 'ram:PostcodeCode').text = organisation.PLZ
  ET.SubElement(spta, 'ram:LineOne').text = organisation.address
  ET.SubElement(spta, 'ram:CityName').text = organisation.city
  ET.SubElement(spta, 'ram:CountryID').text = 'DE'

  # nemail = ET.SubElement(stp, 'ram:URIUniversalCommunication')
  # ET.SubElement(nemail, 'ram:URIID', schemeID="0088").text = organisation.email

  streg = ET.SubElement(stp, 'ram:SpecifiedTaxRegistration')
  ET.SubElement(streg, 'ram:ID', schemeID='VA').text = organisation.UStID
  # _________________________________Ende Seller

  btp = ET.SubElement(ahta, 'ram:BuyerTradeParty')
  ET.SubElement(btp, 'ram:ID').text = str(customer.id)
  # ET.SubElement(btp, 'ram:GlobalID', schemeID='0088').text ='GLN4000000000'
  ET.SubElement(btp, 'ram:Name').text = customer.name

  dtc = ET.SubElement(btp, 'ram:DefinedTradeContact')
  ET.SubElement(dtc, 'PersonName').text = customer.contact
  btuc = ET.SubElement(btp, 'ram:TelephoneUniversalCommunication')
  ET.SubElement(btuc, 'CompleteNumber').text = customer.phone
  bemail = ET.SubElement(btp, 'ram:EmailURIUniversalCommunication')
  ET.SubElement(bemail, 'ram:URIID', schemeID="0088").text = invoice_address.email

  bpta = ET.SubElement(btp, 'ram:PostalTradeAddress')
  ET.SubElement(bpta, 'ram:PostcodeCode').text = customer.PLZ
  ET.SubElement(bpta, 'ram:LineOne').text = customer.address
  ET.SubElement(bpta, 'ram:CityName').text = customer.city
  ET.SubElement(bpta, 'ram:CountryID').text = customer.country_ID
  # _________________________________Ende Buyer

  ahtd = ET.SubElement(sctt, 'ram:ApplicableHeaderTradeDelivery')

  sttp = ET.SubElement(ahtd, 'ram:ShipToTradeParty')
  # ET.SubElement(sttp, 'ram:GlobalID', schemeID='0088').text = customer.credit_number

  ET.SubElement(sttp, 'ram:Name').text = deliver_address.name

  dpta = ET.SubElement(sttp, 'ram:PostalTradeAddress')
  ET.SubElement(dpta, 'ram:PostcodeCode').text = deliver_address.PLZ
  ET.SubElement(dpta, 'ram:LineOne').text = deliver_address.address
  ET.SubElement(dpta, 'ram:CityName').text = deliver_address.city
  ET.SubElement(dpta, 'ram:CountryID').text = deliver_address.country_ID
  # _________________________________Ende ShipToTradeParty

  adsce = ET.SubElement(ahtd, 'ram:ActualDeliverySupplyChainEvent')
  odt = ET.SubElement(adsce, 'ram:OccurrenceDateTime')
  datestring = invoice.date_deliver
  # ds = datestring.split('-')
  # datedeliver = ds[3] + ds[2] + ds[1]
  ET.SubElement(odt, 'udt:DateTimeString', format='102').text = invoice.date_deliver.strftime('%Y%m%d')
  # _________________________________Ende Delivery


  ahts = ET.SubElement(sctt, 'ram:ApplicableHeaderTradeSettlement')
  ET.SubElement(ahts, 'ram:PaymentReference').text = note.transfer_text # Verwendungszweck
  ET.SubElement(ahts, 'ram:InvoiceCurrencyCode').text = 'EUR'

  stspm = ET.SubElement(ahts, 'ram:SpecifiedTradeSettlementPaymentMeans')
  ET.SubElement(stspm, 'ram:TypeCode').text = '58'
  ET.SubElement(stspm, 'ram:Information').text = note.pay_text + ' ' + invoice.date_due.strftime('%d.%m.%Y')

  ppcfa = ET.SubElement(stspm, 'ram:PayeePartyCreditorFinancialAccount')
  ET.SubElement(ppcfa, 'ram:IBANID').text = bank.IBAN  #.replace(" ", "")
  ET.SubElement(ppcfa, 'ram:AccountName').text = organisation.manager

  pscfi =ET.SubElement(stspm, 'ram:PayeeSpecifiedCreditorFinancialInstitution')
  ET.SubElement(pscfi, 'BICID').text = bank.BIC

  att = ET.SubElement(ahts, 'ram:ApplicableTradeTax')
  ET.SubElement(att, 'ram:CalculatedAmount').text = str(invoice.mwst_sum)
  ET.SubElement(att, 'ram:TypeCode').text = 'VAT'
  ET.SubElement(att, 'ram:BasisAmount').text = str(invoice.netto_sum)
  ET.SubElement(att, 'ram:CategoryCode').text = 'S'

  if customer.country_ID == 'DE':
    ET.SubElement(att, 'ram:RateApplicablePercent').text = '19.00'
  else:
    ET.SubElement(att, 'ram:RateApplicablePercent').text = '0.00'
  # _________________________________Ende ApplicableHeaderTradeSettlement

  # stac = ET.SubElement(ahts, 'ram:SpecifiedTradeAllowanceCharge')
  # ci = ET.SubElement(stac, 'ram:ChargeIndicator')
  # ET.SubElement(ci, 'ram:Indicator').text = 'false'
  # ET.SubElement(stac, 'ram:BasisAmount').text = str(invoice.netto_sum)
  # ET.SubElement(stac, 'ram:ActualAmount').text = '0.00'
  # ET.SubElement(stac, 'ram:Reason').text = ' '
  # ctt = ET.SubElement(stac, 'ram:CategoryTradeTax')
  # ET.SubElement(ctt, 'ram:TypeCode').text = 'VAT'
  # ET.SubElement(ctt, 'ram:CategoryCode').text = 'S'
  # ET.SubElement(ctt, 'ram:RateApplicablePercent').text = '0.00'
  #
  # slsc = ET.SubElement(stac, 'ram:SpecifiedLogisticsServiceCharge')
  # ET.SubElement(slsc, 'ram:Description').text = 'Transportkosten: Frachtbetrag'
  # ET.SubElement(slsc, 'ram:AppliedAmount').text = '0.00'
  # ET.SubElement(slsc, 'ram:ActualTradeCurrencyExchange').text = 'EUR'

  stpt = ET.SubElement(ahts, 'ram:SpecifiedTradePaymentTerms')
  paytext = note.pay_text + ' ' + invoice.date_due.strftime('%d.%m.%Y')
  ET.SubElement(stpt, 'ram:Description').text = paytext
  dddt = SubElement(stpt, 'ram:DueDateDateTime')
  ET.SubElement(dddt, 'udt:DateTimeString',format='102').text = invoice.date_due.strftime('%Y%m%d')

  stshms = ET.SubElement(ahts, 'ram:SpecifiedTradeSettlementHeaderMonetarySummation')
  ET.SubElement(stshms, 'ram:LineTotalAmount').text = str(invoice.netto_sum)
  ET.SubElement(stshms, 'ram:ChargeTotalAmount').text = '0.00'
  ET.SubElement(stshms, 'ram:AllowanceTotalAmount').text = '0.00'
  ET.SubElement(stshms, 'ram:TaxBasisTotalAmount').text = str(invoice.netto_sum)
  ET.SubElement(stshms, 'ram:TaxTotalAmount', currencyID="EUR").text = str(invoice.mwst_sum)
  ET.SubElement(stshms, 'ram:GrandTotalAmount').text = str(invoice.brutto_sum)
  ET.SubElement(stshms, 'ram:TotalPrepaidAmount').text = '0.00'
  ET.SubElement(stshms, 'ram:DuePayableAmount').text = str(invoice.brutto_sum)

  prettify(cii)
  tree = ET.ElementTree(cii)

  file_string = 'ZUGFeRD-invoice.xml'
  path_string = 'orgfiles/' + str(organisation.id) + '/' + str(invoice.number)
  new_dir_path = os.path.join(settings.MEDIA_ROOT, path_string)
  if not os.path.exists(new_dir_path):
    os.makedirs(new_dir_path)
  file_path = 'media/' + path_string + '/' + file_string

  tree.write(file_path, encoding="UTF-8", xml_declaration=True)
  OrgFiles.objects.create(
    organisation=organisation,
    file_name=file_path,
    file_size=os.path.getsize(file_path),
    date_created=timezone.now(),
  )
  invoice.date_genXML = timezone.now()
  invoice.save()
  messages.info(request, "XML-Datei wurde erstellt.")

  return render(request, 'einvoice/invoice_list.html', context)
  # return redirect('einvoice:invoice_detail', pk=pk)


# Source - https://stackoverflow.com/a
# Posted by nacitar sevaht
# Retrieved 2026-01-15, License - CC BY-SA 3.0

def prettify(element, indent='  '):
    iChild = 0
    queue = [(0, element)]  # (level, element)
    while queue:
        level, element = queue.pop(0)
        children = [(level + 1, child) for child in list(element)]
        if children:
            element.text = '\n' + indent * (level+1)  # for child open vorher nur \n
            iChild += 1
        if queue:
            if level - queue[0][0] > 1:
              element.tail = '\n' + indent * (level-1)
              iChild -= 1
            else:
              element.tail = '\n' + indent * queue[0][0]  # for sibling open
        else:
            element.tail = '\n' + indent * (level-1)  # for parent close
        queue[0:0] = children  # prepend so children come before siblings


def editor_detail(request):
  context = create_context_invoice(user_id=request.user.id, invoice_pk=0, customer_pk=0, article_pk=0)
  return render(request, 'einvoice/editor_detail.html', context)



# def acustomer_update(request, pk):
#   customer = get_object_or_404(Customer, pk=pk)
#   form = CustomerForm(instance=customer)
#   context = {
#     'form': form,
#   }
#   if request.method == 'POST' and 'customer_form' in request.POST:
#     form = CustomerForm(request.POST, instance=customer)
#     if form.is_valid():
#       customer = form.save()
#       context = create_context_invoice(user_id=request.user.id, invoice_pk=0, customer_pk=0, article_pk=0)
#       return render(request, 'einvoice/invoice_list.html', context)
#   return render(request, 'einvoice/customer_form.html', context)



def check_if_customerhasinvoiceswitharticles(org_id):
  customer_list = Customer.objects.filter(organisation_id=org_id)
  for customer in customer_list:
    cbdeleted = True
    invoice_list = Invoice.objects.filter(customer_id=customer.id)
    for invoice in invoice_list:
      article_list = Article.objects.filter(invoice_id = invoice.id)
      if article_list.count() > 0:
        cbdeleted = False

    if cbdeleted == True:
      customer.can_be_deleted = 'X'  # x entspricht ja
    else:
      customer.can_be_deleted = ''  # leer entspricht nein
    customer.save()

  return


def customer_delete(request, pk, id):
  invoice = get_object_or_404(Invoice, pk=pk)
  customer = get_object_or_404(Customer, pk=id)
  user_id = request.user.id
  organisation_id = customer.organisation_id

  if request.method == 'GET':
    context = create_context_invoice(user_id=user_id, invoice_pk=invoice.pk, customer_pk=customer.pk, article_pk=0)
    return render(request, 'einvoice/customer_confirm_delete.html', context)
  elif request.method == 'POST':
    customer.delete()
    messages.success(request, "Kunde wurde gelöscht")
    context = create_context_invoice(user_id=user_id, invoice_pk=0, customer_pk=0, article_pk=0)

    return redirect('einvoice:invoice_list')


# def address_add(request, id):
def customer_update(request, id):
  customer = get_object_or_404(Customer, pk=id)
  user_id = request.user.id
  enterprise_list = Enterprise.objects.all()
  enterprise = enterprise_list[0]
  editor = Editor.objects.get(author_id=user_id)
  organisation = Organisation.objects.get(id=editor.organisation_id)

  cform = CustomerForm(instance=customer)

  aform = AddressForm()
  address_list = Address.objects.filter(customer_id=customer.id)
  if address_list.count() > 0:
    for address in address_list:
      if address.addr_type == 'Rechnungsadresse':
        aform.fields['iTitle'].initial = address.title
        aform.fields['iName'].initial = address.name
        aform.fields['iAddress'].initial = address.address
        aform.fields['iPLZ'].initial = address.PLZ
        aform.fields['iCity'].initial = address.city
        aform.fields['iCountry'].initial = address.country
        aform.fields['iCountry_ID'].initial = address.country_ID
        aform.fields['iContactName'].initial = address.contact
        aform.fields['iPhone'].initial = address.phone
        aform.fields['iEmail'].initial = address.email
        aform.fields['iCreditNumber'].initial = address.credit_number

      if address.addr_type == 'Lieferadresse':
        aform.fields['dTitle'].initial = address.title
        aform.fields['dName'].initial = address.name
        aform.fields['dAddress'].initial = address.address
        aform.fields['dPLZ'].initial = address.PLZ
        aform.fields['dCity'].initial = address.city
        aform.fields['dCountry'].initial = address.country
        aform.fields['dCountry_ID'].initial = address.country_ID
        aform.fields['dContactName'].initial = address.contact
        aform.fields['dPhone'].initial = address.phone
        aform.fields['dEmail'].initial = address.email
        aform.fields['dCreditNumber'].initial = address.credit_number

  context = {
    'cform': cform,
    'aform': aform,
    'editor': editor,
    'enterprise': enterprise,
    'organisation': organisation,
    'customer': customer,
  }

  # if request.method == 'POST' and 'cCustomer' in request.POST:
  if request.method == 'POST':
    cform = CustomerForm(request.POST, instance=customer)
    if cform.is_valid():
      customer = cform.save(commit=False)
      customer.organisation_id = organisation.id
      customer.save()
    # context = create_context_invoice(user_id=user_id, invoice_pk=0, customer_pk=id, article_pk=0)
    # return render(request, 'einvoice/invoice_list.html', context)

  # if request.method == 'POST' and 'iCustomer' in request.POST:
    aform = AddressForm(request.POST)
    if aform.is_valid():
      address_list = Address.objects.filter(customer_id=customer.id, addr_type='Rechnungsadresse')
      if address_list.count() > 0:
        address = address_list[0]
      else:
        address = Address.objects.create(customer_id=customer.id, addr_type='Rechnungsadresse')

      address.title=aform.cleaned_data['iTitle']
      address.name=aform.cleaned_data['iName']
      address.address=aform.cleaned_data['iAddress']
      address.PLZ=aform.cleaned_data['iPLZ']
      address.city=aform.cleaned_data['iCity']
      address.country=aform.cleaned_data['iCountry']
      address.country_ID=aform.cleaned_data['iCountry_ID']
      address.contact=aform.cleaned_data['iContactName']
      address.phone=aform.cleaned_data['iPhone']
      address.email=aform.cleaned_data['iEmail']
      address.credit_number=aform.cleaned_data['iCreditNumber']
      address.save()

    # context = create_context_invoice(user_id=user_id, invoice_pk=0, customer_pk=id, article_pk=0)
    # return render(request, 'einvoice/invoice_list.html', context)

  # if request.method == 'POST' and 'dCustomer' in request.POST:
    dform = AddressForm(request.POST)
    if dform.is_valid():
      address_list = Address.objects.filter(customer_id=customer.id, addr_type='Lieferadresse')
      if address_list.count() > 0:
        address = address_list[0]
      else:
        address = Address.objects.create(customer_id=customer.id, addr_type='Lieferadresse')

      address.name=dform.cleaned_data['dName']
      address.address=dform.cleaned_data['dAddress']
      address.PLZ=dform.cleaned_data['dPLZ']
      address.city=dform.cleaned_data['dCity']
      address.country=dform.cleaned_data['dCountry']
      address.country_ID=dform.cleaned_data['dCountry_ID']
      address.contact=dform.cleaned_data['dContactName']
      address.phone=dform.cleaned_data['dPhone']
      address.email=dform.cleaned_data['dEmail']
      address.credit_number=dform.cleaned_data['dCreditNumber']
      address.save()

    context = create_context_invoice(user_id=user_id, invoice_pk=0, customer_pk=id, article_pk=0)
    return render(request, 'einvoice/invoice_list.html', context)

  return render(request, 'einvoice/address_form.html', context)

def customer_add(request):
  form = CustomerForm()
  user_id = request.user.id
  enterprise_list = Enterprise.objects.all()
  enterprise = enterprise_list[0]
  editor = Editor.objects.get(author_id=user_id)
  organisation = Organisation.objects.get(id=editor.organisation_id)
  context = {
    'form': form,
    'editor': editor,
    'enterprise': enterprise,
    'organisation': organisation,
  }

  if request.method == 'POST' and 'customer_form' in request.POST:
    form = CustomerForm(request.POST)
    if form.is_valid():
      customer = form.save(commit=False)
      org_id = organisation.id
      invoice_list = Invoice.objects.filter(organisation_id = org_id)
      customer.organisation_id = org_id
      customer.has_active_invoices = False
      customer.save()

      newinvoice = Invoice()
      newinvoice.customer_id = customer.id
      newinvoice.organisation_id = org_id
      # newinvoice.number = generate_invoice_number(invoice_list)
      newinvoice.save()

      # weitere Adressen anlegen für diesen Customer
      Address.objects.create(
        customer_id=customer.id,
        addr_type='Rechnungsadresse',
        title=customer.title,
        name=customer.name,
        address=customer.address,
        PLZ=customer.PLZ,
        city=customer.city,
        country=customer.country,
        country_ID = customer.country_ID,
        contact=customer.contact,
        phone=customer.phone,
        email=customer.email,
        credit_number = customer.credit_number,
      )
      Address.objects.create(
        customer_id=customer.id,
        addr_type='Lieferadresse',
        title=customer.title,
        name=customer.name,
        address=customer.address,
        PLZ=customer.PLZ,
        city=customer.city,
        country=customer.country,
        country_ID=customer.country_ID,
        contact=customer.contact,
        email=customer.email,
        phone=customer.phone,
        credit_number=customer.credit_number,
      )

      context = create_context_invoice(user_id=user_id, invoice_pk=0, customer_pk=0, article_pk=0)
      # return render(request, 'einvoice/invoice_form.html', context)
    return render(request, 'einvoice/invoice_list.html', context)
    #   return redirect('einvoice/invoice_form.html')

  return render(request, 'einvoice/customer_form.html', context)



def invoice_changeLanguage(request, pk):
  invoice = get_object_or_404(Invoice, pk=pk)
  form = LanguageForm(instance=invoice)
  context = {
    'form': form,
    'invoice': invoice,
  }
  if request.method == "POST":
    form = LanguageForm(request.POST, instance=invoice)
    if form.is_valid():
      invoice = form.save(commit=False)
      invoice.language = form.cleaned_data['language']
      invoice.save()
      context = create_context_invoice(user_id=request.user.id, invoice_pk=pk, customer_pk=0, article_pk=0)
    return render(request, 'einvoice/invoice_detail.html', context)

  return render(request, 'einvoice/language_form.html', context)


def invoice_changeTitle(request, pk):
  invoice = get_object_or_404(Invoice, pk=pk)
  form = TitleForm(instance=invoice)
  context = {
    'form': form,
    'invoice': invoice,
  }
  if request.method == "POST":
    form = TitleForm(request.POST, instance=invoice)
    if form.is_valid():
      invoice = form.save(commit=False)
      invoice.type = form.cleaned_data['type']
      invoice.date_deliver = form.cleaned_data['date_deliver']
      invoice.date_due = form.cleaned_data['date_due']
      invoice.save()
      # context = create_context_invoice(user_id=request.user.id, invoice_pk=pk, customer_pk=0, article_pk=0)
    return redirect('einvoice:invoice_detail', pk=pk)

  return render(request, 'einvoice/title_form.html', context)

def invoice_genPDF(request, pk):
  invoice = Invoice.objects.get(pk=pk)
  customer = Customer.objects.get(pk=invoice.customer_id)
  organisation = invoice.organisation
  organisation_id = invoice.organisation_id

  template_path = 'einvoice/invoice_pdf.html'
  context = create_context_invoice(user_id=request.user.id, invoice_pk=pk, customer_pk=customer.id, article_pk=0)

  # Create a Django response object, and set content type to PDF
  response = HttpResponse(content_type='application/pdf')
  # if pdfdownload:
  # response['Content-Disposition'] = 'attachment; filename=' + 'media/pdfs/' + 'Re' + str(invoice.number) + '.pdf'
  # if pdfdisplay:
  # response['Content-Disposition'] = 'filename=' + 'media/pdfs/' + 'Re' + str(invoice.number) + '.pdf'

  # find the template and render it.
  template = get_template(template_path)
  html = template.render(context)

  # create a pdf
  # pisa_status = pisa.CreatePDF(
  #   html, dest=response,
  # )
  filename = 'media/orgfiles/' + str(organisation_id) + '/Re' + str(invoice.number) + '.pdf'

  with open(filename, 'wb+') as destination:
    pisa_status = pisa.CreatePDF(
      html, dest=destination,
    )
    # if error then show some funny view
    if pisa_status.err:
      return HttpResponse('We had some errors <pre>' + html + '</pre>')
    else:
      OrgFiles.objects.update_or_create(
        organisation=organisation,
        file_name=filename,
        file_size=os.path.getsize(filename),
        date_created=timezone.now(),
      )
      invoice.date_genPDF = timezone.now()
      invoice.save()

    try:
      return FileResponse(open(filename, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
      raise Http404()

  return redirect('einvoice:invoice_detail', pk=pk)



# def invoice_showPDF(request,pk):
#   invoice = Invoice.objects.get(pk=pk)
#   filename = 'Re' + invoice.number + '.pdf'
#   filename = 'media/pdfs/' + 'Re' + str(invoice.number) + '.pdf'
#   try:
#     return FileResponse(open(filename, 'rb'), content_type='application/pdf')
#   except FileNotFoundError:
#     raise Http404()



def generate_invoice_number(invoice_list, org_id):
  currentyear = timezone.now().year
  intyear = currentyear * 1000  # 2025000

  if len(invoice_list) > 0:
    # org_id = 1
    # org_id = invoice_list[0].organisation_id

    sinumber = invoice_list[0].number
    s = "".join([c for c in sinumber if not c.isdigit()])  # Getting letters
    n = "".join([c for c in sinumber if c.isdigit()])  # Getting numbers
    maxno = int(n)

    for invoice in invoice_list:
      sinumber = invoice.number
      s = "".join([c for c in sinumber if not c.isdigit()])  # Getting letters
      n = "".join([c for c in sinumber if c.isdigit()])  # Getting numbers
      intnumber = int(n)
      if intnumber > maxno:
        maxno = int(n)

    strno = str(maxno)

    if org_id == 3:  # EDVIN
      noyear = strno[:4]
      if noyear == str(currentyear):
        new_number = str(maxno + 1)
      else:
        new_number = str(intyear + 101)

      return new_number

    else:
      new_number = s + str(maxno + 1)

    return new_number

  else:
    new_number = str(intyear + 101)
    return new_number


def invoice_add(request):
  user_id = request.user.id
  editor = Editor.objects.get(author_id=user_id)
  enterprise_list = Enterprise.objects.all()
  enterprise = enterprise_list[0]
  organisation = Organisation.objects.get(id=editor.organisation_id)
  invoice_list = Invoice.objects.filter(organisation_id=organisation.id)
  newiNumber = generate_invoice_number(invoice_list, organisation.id)

  if request.method == 'POST':
    form = InvoiceForm(request.POST, user=request.user)

    if form.is_valid():
      invoice = form.save(commit=False)
      invoice.organisation = organisation
      invoice.number = form.cleaned_data['number']
      now = timezone.now()
      now10 = now + timedelta(days=10)
      now30 = now + timedelta(days=30)
      invoice.date_due = now10
      invoice.date_deliver = now30
      invoice = form.save(commit=True)
      invoice_id = invoice.id
      context = create_context_invoice(user_id=user_id, invoice_pk=invoice_id, customer_pk=0, article_pk=0)
      return render(request, 'einvoice/invoice_detail.html', context)


  else:
    initial_data = {
      'number': newiNumber,
    }
    form = InvoiceForm(request.GET, initial=initial_data, user=request.user)
    context = {
      'form': form,
      'editor': editor,
      'organisation': organisation,
      'enterprise': enterprise,
      'newiNumber': newiNumber,
    }
    return render(request, 'einvoice/invoice_form.html', context)

  context = {
    'form': form,
    'editor': editor,
    'organisation': organisation,
    'enterprise': enterprise,
    'newiNumber': newiNumber,
  }
  return render(request, 'einvoice/invoice_form.html', context)


class InvoiceListView(LoginRequiredMixin, ListView):
  model = Invoice
  context_object_name = 'invoices'
  template_name = 'einvoice/invoice_list.html'

  def __init__(self):
    super().__init__()
    self.request = None

  def get_context_data(self, **kwargs):
    user_id = self.request.user.id
    context = create_context_invoice(user_id, invoice_pk=0, customer_pk=0, article_pk=0)
    return context



def create_context_invoice(user_id, invoice_pk, customer_pk, article_pk):
  editor = Editor.objects.get(author_id=user_id)
  enterprise_list = Enterprise.objects.all()
  enterprise = enterprise_list[0]
  organisation = Organisation.objects.get(id=editor.organisation_id)
  org_id = organisation.id

  invoice_list = Invoice.objects.filter(organisation_id=organisation.id)
  check_if_customerhasinvoiceswitharticles(org_id)

  # Basis Data
  context = {
    'editor': editor,
    'enterprise': enterprise,
    'organisation': organisation,
    'invoice_list': invoice_list,
  }

  if invoice_pk > 0:
    invoice = Invoice.objects.get(pk=invoice_pk)
    note = Note.objects.get(language=invoice.language)
    text = Text.objects.get(language=invoice.language)
    customer = Customer.objects.get(pk=invoice.customer_id)
    article_list = Article.objects.filter(invoice=invoice)
    article_list_sorted = sorted(article_list, key=lambda item: item.pos)
    iNOfArticles = article_list.count()
    calculate_sum(invoice, article_list)

    if invoice.type == 'Rechnung':
      docTitle = text.Rechnung
    elif invoice.type == 'Angebot':
      docTitle = text.Angebot
    elif invoice.type == 'Auftragsbestätigung':
      docTitle = text.Auftrag
    else:
      docTitle = text.Gutschrift

    context['invoice'] = invoice
    context['invoice_id'] = invoice_pk
    context['article_list'] = article_list_sorted
    context['iNOfArticles'] = iNOfArticles
    context['customer'] = customer
    context['note'] = note
    context['text'] = text
    context['type'] = invoice.type
    context['docTitle'] = docTitle

  if article_pk > 0:    # article_add, delete, update and pdf
    invoice = Invoice.objects.get(pk=invoice_pk)
    # article_list = Article.objects.filter(invoice=invoice)
    article = Article.objects.get(pk=article_pk)
    context['article'] = article
    # calculate_sum(invoice, article_list)

  if customer_pk > 0: # customer_delete and pdf
    bank = Bank.objects.get(organisation_id=org_id)
    context['bank'] = bank

  return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
  model = Invoice
  template_name = 'einvoice/invoice_detail.html'

  def get_context_data(self, **kwargs):
    user_id = self.request.user.id
    context = create_context_invoice(user_id, invoice_pk=self.kwargs['pk'], customer_pk=0, article_pk=0)
    return context



class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
  model = Invoice
  form_class = InvoiceForm
  template_name = 'einvoice/invoice_form.html'
  success_url = reverse_lazy('einvoice:invoice_list')


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
  model = Invoice
  context_object_name = 'invoice'
  success_url = reverse_lazy('einvoice:invoice_list')
  success_message = '%(number) gelöscht.'
  def get_success_message(self, cleaned_data):
    return self.get_success_message(dict(
      cleaned_data,
      number=cleaned_data['number']
    ))

  def form_valid(self, form):
    messages.success(self.request, "Rechnung gelöscht.")
    return super(InvoiceDeleteView, self).form_valid(form)


def article_add(request, pk):
  user = request.user
  form = ArticleForm(initial={'pos': '3.2'})
  invoice = get_object_or_404(Invoice, pk=pk)
  enterprise_list = Enterprise.objects.all()
  enterprise = enterprise_list[0]
  editor = Editor.objects.get(author_id=user)
  organisation = Organisation.objects.get(id=editor.organisation_id)
  customer = Customer.objects.get(pk=invoice.customer_id)

  article_list = Article.objects.filter(invoice=invoice)
  iNOfArticles = article_list.count()
  article_list_sorted = sorted(article_list, key=lambda item: item.pos)
  context = {
    'invoice': invoice,
    'form': form,
    'article_list': article_list_sorted,
    'iNOfArticles': iNOfArticles,
    'enterprise': enterprise,
    'editor': editor,
    'organisation': organisation,
    'customer': customer,
  }
  if request.method == 'POST':
    form = ArticleForm(request.POST)
    print(form.errors.as_data())
    newpos = form.data['pos']

    for article in article_list:
      actpos = article.pos
      if actpos == newpos:
        messages.error(request, "Positionsnummer schon vorhanden")
        return render(request, 'einvoice/article_form.html', context)

    print(form.errors.as_data())
    if form.is_valid():
      article = form.save(commit=False)
      makeUnit(invoice, article)

      article.price_pos = article.price * article.nofArticles
      article.invoice = invoice
      article= form.save(commit=True)
      context = create_context_invoice(user_id=request.user.id, invoice_pk=invoice.id, customer_pk=0, article_pk=article.pk)
      return render(request, 'einvoice/invoice_detail.html', context)

  return render(request, 'einvoice/article_form.html', context)


def makeUnit(invoice, article):
    unit = Unit.objects.get(language=invoice.language)
    if article.unit == '1' or article.unit == 'Std':
      article.unit = unit.std
    elif article.unit == '2' or article.unit == 'Stk':
      article.unit = unit.stk
    elif article.unit == '3' or article.unit == 'km':
      article.unit = unit.km
    else:
      article.unit = ' '

def calculate_sum(invoice, article_list):
  mwst = 0
  sum = 0
  service = 0
  for article in article_list:
    if article.category == "3":
      service = service + article.price_pos
    if article.category != "2":  # Titel
      sum = sum + article.price_pos
      mwst = mwst + article.price_pos * article.tax_percentage/100
  total = sum + mwst
  invoice.netto_sum = f"{sum:.2f}"
  invoice.mwst_sum = f"{mwst:.2f}"
  invoice.service_sum = f"{service:.2f}"
  invoice.brutto_sum = f"{total:.2f}"
  invoice.save(update_fields=['netto_sum', 'service_sum', 'mwst_sum', 'brutto_sum'])
  return


def article_delete(request, pk, id):
  user_id = request.user.id
  invoice = get_object_or_404(Invoice, pk=pk)
  article = Article.objects.get(id=id)
  context = create_context_invoice(user_id=request.user.id, invoice_pk=invoice.pk, customer_pk=0, article_pk=article.pk)
  if request.method == 'GET':
    return render(request, 'einvoice/article_confirm_delete.html', context)
  elif request.method == 'POST':
    article.delete()
    messages.success(request, f"Artikel wurde gelöscht")
    # article_list = Article.objects.filter(invoice=invoice)
    # article_list_sorted = sorted(article_list, key=lambda item: item.pos)
    # calculate_sum(invoice, article_list)
    context = create_context_invoice(user_id=user_id, invoice_pk=invoice.pk, customer_pk=0,
                                     article_pk=0)
    # return redirect('einvoice:invoice_detail', pk=pk)
    return render(request, 'einvoice/invoice_detail.html', context)


def article_update(request, pk, id):
  invoice = get_object_or_404(Invoice, pk=pk)
  article = get_object_or_404(Article, pk=id)
  article_list = Article.objects.filter(invoice=invoice)
  article_list_sorted = sorted(article_list, key=lambda item: item.pos)
  form = ArticleForm(instance=article)
  context = {
    'invoice': invoice,
    'form': form,
    'article_list': article_list_sorted,
  }
  if request.method == "POST":
    form = ArticleForm(request.POST, instance=article)
    if form.is_valid():
      article = form.save(commit=False)
      article.price_pos = article.price * article.nofArticles
      article.invoice = invoice
      makeUnit(invoice, article)
      article= form.save(commit=True)
      context = create_context_invoice(user_id=request.user.id, invoice_pk=invoice.pk, customer_pk=0, article_pk=article.pk)
    return render(request, 'einvoice/invoice_detail.html', context)

  return render(request, 'einvoice/article_form.html', context)





# def image_add(request, pk):
#   form = ImageForm()
#   invoice = get_object_or_404(Invoice, pk=pk)
#   context = {
#     'invoice': invoice,
#     'form': form
#   }
#   if request.method == 'POST':
#     form = ImageForm(request.POST)
#     if form.is_valid():
#       article = form.save(commit=False)
#       article.invoice = invoice
#       article.description = ''
#       article.category = 3
#       article.save()
#       context = {
#         'invoice': invoice,
#         'article_list': Article.objects.all(),
#       }
#     return render('einvoice/article_list.html', context)
#   return render(request, 'einvoice/title_form.html', context)



def convert_csv_to_text(csv_file_path):
  with open(csv_file_path, 'r') as file:
    reader = csv.reader(file)
    rows = list(reader)

  text = ''
  for row in rows:
    text += ','.join(row) + '\n'

  return text



def get_files_from_directory(directory_path):
  files = []
  for filename in os.listdir(directory_path):
    file_path = os.path.join(directory_path, filename)
    if os.path.isfile(file_path):
      try:
        print(' > file_path ' + file_path)
        _, extension = os.path.splitext(filename)
        if extension.lower() == '.csv':
          csv_text = convert_csv_to_text(file_path)
        else:
          csv_text = ''

        files.append({
          'file': file_path.split(os.sep + 'media' + os.sep)[1],
          'filename': filename,
          'file_path': file_path,
          'csv_text': csv_text
        })
      except Exception as e:
        print(' > ' + str(e))
  return files


# def save_info(request, file_path):
#   path = file_path.replace('%slash%', '/')
#   if request.method == 'POST':
#     FileInfo.objects.update_or_create(
#       path=path,
#       defaults={
#         'info': request.POST.get('info')
#       }
#     )
#
#   return redirect(request.META.get('HTTP_REFERER'))


def get_breadcrumbs(request):
  path_components = [component for component in request.path.split("/") if component]
  breadcrumbs = []
  url = ''

  for component in path_components:
    url += f'/{component}'
    if component == "file-manager":
      component = "media"
    breadcrumbs.append({'name': component, 'url': url})

  return breadcrumbs


def file_manager(request, directory=''):
  media_path = os.path.join(settings.MEDIA_ROOT)
  directories = generate_nested_directory(media_path, media_path)
  selected_directory = directory

  files = []
  selected_directory_path = media_path + selected_directory
  # selected_directory_path = os.path.join(media_path, selected_directory)
  if os.path.isdir(selected_directory_path):
    files = get_files_from_directory(selected_directory_path)

  breadcrumbs = get_breadcrumbs(request)

  context = {
    'directories': directories,
    'files': files,
    'selected_directory': selected_directory,
    'segment': 'file_manager',
    'breadcrumbs': breadcrumbs
  }
  return render(request, 'einvoice/file-manager.html', context)


def generate_nested_directory(root_path, current_path):
  directories = []
  for name in os.listdir(current_path):
    if os.path.isdir(os.path.join(current_path, name)):
      unique_id = str(uuid.uuid4())
      nested_path = os.path.join(current_path, name)
      nested_directories = generate_nested_directory(root_path, nested_path)
      directories.append({'id': unique_id, 'name': name, 'path': os.path.relpath(nested_path, root_path),
                          'directories': nested_directories})
  return directories


def delete_file(request, file_path):
  path = file_path.replace('%slash%', '/')
  absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
  os.remove(absolute_file_path)
  print("File deleted", absolute_file_path)
  return redirect(request.META.get('HTTP_REFERER'))


def download_file(request, file_path):
  path = file_path.replace('%slash%', '/')
  absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
  if os.path.exists(absolute_file_path):
    with open(absolute_file_path, 'rb') as fh:
      response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
      response['Content-Disposition'] = 'inline; filename=' + os.path.basename(absolute_file_path)
      return response
  raise Http404


def upload_file(request):
  media_path = os.path.join(settings.MEDIA_ROOT)
  selected_directory = request.POST.get('directory', '')
  selected_directory_path = media_path + selected_directory
  # selected_directory_path = os.path.join(media_path, selected_directory)
  if request.method == 'POST':
    file = request.FILES.get('file')
    file_path = os.path.join(selected_directory_path, file.name)
    with open(file_path, 'wb') as destination:
      for chunk in file.chunks():
        destination.write(chunk)

  return redirect(request.META.get('HTTP_REFERER'))


# def openFile():
#   filepath = filedialog.askopenfilename()
#   file = open(filepath, 'r')
#   print(file.read())
#   file.close()
#
# def invoice_add(request):
#   openFile()

  # form = InvoiceForm()
  # enterprise = Enterprise.objects.first()
  # context = {
  #   'enterprise': enterprise,
  #   'form': form,
  # }
  # if request.method == 'POST':
  #   form = InvoiceForm(request.POST)
  #   if form.is_valid():
  #     invoice = form.save(commit=False)
  # return redirect('einvoice:invoice_list')


# def get_files_from_directory(directory_path):
#   files = []
#   for filename in os.listdir(directory_path):
#     file_path = os.path.join(directory_path, filename)
#     if os.path.isfile(file_path):
#       try:
#         print(' > file_path ' + file_path)
#         _, extension = os.path.splitext(filename)
#         if extension.lower() == '.csv':
#           csv_text = convert_csv_to_text(file_path)
#         else:
#           csv_text = ''
#
#         files.append({
#           'file': file_path.split(os.sep + 'media' + os.sep)[1],
#           'filename': filename,
#           'file_path': file_path,
#           'csv_text': csv_text
#         })
#       except Exception as e:
#         print(' > ' + str(e))
#   return files


