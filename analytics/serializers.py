from rest_framework import serializers
from .models import *
from accounts.models import SocialMediaAccount

class SocialMediaAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaAccount
        fields = ['id', 'platform', 'account_username', 'account_id', 'is_active', 'connected_at', 'last_synced']
        read_only_fields = ['id', 'connected_at', 'last_synced']

class PostSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source='social_account.platform', read_only=True)
    account_username = serializers.CharField(source='social_account.account_username', read_only=True)
    latest_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'post_id', 'platform', 'account_username', 'content_type', 'caption', 
                  'media_url', 'thumbnail_url', 'posted_at', 'latest_metrics', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_latest_metrics(self, obj):
        latest = obj.metrics.first()
        if latest:
            return PostMetricsSerializer(latest).data
        return None

class PostMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMetrics
        fields = ['id', 'likes_count', 'comments_count', 'shares_count', 'saves_count', 
                  'views_count', 'reach', 'impressions', 'engagement_rate', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'comment_id', 'username', 'text', 'likes_count', 'sentiment_score', 'posted_at']
        read_only_fields = ['id']

class HashtagSerializer(serializers.ModelSerializer):
    usage_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Hashtag
        fields = ['id', 'tag', 'usage_count', 'created_at']
        read_only_fields = ['id', 'created_at']

class AudienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audience
        fields = ['id', 'followers_count', 'following_count', 'age_range_13_17', 'age_range_18_24', 
                  'age_range_25_34', 'age_range_35_44', 'age_range_45_54', 'age_range_55_plus',
                  'gender_male', 'gender_female', 'gender_other', 'top_countries', 'top_cities', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']

class EngagementPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngagementPattern
        fields = ['id', 'hour_of_day', 'day_of_week', 'avg_engagement_rate', 'avg_likes', 
                  'avg_comments', 'avg_shares', 'post_count', 'updated_at']
        read_only_fields = ['id']

class AIInsightSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source='social_account.platform', read_only=True)
    
    class Meta:
        model = AIInsight
        fields = ['id', 'platform', 'insight_type', 'title', 'description', 'data', 
                  'priority', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']

class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = ['id', 'query_text', 'response', 'response_data', 'execution_time', 'created_at']
        read_only_fields = ['id', 'response', 'response_data', 'execution_time', 'created_at']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'report_type', 'title', 'description', 'format', 'filters', 
                  'file', 'status', 'created_at', 'completed_at']
        read_only_fields = ['id', 'file', 'status', 'created_at', 'completed_at']

class CompetitorSerializer(serializers.ModelSerializer):
    latest_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = Competitor
        fields = ['id', 'platform', 'account_username', 'account_id', 'is_active', 
                  'latest_metrics', 'added_at']
        read_only_fields = ['id', 'added_at']
    
    def get_latest_metrics(self, obj):
        latest = obj.metrics.first()
        if latest:
            return CompetitorMetricsSerializer(latest).data
        return None

class CompetitorMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitorMetrics
        fields = ['id', 'followers_count', 'following_count', 'posts_count', 'avg_engagement_rate',
                  'avg_likes', 'avg_comments', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']

class ContentStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentStrategy
        fields = ['id', 'title', 'description', 'recommendations', 'optimal_times', 
                  'content_mix', 'hashtag_strategy', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']