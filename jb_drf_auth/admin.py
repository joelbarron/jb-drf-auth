"""Reusable admin classes for jb-drf-auth.

Integrators register their concrete models against these admin classes:

    from django.contrib import admin
    from jb_drf_auth import admin as auth_admin
    from .models import User, Profile, Device, OtpCode, SmsLog, EmailLog

    admin.site.register(User, auth_admin.UserAdmin)
    admin.site.register(Profile, auth_admin.ProfileAdmin)
    admin.site.register(Device, auth_admin.DeviceAdmin)
    admin.site.register(OtpCode, auth_admin.OtpCodeAdmin)
    admin.site.register(SmsLog, auth_admin.SmsLogAdmin)
    admin.site.register(EmailLog, auth_admin.EmailLogAdmin)

To add project-specific columns, subclass the base admin:

    class FinzenioUserAdmin(auth_admin.UserAdmin):
        list_display = auth_admin.UserAdmin.list_display + ("stripe_customer_id",)

    admin.site.register(User, FinzenioUserAdmin)
"""

from django.contrib import admin


class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "username", "is_active", "is_verified", "is_staff")
    search_fields = ("email", "username", "phone")
    list_filter = ("is_active", "is_verified", "is_staff", "is_superuser")
    ordering = ("-id",)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "is_default", "is_active")
    search_fields = ("user__email", "first_name", "last_name")
    list_filter = ("role", "is_default", "is_active")
    ordering = ("-id",)


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "platform", "name", "linked_at")
    search_fields = ("user__email", "platform", "name", "token")
    list_filter = ("platform",)
    ordering = ("-id",)


class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone", "channel", "is_used", "valid_until")
    search_fields = ("email", "phone", "code")
    list_filter = ("channel", "is_used")
    ordering = ("-id",)


class SmsLogAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "provider", "status", "created")
    search_fields = ("phone", "provider", "message")
    list_filter = ("status", "provider")
    ordering = ("-id",)


class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("id", "to_email", "subject", "provider", "status", "created")
    search_fields = ("to_email", "subject")
    list_filter = ("status", "provider")
    ordering = ("-id",)


__all__ = [
    "UserAdmin",
    "ProfileAdmin",
    "DeviceAdmin",
    "OtpCodeAdmin",
    "SmsLogAdmin",
    "EmailLogAdmin",
]
