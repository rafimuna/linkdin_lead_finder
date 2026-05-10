# scraper/models.py

from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re

class Profile(models.Model):
    """
    LinkedIn Profile Model - এখানে সকল স্ক্র্যাপ করা প্রোফাইলের তথ্য সংরক্ষণ করা হবে
    
    Why this model?
    - Database এ তথ্য সংরক্ষণের জন্য Django ORM ব্যবহার করব
    - প্রতিটি ফিল্ড specific ডাটা টাইপের জন্য তৈরি করা হয়েছে
    - Indexing দিয়ে সার্চ দ্রুত করা হয়েছে
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
        unique=True,  # Duplicate প্রোফাইল রুখতে unique constraint
        max_length=500,
        verbose_name="LinkedIn Profile URL",
        validators=[URLValidator()]
    )
    
    profile_picture_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name="Profile Picture URL"
    )
    
    # ========== AI Classification ==========
    # এগুলো AI দ্বারা ক্লাসিফাই করা হবে
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
        db_index=True,  # Index for faster filtering
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
        db_index=True,  # গুরুত্বপূর্ণ: keyword দিয়ে সার্চ দ্রুত হবে
        verbose_name="Search Keyword Used",
        help_text="কোন keyword দিয়ে প্রোফাইলটি পাওয়া গেছে"
    )
    
    # ========== Scraping Metadata ==========
    is_scraped = models.BooleanField(
        default=False,
        verbose_name="Fully Scraped",
        help_text="সম্পূর্ণ প্রোফাইলের তথ্য নেয়া হয়েছে কিনা"
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
        help_text="স্ক্র্যাপিং-এ error হলে এখানে সংরক্ষণ হবে"
    )
    
    # ========== Timestamps ==========
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
    
    # ========== Meta Class ==========
    class Meta:
        verbose_name = "LinkedIn Profile"
        verbose_name_plural = "LinkedIn Profiles"
        ordering = ['-created_at']  # নতুনগুলো আগে দেখাবে
        indexes = [
            models.Index(fields=['category', 'created_at']),  # Combined index
            models.Index(fields=['search_keyword']),
            models.Index(fields=['location']),
        ]
    
    # ========== String Representation ==========
    def __str__(self):
        """Django admin এবং shell-এ কী দেখাবে"""
        return f"{self.name} - {self.get_category_display()}"
    
    # ========== Custom Methods ==========
    
    def get_skills_list(self):
        """স্কিলগুলো লিস্ট আকারে রিটার্ন করবে"""
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',')]
        return []
    
    def update_category(self, new_category, confidence):
        """AI ক্লাসিফিকেশন আপডেট করার জন্য মেথড"""
        self.category = new_category
        self.confidence_score = confidence
        self.save(update_fields=['category', 'confidence_score', 'updated_at'])
        return True
    
    def mark_as_completed(self):
        """স্ক্র্যাপিং সম্পূর্ণ হলে কল করবেন"""
        self.is_scraped = True
        self.scrape_status = 'completed'
        self.last_scraped_at = timezone.now()
        self.save(update_fields=['is_scraped', 'scrape_status', 'last_scraped_at'])
    
    def mark_as_failed(self, error_msg):
        """স্ক্র্যাপিং fail হলে কল করবেন"""
        self.scrape_status = 'failed'
        self.error_message = error_msg
        self.save(update_fields=['scrape_status', 'error_message'])
    
    def clean(self):
        """ডাটা সেভ হওয়ার আগে validation"""
        super().clean()
        
        # নাম যেন খালি না হয়
        if self.name and len(self.name.strip()) < 2:
            raise ValidationError({'name': 'নাম কমপক্ষে ২ অক্ষরের হতে হবে'})
        
        # URL valid কিনা চেক করা (already URLValidator আছে)
        if self.linkedin_url and 'linkedin.com' not in self.linkedin_url:
            raise ValidationError({'linkedin_url': 'শুধু LinkedIn URL দেওয়া যাবে'})
    
    def save(self, *args, **kwargs):
        """সেভ করার আগে clean() কল করবে"""
        self.full_clean()  # Calls clean() method
        super().save(*args, **kwargs)


class SearchHistory(models.Model):
    """
    প্রতিটি সার্চের ইতিহাস রাখার জন্য Model
    
    কেন দরকার?
    - ইউজার কোন keyword দিয়ে সার্চ করেছে তার রেকর্ড রাখা
    - কতটি প্রোফাইল পাওয়া গেছে তার统计
    - Duplicate সার্চ রুখতে
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
    
    search_duration = models.FloatField(
        default=0.0,
        help_text="সার্চ করতে কত সেকেন্ড লেগেছে",
        verbose_name="Search Duration (seconds)"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="IP Address"
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='searches',
        verbose_name="User"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Searched At"
    )
    
    class Meta:
        verbose_name = "Search History"
        verbose_name_plural = "Search Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"'{self.keyword}' - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ProxyPool(models.Model):
    """
    Proxy সার্ভারগুলো ম্যানেজ করার জন্য Model
    
    LinkedIn scraping-এ IP block এড়ানোর জন্য proxy ব্যবহার করা হয়
    """
    
    proxy_url = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Proxy URL",
        help_text="যেমন: http://user:pass@123.45.67.89:8080"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
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
    
    response_time = models.FloatField(
        default=0.0,
        help_text="Average response time in seconds",
        verbose_name="Response Time"
    )
    
    class Meta:
        verbose_name = "Proxy Pool"
        verbose_name_plural = "Proxy Pool"
    
    def __str__(self):
        return self.proxy_url
    
    def get_success_rate(self):
        """Success rate calculate করা"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100