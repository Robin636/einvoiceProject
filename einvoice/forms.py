from unicodedata import category

import bootstrap_datepicker_plus
from django import forms
from django.db.models import CharField
from grappelli.tests.models import Category

# from setuptools.package_index import user_agent

from einvoice.models import Invoice, Article, Customer, Editor, Organisation, lang_CHOICES
from django.forms import Textarea, RadioSelect, DateInput, NumberInput, BaseModelFormSet
from django.core import validators
from django.contrib.auth.models import User
from bootstrap_datepicker_plus.widgets import DatePickerInput, TimePickerInput, DateTimePickerInput
from crispy_forms.helper import FormHelper


# from django.forms import fields
import datetime
from datetime import datetime
from django.db.models.functions import LastValue
# import time


class InvoiceForm(forms.ModelForm):
  required_css_class = 'required'

  def __init__(self, *args, **kwargs):
    # super().__init__()
    user = kwargs.pop('user', None)
    super(InvoiceForm, self).__init__(*args, **kwargs)
    editor = Editor.objects.get(author_id=user)
    organisation_id = Organisation.objects.get(id=editor.organisation_id).id

    self.fields['customer'] = forms.ModelChoiceField(queryset=Customer.objects.filter(organisation_id = organisation_id))

  class Meta:
    model = Invoice
    fields = ('number', 'customer', 'language')
    labels = {'number': 'Rechnungsnummer', 'customer': 'Kundenname', 'language': 'Sprache'}



  # class Meta:
  #   model = Invoice
    # fields = ('customer', 'number')
    # labels = {'number' : 'Rechnungsnummer', 'customer': 'Kundenname'}
    # widgets={
    #   'traveldate': DatePickerInput(),
    #   'starttime': TimePickerInput(),
    #   'endtime': TimePickerInput(),
    # }
    # type = forms.ChoiceField(label="Art", choices=[('K', 'KFZ'), ('F', 'Flug'), ('Z', 'Zug')])
    # km = forms.IntegerField(label="Gefahrene km")
    # comment = forms.CharField(widget=forms.Textarea(attrs={'rows':5, 'cols':20,}))



class ArticleForm(forms.ModelForm):
  required_css_class = 'required'
  class Meta:
    model = Article
    fields = ['pos', 'description', 'nofArticles', 'unit',
              'price', 'tax_percentage', 'category']
    # description = forms.CharField(widget=forms.Textarea(attrs={'rows':1, 'cols':100,}))
    # nofArticles = forms.DecimalField(widget=forms.NumberInput(attrs={'min':0, 'max':5000}))


# class ImageForm(forms.ModelForm):
#   required_css_class = 'required'
#   class Meta:
#     model = Image
#     fields = ['name', 'image']
#     labels = {'name': 'Bez.', 'image': 'Bild'}


class TitleForm(forms.ModelForm):
  required_css_class = 'required'
  class Meta:
    model = Invoice
    fields = ['type', 'date_deliver', 'date_due']
    # labels = {'type': 'Dokumenttype', 'date_deliver': 'Lieferdatum'}
    widgets = {
      'date_deliver': DatePickerInput(),
      'date_due': DatePickerInput(),
    }
    options = {
      'format': 'DD.MM.YYYY',
      'locale': 'de_DE',
    }


class LanguageForm(forms.ModelForm):
  required_css_class = 'required'
  class Meta:
    model = Invoice
    fields = ['language']
    labels = {'language': 'Sprache der Rechnung'}


class AddressForm(forms.Form):
  iTitle = forms.CharField(label='Titel', max_length=15, required=False)
  iName = forms.CharField(label='Kundenname', max_length=60, required=False)
  iAddress = forms.CharField(label='Adresse', max_length=60, required=False)
  iPLZ = forms.CharField(label='PLZ', max_length=10, required=False)
  iCity = forms.CharField(label='Stadt', max_length=30, required=False)
  iCountry = forms.CharField(label='Land', max_length=30, required=False)
  iCountry_ID = forms.CharField(label='Country ID', max_length=3, required=False)
  iContactName = forms.CharField(label='Kontakt Name', max_length=60, required=False)
  iPhone = forms.CharField(label='Tel. Nr. Kontakt', max_length=50, required=False)
  iEmail = forms.CharField(label='Email', max_length=60, required=False)
  iCreditNumber = forms.CharField(label='Kreditoren Number', max_length=30, required=False)
  dTitle = forms.CharField(label='Titel', max_length=15, required=False)
  dName = forms.CharField(label='Kundenname', max_length=60, required=False)
  dAddress = forms.CharField(label='Adresse', max_length=60, required=False)
  dPLZ = forms.CharField(label='PLZ', max_length=10, required=False)
  dCity = forms.CharField(label='Stadt', max_length=30, required=False)
  dCountry = forms.CharField(label='Land', max_length=30, required=False)
  dCountry_ID = forms.CharField(label='Country ID', max_length=3, required=False)
  dContactName = forms.CharField(label='Kontakt Name', max_length=60, required=False)
  dPhone = forms.CharField(label='Tel. Nr. Kontakt', max_length=50, required=False)
  dEmail = forms.CharField(label='Email', max_length=60, required=False)
  dCreditNumber = forms.CharField(label='Kreditoren Number', max_length=30, required=False)



class CustomerForm(forms.ModelForm):
  required_css_class = 'required'
  class Meta:
    model = Customer
    fields = ['title', 'name', 'address', 'PLZ', 'city', 'country', 'country_ID', 'contact', 'phone', 'email', 'credit_number']
    # labels = {'title': 'Titel', 'name': 'Name', 'address': 'Adresse', 'PLZ': 'PLZ', 'city': 'Stadt',
    #           'country': 'Land', 'contact': 'Kontaktperson', 'email': 'E-Mail'}