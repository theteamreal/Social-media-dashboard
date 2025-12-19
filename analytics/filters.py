from django_filters import rest_framework as filters
from .models import Post, PostMetrics

class PostFilter(filters.FilterSet):
    date_from = filters.DateTimeFilter(field_name='posted_at', lookup_expr='gte')
    date_to = filters.DateTimeFilter(field_name='posted_at', lookup_expr='lte')
    min_likes = filters.NumberFilter(field_name='metrics__likes_count', lookup_expr='gte')
    min_engagement = filters.NumberFilter(field_name='metrics__engagement_rate', lookup_expr='gte')
    
    class Meta:
        model = Post
        fields = ['content_type', 'social_account__platform', 'date_from', 'date_to']

class PostMetricsFilter(filters.FilterSet):
    date_from = filters.DateTimeFilter(field_name='recorded_at', lookup_expr='gte')
    date_to = filters.DateTimeFilter(field_name='recorded_at', lookup_expr='lte')
    
    class Meta:
        model = PostMetrics
        fields = ['post', 'date_from', 'date_to']