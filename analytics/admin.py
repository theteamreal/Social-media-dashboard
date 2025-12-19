from django.contrib import admin
from .models import *

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['post_id', 'social_account', 'content_type', 'posted_at']
    list_filter = ['content_type', 'social_account__platform', 'posted_at']
    search_fields = ['post_id', 'caption']
    date_hierarchy = 'posted_at'

@admin.register(PostMetrics)
class PostMetricsAdmin(admin.ModelAdmin):
    list_display = ['post', 'likes_count', 'comments_count', 'engagement_rate', 'recorded_at']
    list_filter = ['recorded_at']
    date_hierarchy = 'recorded_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['comment_id', 'username', 'post', 'sentiment_score', 'posted_at']
    list_filter = ['posted_at']
    search_fields = ['username', 'text']

@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ['tag', 'created_at']
    search_fields = ['tag']

@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):
    list_display = ['social_account', 'followers_count', 'following_count', 'recorded_at']
    list_filter = ['social_account__platform', 'recorded_at']
    date_hierarchy = 'recorded_at'

@admin.register(EngagementPattern)
class EngagementPatternAdmin(admin.ModelAdmin):
    list_display = ['social_account', 'hour_of_day', 'day_of_week', 'avg_engagement_rate']
    list_filter = ['day_of_week', 'social_account__platform']

@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight_type', 'title', 'priority', 'is_read', 'created_at']
    list_filter = ['insight_type', 'is_read', 'priority']
    search_fields = ['title', 'description']

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query_text', 'execution_time', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query_text']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_type', 'title', 'format', 'status', 'created_at']
    list_filter = ['report_type', 'format', 'status']
    search_fields = ['title']

@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'account_username', 'is_active', 'added_at']
    list_filter = ['platform', 'is_active']
    search_fields = ['account_username']

@admin.register(CompetitorMetrics)
class CompetitorMetricsAdmin(admin.ModelAdmin):
    list_display = ['competitor', 'followers_count', 'avg_engagement_rate', 'recorded_at']
    list_filter = ['recorded_at']
    date_hierarchy = 'recorded_at'

@admin.register(ContentStrategy)
class ContentStrategyAdmin(admin.ModelAdmin):
    list_display = ['user', 'social_account', 'title', 'is_active', 'created_at']
    list_filter = ['is_active', 'social_account__platform']
    search_fields = ['title', 'description']