from django.contrib.admin.apps import AdminConfig

class DolAdminConfig(AdminConfig):
    default_site = "config.admin_site.DolSystemAdminSite"
