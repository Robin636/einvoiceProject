from fileinput import filename

from django.db import models
# from django.db.models import Max
from localflavor.generic.models import IBANField
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from datetime import datetime, timezone


# Create your models here.
# das bin ich mit meinem Applogo
class Enterprise(models.Model):
  name = models.CharField(max_length=100)
  address = models.CharField(max_length=100)
  text = models.CharField(max_length=100, blank=True)
  slogan = models.CharField(max_length=100, blank=True)
  logo = models.ImageField(default='logo.png', upload_to='logos',blank=True)

  def __str__(self):
    return self.name


class Editor(models.Model):
  author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
  organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, related_name='organisation_editors')
  firstname = models.CharField(max_length=50)
  lastname = models.CharField(max_length=50)
  email = models.EmailField(default=' ', blank=True)
  street = models.CharField(max_length=50, default=' ', blank=True)
  houseno = models.CharField(max_length=50, default=' ', blank=True)
  pid = models.IntegerField(default=0, blank=True)
  city = models.CharField(max_length=50, default=' ', blank=True)
  telefon = models.CharField(max_length=20, default=' ', blank=True)
  mobile = models.CharField(max_length=20, default=' ', blank=True)

  def __str__(self):
    return self.firstname + ' ' + self.lastname + ' ' + self.organisation.name + ' ' + str(self.organisation_id)


# Verkäufer
class Organisation(models.Model):
  name = models.CharField(max_length=100)
  manager = models.CharField(max_length=100, blank=True)
  address = models.CharField(max_length=100)
  PLZ = models.CharField(max_length=10, default='Org_PLZ', blank=True)
  city = models.CharField(max_length=50, default='Org_city', blank=True)
  phone = models.CharField(max_length=50, default='Tel. Nr Verkäufer', blank=True)
  email = models.EmailField(max_length=100, blank=True)
  website = models.URLField(max_length=100, blank=True)
  UStID = models.CharField(max_length=14, default='USTID')
  taxno = models.CharField(max_length=13, blank=True, default='201/113/40209')
  HRBno = models.CharField(max_length=30, blank=True, default='')
  court = models.CharField(max_length=50, blank=True, default='')
  slogan = models.TextField(blank=True)
  # logo = models.ImageField(upload_to='logo', blank=True)
  logo = models.ImageField()

  def __str__(self):
    return self.name + "  " + self.address


class Bank(models.Model):
  # needed for Briefkopf
  organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, related_name='organisation_banks')
  accountname = models.CharField(max_length=100, default='Empfängername ')
  bankname = models.CharField(max_length=30, default='Bankname')
  IBAN = IBANField(include_countries=IBAN_SEPA_COUNTRIES)
  BIC = models.CharField(max_length=12, default='BIC')

  def __str__(self):
    return self.BIC + " " + self.IBAN

# Käufer
class Customer(models.Model):
  organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, related_name='organisation_customers', default=1)
  title = models.CharField(max_length=50, default='Customertitle')
  name = models.CharField(max_length=50, default='Customername')
  address = models.CharField(max_length=100, default='Customeraddress')
  PLZ = models.CharField(max_length=10, default='Cust PLZ')
  city = models.CharField(max_length=50, default='Customercity')
  country = models.CharField(max_length=20, default='Deutschland')
  country_ID = models.CharField(max_length=2, default='DE')
  email = models.EmailField(max_length=100, default='info@customer.de')
  contact = models.CharField(max_length=100, default='Hans Zimmer')
  phone = models.CharField(max_length=50, default='Telefonnummer')
  credit_number = models.CharField(max_length=20, default='549910', blank=True)
  can_be_deleted = models.CharField(max_length=4, default='X')

  def __str__(self):
    return self.name + "   " + self.address


addr_type_CHOICES = [('1', 'Rechnungsadresse'), ('2', 'Lieferadresse')]

class Address(models.Model):
  customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='customer_address')
  addr_type = models.CharField(max_length=20, choices=addr_type_CHOICES, default='Rechnungsadresse')
  title = models.CharField(max_length=15, default='Titel', blank=True)
  name = models.CharField(max_length=100, default='Name', blank=True)
  address = models.CharField(max_length=100, default='Address', blank=True)
  PLZ = models.CharField(max_length=10, default='PLZ', blank=True)
  city = models.CharField(max_length=50, default='City', blank=True)
  country = models.CharField(max_length=20, default='Country', blank=True)
  country_ID = models.CharField(max_length=2, default='DE', blank=True)
  contact = models.CharField(max_length=100, default='Kontakt Name', blank=True)
  phone = models.CharField(max_length=50, default='Tel. Nr. Kontakt', blank=True)
  email = models.EmailField(max_length=100, default='info@address.de', blank=True)
  credit_number = models.CharField(max_length=20, default='549910', blank=True)

  def __str__(self):
    return self.addr_type + ": " + self.name



