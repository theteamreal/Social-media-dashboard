from django.db import models
from accounts.models import User, SocialMediaAccount

class Post(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('reel', 'Reel'),
        ('carousel', 'Carousel'),
        ('static', 'Static Post'),
        ('story', 'Story'),
        ('video', 'Video'),
    ]
    
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='posts')
    post_id = models.CharField(max_length=255, unique=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    caption = models.TextField(blank=True, null=True)
    media_url = models.URLField(max_length=1000, blank=True, null=True)
    thumbnail_url = models.URLField(max_length=1000, blank=True, null=True)
    posted_at = models.DateTimeField()
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['social_account', 'posted_at']),
            models.Index(fields=['content_type', 'posted_at']),
        ]

class PostMetrics(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='metrics')
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    saves_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    reach = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['post', 'recorded_at']),
        ]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    text = models.TextField()
    likes_count = models.IntegerField(default=0)
    replied_to = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    posted_at = models.DateTimeField()
    sentiment_score = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-posted_at']

class Hashtag(models.Model):
    tag = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PostHashtag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_hashtags')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='post_hashtags')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'hashtag']

class Audience(models.Model):
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='audience')
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    age_range_13_17 = models.FloatField(default=0.0)
    age_range_18_24 = models.FloatField(default=0.0)
    age_range_25_34 = models.FloatField(default=0.0)
    age_range_35_44 = models.FloatField(default=0.0)
    age_range_45_54 = models.FloatField(default=0.0)
    age_range_55_plus = models.FloatField(default=0.0)
    gender_male = models.FloatField(default=0.0)
    gender_female = models.FloatField(default=0.0)
    gender_other = models.FloatField(default=0.0)
    top_countries = models.JSONField(default=dict)
    top_cities = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']

class EngagementPattern(models.Model):
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='engagement_patterns')
    hour_of_day = models.IntegerField()
    day_of_week = models.IntegerField()
    avg_engagement_rate = models.FloatField(default=0.0)
    avg_likes = models.FloatField(default=0.0)
    avg_comments = models.FloatField(default=0.0)
    avg_shares = models.FloatField(default=0.0)
    post_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['social_account', 'hour_of_day', 'day_of_week']

class AIInsight(models.Model):
    INSIGHT_TYPE_CHOICES = [
        ('content_performance', 'Content Performance'),
        ('audience_behavior', 'Audience Behavior'),
        ('optimal_timing', 'Optimal Timing'),
        ('trend_analysis', 'Trend Analysis'),
        ('competitor_analysis', 'Competitor Analysis'),
        ('recommendation', 'Recommendation'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insights')
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='insights', blank=True, null=True)
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    data = models.JSONField(default=dict)
    priority = models.IntegerField(default=0)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']

class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')
    query_text = models.TextField()
    response = models.TextField(blank=True, null=True)
    response_data = models.JSONField(default=dict)
    execution_time = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('performance', 'Performance Report'),
        ('engagement', 'Engagement Report'),
        ('audience', 'Audience Report'),
        ('content', 'Content Analysis Report'),
        ('comparative', 'Comparative Report'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    filters = models.JSONField(default=dict)
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']

class Competitor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competitors')
    platform = models.CharField(max_length=20)
    account_username = models.CharField(max_length=255)
    account_id = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'platform', 'account_id']

class CompetitorMetrics(models.Model):
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name='metrics')
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)
    avg_engagement_rate = models.FloatField(default=0.0)
    avg_likes = models.FloatField(default=0.0)
    avg_comments = models.FloatField(default=0.0)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']

class ContentStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    social_account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE, related_name='strategies')
    title = models.CharField(max_length=255)
    description = models.TextField()
    recommendations = models.JSONField(default=list)
    optimal_times = models.JSONField(default=list)
    content_mix = models.JSONField(default=dict)
    hashtag_strategy = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)