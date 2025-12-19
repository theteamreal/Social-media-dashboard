from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SocialMediaAccount

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'organization', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'organization']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'organization', 'profile_image', 'is_verified')}),
    )

@admin.register(SocialMediaAccount)
class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'account_username', 'is_active', 'connected_at']
    list_filter = ['platform', 'is_active']
    search_fields = ['account_username', 'user__username']
    date_hierarchy = 'connected_at'