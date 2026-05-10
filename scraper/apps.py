# scraper/apps.py

from django.apps import AppConfig

class ScraperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scraper'
    verbose_name = 'LinkedIn Scraper'
    
    def ready(self):
        """App ready হলে signal connect করবে (later use করব)"""
        # import scraper.signals  # later
        pass