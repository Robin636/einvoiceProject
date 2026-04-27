from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import include, path, re_path

# from django.conf.urls import include


from einvoice import views


# from django.urls import re_path as url

# from . import views
# from django.urls import include, path, re_path

app_name = 'einvoice'

urlpatterns = [
  path('', views.index, name='index'),
  path('admin/', admin.site.urls),
  path('accounts/', include('django.contrib.auth.urls')),
  path('about/', views.AboutView.as_view(), name='about'),

  path('einvoice/', views.InvoiceListView.as_view(), name='invoice_list'),
  path('editor/', views.editor_detail, name='editor_detail'),

  path('invoice/add', views.invoice_add, name='invoice_add'),
  path('invoice/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
  path('invoice/<int:pk>/update', views.InvoiceUpdateView.as_view(), name='invoice_update'),
  path('invoice/<int:pk>/delete', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
  path('invoice/<int:pk>/genPDF', views.invoice_genPDF, name='invoice_genPDF'),
  path('invoice/<int:pk>/genXML', views.invoice_genXML, name='invoice_genXML'),
  path('invoice/<int:pk>/send', views.invoice_send, name='invoice_send'),

  path('invoice/<int:pk>/changeTitle', views.invoice_changeTitle, name='invoice_changeTitle'),
  path('invoice/<int:pk>/changeLanguage', views.invoice_changeLanguage, name='invoice_changeLanguage'),

  path('customer/add', views.customer_add, name='customer_add'),
  path('customer/<int:id>/update', views.customer_update, name='customer_update'),
  path('invoice/<int:pk>/customer/<int:id>/delete', views.customer_delete, name='customer_delete'),

  path('invoice/<int:pk>/article/add', views.article_add, name='article_add'),
  path('invoice/<int:pk>/article/<int:id>/delete', views.article_delete, name='article_delete'),
  path('invoice/<int:pk>/article/<int:id>/', views.article_update, name='article_update'),


  # path('file-manager/', views.file_manager, name='file_manager'),
  # path(r'^file-manager/(?P<directory>.*)?/$', views.file_manager, name='file_manager'),
  # path('delete-file/<str:file_path>/', views.delete_file, name='delete_file'),
  # path('download-file/<str:file_path>/', views.download_file, name='download_file'),
  # path('upload-file/', views.upload_file, name='upload_file'),
  # path('save-info/<str:file_path>/', views.save_info, name='save_info'),

]
