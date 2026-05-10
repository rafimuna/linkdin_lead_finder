# scraper/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, SearchHistory, ProxyPool

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Django admin panel-এ Profile model কেমন দেখাবে
    """
    
    # লিস্টে কোন ফিল্ড দেখাবে
    list_display = [
        'name', 
        'headline_preview', 
        'location', 
        'category_badge', 
        'confidence_score',
        'scrape_status_badge',
        'created_at'
    ]
    
    # কোন ফিল্ড দিয়ে ফিল্টার করা যাবে
    list_filter = [
        'category', 
        'scrape_status', 
        'is_scraped',
        'created_at'
    ]
    
    # কোন ফিল্ড দিয়ে সার্চ করা যাবে
    search_fields = [
        'name', 
        'headline', 
        'location', 
        'skills',
        'linkedin_url'
    ]
    
    # রিড-ওনলি ফিল্ড
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'linkedin_url_display',
        'skills_formatted'
    ]
    
    # পেজিনেশন
    list_per_page = 25
    
    # ডিফল্ট অর্ডারিং
    ordering = ['-created_at']
    
    # এডিট ফর্মে ফিল্ডের গ্রুপিং
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'headline', 'location', 'about')
        }),
        ('Professional Info', {
            'fields': ('skills', 'experience', 'education')
        }),
        ('LinkedIn Info', {
            'fields': ('linkedin_url', 'linkedin_url_display', 'profile_picture_url')
        }),
        ('AI Classification', {
            'fields': ('category', 'confidence_score')
        }),
        ('Scraping Status', {
            'fields': ('is_scraped', 'scrape_status', 'error_message', 
                      'search_keyword', 'last_scraped_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Collapsible section
        }),
    )
    
    def headline_preview(self, obj):
        """Headline এর প্রথম 50 অক্ষর দেখাবে"""
        if obj.headline:
            return obj.headline[:50] + ('...' if len(obj.headline) > 50 else '')
        return '-'
    headline_preview.short_description = 'Headline'
    
    def category_badge(self, obj):
        """Category টি colored badge হিসেবে দেখাবে"""
        colors = {
            'recruiter': 'red',
            'hr': 'orange',
            'backend_dev': 'green',
            'frontend_dev': 'blue',
            'ceo': 'purple',
            'manager': 'brown',
        }
        color = colors.get(obj.category, 'gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 12px; color: white;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def scrape_status_badge(self, obj):
        """Status হিসেবে colored badge"""
        colors = {
            'pending': 'gray',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red',
            'blocked': 'darkred',
        }
        color = colors.get(obj.scrape_status, 'gray')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; border-radius: 12px; color: white;">{}</span>',
            color,
            obj.get_scrape_status_display()
        )
    scrape_status_badge.short_description = 'Status'
    
    def linkedin_url_display(self, obj):
        """Clickable LinkedIn link"""
        return format_html('<a href="{}" target="_blank">🔗 View Profile</a>', obj.linkedin_url)
    linkedin_url_display.short_description = 'LinkedIn Link'
    
    def skills_formatted(self, obj):
        """Skills গুলো comma separated দেখাবে"""
        skills_list = obj.get_skills_list()
        if skills_list:
            return ', '.join(skills_list)
        return '-'
    skills_formatted.short_description = 'Skills'
    
    # Actions
    actions = ['mark_as_completed', 'mark_as_failed', 'reclassify_profiles']
    
    def mark_as_completed(self, request, queryset):
        """Selected প্রোফাইলগুলো completed হিসেবে mark করবে"""
        updated = queryset.update(scrape_status='completed', is_scraped=True)
        self.message_user(request, f'{updated} profiles marked as completed.')
    mark_as_completed.short_description = "Mark selected as completed"
    
    def mark_as_failed(self, request, queryset):
        """Failed হিসেবে mark করবে"""
        updated = queryset.update(scrape_status='failed')
        self.message_user(request, f'{updated} profiles marked as failed.')
    mark_as_failed.short_description = "Mark selected as failed"
    
    def reclassify_profiles(self, request, queryset):
        """AI দিয়ে reclassify করতে হবে (later implement)"""
        self.message_user(request, 'Reclassification feature coming soon!')
    reclassify_profiles.short_description = "Re-classify with AI"


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'total_results_found', 'profiles_scraped', 
                   'search_duration', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['keyword']
    readonly_fields = ['created_at']


@admin.register(ProxyPool)
class ProxyPoolAdmin(admin.ModelAdmin):
    list_display = ['proxy_url', 'is_active', 'success_count', 'fail_count', 
                   'success_rate', 'last_used']
    list_filter = ['is_active']
    search_fields = ['proxy_url']
    
    def success_rate(self, obj):
        return f"{obj.get_success_rate():.1f}%"
    success_rate.short_description = 'Success Rate'