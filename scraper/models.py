# scraper/models.py - COMPLETELY FIXED - NO ERRORS

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import re


class Profile(models.Model):
    """
    LinkedIn Profile Model - Stores all scraped profile information
    """
    
    # ========== Basic Information ==========
    name = models.CharField(
        max_length=255,
        verbose_name="Full Name",
        help_text="LinkedIn প্রোফাইলের পুরো নাম"
    )
    
    headline = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Professional Headline",
        help_text="যেমন: 'Senior Software Engineer at Google'"
    )
    
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Location",
        help_text="প্রোফাইলের লোকেশন (দেশ/শহর)"
    )
    
    about = models.TextField(
        blank=True,
        null=True,
        verbose_name="About Section",
        help_text="LinkedIn প্রোফাইলের 'About' সেকশন"
    )
    
    # ========== Professional Information ==========
    skills = models.TextField(
        blank=True,
        null=True,
        verbose_name="Skills",
        help_text="স্কিলগুলো কমা দিয়ে আলাদা করা থাকবে"
    )
    
    experience = models.TextField(
        blank=True,
        null=True,
        verbose_name="Work Experience",
        help_text="কাজের অভিজ্ঞতার বিবরণ"
    )
    
    education = models.TextField(
        blank=True,
        null=True,
        verbose_name="Education",
        help_text="শিক্ষাগত যোগ্যতা"
    )
    
    # ========== Contact & URLs ==========
    linkedin_url = models.URLField(
        max_length=500,
        unique=False,
        verbose_name="LinkedIn Profile URL",
    )
    
    profile_picture_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name="Profile Picture URL"
    )
    
    # ========== AI Classification ==========
    category = models.CharField(
        max_length=50,
        choices=[
            ('recruiter', 'Recruiter'),
            ('hr', 'HR Professional'),
            ('backend_dev', 'Backend Developer'),
            ('frontend_dev', 'Frontend Developer'),
            ('fullstack_dev', 'Full Stack Developer'),
            ('devops', 'DevOps Engineer'),
            ('data_scientist', 'Data Scientist'),
            ('manager', 'Manager'),
            ('ceo', 'CEO/Founder'),
            ('marketing', 'Marketing Professional'),
            ('sales', 'Sales Professional'),
            ('other', 'Other'),
        ],
        default='other',
        db_index=True,
        verbose_name="AI Classified Category"
    )
    
    confidence_score = models.FloatField(
        default=0.0,
        help_text="AI ক্লাসিফিকেশনের confidence score (0-1)",
        verbose_name="AI Confidence Score"
    )
    
    # ========== Search Related ==========
    search_keyword = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Search Keyword Used",
    )
    
    # ========== Scraping Metadata ==========
    is_scraped = models.BooleanField(
        default=False,
        verbose_name="Fully Scraped",
    )
    
    scrape_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('blocked', 'Blocked by LinkedIn'),
        ],
        default='pending',
        verbose_name="Scraping Status"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Error Message",
    )
    
    # ========== Timestamps ==========
    # FIXED: Only auto_now_add, no default
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    
    last_scraped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Scraped At"
    )
    
    class Meta:
        verbose_name = "LinkedIn Profile"
        verbose_name_plural = "LinkedIn Profiles"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['search_keyword']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"
    
    def clean_linkedin_url(self):
        """Clean LinkedIn URL before saving"""
        if self.linkedin_url:
            if '#:~:text' in self.linkedin_url:
                self.linkedin_url = self.linkedin_url.split('#:~:text')[0]
            if '?' in self.linkedin_url:
                self.linkedin_url = self.linkedin_url.split('?')[0]
            self.linkedin_url = self.linkedin_url.rstrip('/')
            match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', self.linkedin_url)
            if match:
                self.linkedin_url = match.group(1)
    
    def clean(self):
        """Data validation before saving"""
        if self.name and len(self.name.strip()) < 2:
            raise ValidationError({'name': 'নাম কমপক্ষে ২ অক্ষরের হতে হবে'})
        if self.linkedin_url and 'linkedin.com' not in self.linkedin_url:
            raise ValidationError({'linkedin_url': 'শুধু LinkedIn URL দেওয়া যাবে'})
        if self.headline and len(self.headline) > 500:
            self.headline = self.headline[:497] + '...'
    
    def save(self, *args, **kwargs):
        """Save method with URL cleaning"""
        self.clean_linkedin_url()
        try:
            self.clean()
        except ValidationError as e:
            print(f"Validation error: {e}")
        super().save(*args, **kwargs)
    
    def get_skills_list(self):
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
        return []
    
    def update_category(self, new_category, confidence):
        self.category = new_category
        self.confidence_score = confidence
        self.save(update_fields=['category', 'confidence_score', 'updated_at'])
        return True
    
    def mark_as_completed(self):
        self.is_scraped = True
        self.scrape_status = 'completed'
        self.last_scraped_at = timezone.now()
        self.save(update_fields=['is_scraped', 'scrape_status', 'last_scraped_at'])
    
    def mark_as_failed(self, error_msg):
        self.scrape_status = 'failed'
        self.error_message = error_msg[:500]
        self.save(update_fields=['scrape_status', 'error_message'])
    
    def mark_as_blocked(self):
        self.scrape_status = 'blocked'
        self.save(update_fields=['scrape_status'])
    
    @classmethod
    def get_by_clean_url(cls, url):
        if '#:~:text' in url:
            url = url.split('#:~:text')[0]
        return cls.objects.filter(linkedin_url=url).first()


