from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'birth_date')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')