class Text(models.Model):
  language = models.CharField(max_length=2, default='DE')
  pos = models.CharField(max_length=20, blank=True, default='Pos.')
  Beschreibung = models.CharField(max_length=100, blank=True, default='Beschreibung')
  Menge = models.CharField(max_length=100, blank=True, default='Menge')
  Einheit = models.CharField(max_length=100, blank=True, default='Einheit')
  EPreis = models.CharField(max_length=100, blank=True, default='E-Preis')
  Preis = models.CharField(max_length=100, blank=True, default='Preis')
  StSatz = models.CharField(max_length=100, blank=True, default='St-Satz')
  Summe = models.CharField(max_length=20, blank=True, default='Summe')
  MwSt = models.CharField(max_length=20, blank=True, default='MwSt')
  Gesamt = models.CharField(max_length=20, blank=True, default='Gesamt')
  Empfaenger = models.CharField(max_length=20, blank=True, default='Empfänger')
  Rechnung = models.CharField(max_length=20, blank=True, default='RECHNUNG')
  Angebot = models.CharField(max_length=20, blank=True, default='ANGEBOT')
  Auftrag = models.CharField(max_length=20, blank=True, default='AUFTRAGSBESTÄTIGUNG')
  Gutschrift = models.CharField(max_length=20, blank=True, default='GUTSCHRIFT')
  USTID = models.CharField(max_length=20, blank=True, default='USt-ID')

  def __str__(self):
    return "Texte in " + self.language


class Unit(models.Model):
  language = models.CharField(max_length=2, default='DE')
  std = models.CharField(max_length=5, blank=True, default='Std')
  stk = models.CharField(max_length=5, blank=True, default='Stk')
  km = models.CharField(max_length=5, blank=True, default='km')

  def __str__(self):
    return "Units in " + self.language

class Note(models.Model):
  language = models.CharField(max_length=2, default='DE')
  eigentums_text = models.CharField(max_length=100, blank=True, default='Der Verkäufer bleibt Eigentümer der Waren bis zur vollständigen Erfüllung der Kaufpreisforderung.')
  bonus_text = models.CharField(max_length=100, blank=True, default='Es bestehen keine Rabatt- oder Bonusvereinbarungen.')
  thankyou_text = models.CharField(max_length=100, blank=True, default='Vielen Dank für den Auftrag!')
  offer_text = models.CharField(max_length=100, blank= True, default='Ich würde mich über den Auftrag freuen!')
  advice_text = models.CharField(max_length=100, blank=True, default='Es gelten die AGBs der Homepage.')
  pay_text = models.CharField(max_length=100, blank=True, default='Bitte bezahlen Sie den Gesamtbetrag bis zum ')
  service_text = models.CharField(max_length=80, blank=True, default='Enthaltene Dienstleistung:')
  transfer_text = models.CharField(max_length=80, blank=True, default='Bitte Rechnungsnummer angeben!')

  def __str__(self):
    return "Notes in " + self.language


lang_CHOICES = [('DE', 'DE'), ('EN', 'EN'), ('FR', 'FR')]
invoice_CHOICES = [('Rechnung', 'Rechnung'), ('Angebot', 'Angebot'), ('Auftragsbestätigung', 'Auftragsbestätigung'), ('Gutschrift', 'Gutschrift')]

class Invoice(models.Model):
  customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='customer_invoices')
  organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='organisation_invoices')
  type = models.CharField(max_length=30, choices=invoice_CHOICES, default='Rechnung')
  number = models.CharField(max_length=20, default='2026101')
  timeperiod = models.CharField(max_length=100, default='Timeperiod', blank=True)
  netto_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
  service_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
  mwst_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
  brutto_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
  language = models.CharField(max_length=2, choices=lang_CHOICES, default='DE')
  date_created = models.DateField(auto_now_add=True)
  date_genPDF = models.DateTimeField(default=None, blank=True, null=True)
  date_genXML = models.DateTimeField(default=None, blank=True, null=True)
  date_due = models.DateTimeField(default=None, blank=True, null=True)  # Zahlungsdatum
  date_sentFiles = models.DateTimeField(default=None, blank=True, null=True)
  date_deliver = models.DateTimeField(null=True)


  def __str__(self):
    return str(self.number) + " " + str(self.date_created) + " " + self.customer.name
    # return self.customer.name + " " + str(self.number) + " " + str(self.date_created)


cat_CHOICES = [('1', 'Dienstleistung'), ('2', 'Titel'), ('3', 'Artikel'), ('4', 'Rabatt')]
unit_CHOICES = [('1', 'Std'), ('2', 'Stk'), ('3', 'km'), ('0', ' ')]


class Article(models.Model):
  invoice = models.ForeignKey('einvoice.Invoice', on_delete=models.CASCADE, related_name='invoice_articles')
  category = models.CharField(max_length=14, choices=cat_CHOICES, default='Artikel')
  pos = models.CharField(max_length=5, default='2.1')
  description = models.CharField(max_length=100, blank=True, default='Artikeltext')
  nofArticles = models.DecimalField(max_digits=6, decimal_places=2, default=1.0)
  unit = models.CharField(max_length=3, choices=unit_CHOICES, default='Std')
  price = models.DecimalField(max_digits=10, decimal_places=2, default=70.00)
  price_pos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
  tax_percentage = models.DecimalField(max_digits=2, decimal_places=0, default=19)

  def __str__(self):
    return self.description


class OrgFiles(models.Model):
  organisation = models.ForeignKey('einvoice.Organisation', on_delete=models.CASCADE, related_name='organisation_files')
  file_name = models.CharField(max_length=100, blank=True, default='OrgFilename')
  date_created = models.DateTimeField(default=None, blank=True, null=True)
  file_size = models.IntegerField(default=0)

  def __str__(self):
    return self.file_name
