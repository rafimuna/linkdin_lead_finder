from django.db import models
from django.contrib.auth.models import User
from scraper.models import Profile

class ExportHistory(models.Model):
    """
    Track all export activities
    """
    EXPORT_FORMATS = (
        ('csv', 'CSV Format'),
        ('excel', 'Excel Format'),
        ('pdf', 'PDF Format'),
    )
    
    EXPORT_TYPES = (
        ('all', 'All Profiles'),
        ('filtered', 'Filtered Profiles'),
        ('single', 'Single Profile'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPES, default='all')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    record_count = models.IntegerField(default=0)
    filters_used = models.JSONField(default=dict, blank=True, help_text="Filters applied during export")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Export History'
        verbose_name_plural = 'Export Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.export_format.upper()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"