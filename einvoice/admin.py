from django.contrib import admin
from typing_extensions import TextIO

from einvoice.models import (Editor, Address, Article, Bank, Customer, Enterprise, Invoice, Organisation, Text, Note, Unit)

# Register your models here.
admin.site.register(Editor)
admin.site.register(Enterprise)
admin.site.register(Organisation)
admin.site.register(Customer)
admin.site.register(Invoice)
admin.site.register(Article)
admin.site.register(Bank)
admin.site.register(Address)
admin.site.register(Text)
admin.site.register(Note)
admin.site.register(Unit)

