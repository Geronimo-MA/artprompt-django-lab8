from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'Панель управления ArtPrompt'
admin.site.site_title = 'ArtPrompt Администрирование'
admin.site.index_title = 'Управление арт-промптами и художественными идеями'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('artprompt.urls')),
    path('users/', include('users.urls', namespace='users')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)