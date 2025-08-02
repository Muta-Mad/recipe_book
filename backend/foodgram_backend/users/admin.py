from django.contrib import admin
from .models import CustomUser, Subscribe


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email')


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