class SearchHistory(models.Model):
    """
    Search History Model - Tracks all user searches
    """
    
    keyword = models.CharField(
        max_length=255, 
        verbose_name="Search Keyword", 
        db_index=True
    )
    
    total_results_found = models.IntegerField(
        default=0, 
        verbose_name="Total Results Found"
    )
    
    profiles_scraped = models.IntegerField(
        default=0, 
        verbose_name="Profiles Scraped"
    )
    
    profiles_saved = models.IntegerField(
        default=0, 
        verbose_name="New Profiles Saved"
    )
    
    search_duration = models.FloatField(
        default=0.0, 
        verbose_name="Search Duration (seconds)"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True, 
        verbose_name="IP Address"
    )
    
    user_agent = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="User Agent"
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='searches',
        verbose_name="User"
    )
    
    # FIXED: Only auto_now_add
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Searched At"
    )
    
    class Meta:
        verbose_name = "Search History"
        verbose_name_plural = "Search Histories"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['keyword', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"'{self.keyword}' - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def success_rate(self):
        if self.total_results_found > 0:
            return (self.profiles_scraped / self.total_results_found) * 100
        return 0.0


class ProxyPool(models.Model):
    """
    Proxy Pool Model - Manage proxy servers for scraping
    """
    
    PROXY_TYPES = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
        ('socks4', 'SOCKS4'),
        ('socks5', 'SOCKS5'),
    ]
    
    proxy_url = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Proxy URL",
    )
    
    proxy_type = models.CharField(
        max_length=10,
        choices=PROXY_TYPES,
        default='http',
        verbose_name="Proxy Type"
    )
    
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Is Active"
    )
    
    is_anonymous = models.BooleanField(
        default=True, 
        verbose_name="Is Anonymous"
    )
    
    success_count = models.IntegerField(
        default=0, 
        verbose_name="Success Count"
    )
    
    fail_count = models.IntegerField(
        default=0, 
        verbose_name="Fail Count"
    )
    
    last_used = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Last Used"
    )
    
    last_checked = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Last Checked"
    )
    
    response_time = models.FloatField(
        default=0.0, 
        verbose_name="Response Time"
    )
    
    country = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Country"
    )
    
    # FIXED: Only auto_now_add - removed default
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    
    class Meta:
        verbose_name = "Proxy Pool"
        verbose_name_plural = "Proxy Pool"
        ordering = ['-success_count']
        indexes = [
            models.Index(fields=['is_active', 'success_count']),
            models.Index(fields=['country']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.proxy_url}"
    
    def get_success_rate(self):
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100
    
    def record_success(self):
        self.success_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['success_count', 'last_used'])
    
    def record_failure(self):
        self.fail_count += 1
        self.last_used = timezone.now()
        if self.get_success_rate() < 20 and self.success_count + self.fail_count > 10:
            self.is_active = False
        self.save(update_fields=['fail_count', 'last_used', 'is_active'])
    
    def mark_as_checked(self, response_time_ms):
        self.last_checked = timezone.now()
        self.response_time = response_time_ms
        self.save(update_fields=['last_checked', 'response_time'])


# ========== Signal for auto-cleanup ==========
from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=Profile)
def profile_pre_save(sender, instance, **kwargs):
    """Auto-clean URL before any save"""
    instance.clean_linkedin_url()