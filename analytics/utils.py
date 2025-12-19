from django.db.models import Avg, Sum, Count
from datetime import timedelta
from django.utils import timezone

def calculate_engagement_rate(likes, comments, shares, followers):
    if followers == 0:
        return 0.0
    total_engagement = likes + comments + shares
    return (total_engagement / followers) * 100

def get_trending_hashtags(user, days=30):
    from .models import Hashtag, Post
    
    date_from = timezone.now() - timedelta(days=days)
    
    trending = Hashtag.objects.filter(
        post_hashtags__post__social_account__user=user,
        post_hashtags__post__posted_at__gte=date_from
    ).annotate(
        usage_count=Count('post_hashtags'),
        avg_engagement=Avg('post_hashtags__post__metrics__engagement_rate')
    ).order_by('-usage_count', '-avg_engagement')[:20]
    
    return trending

def get_optimal_posting_times(social_account):
    from .models import EngagementPattern
    
    patterns = EngagementPattern.objects.filter(
        social_account=social_account
    ).order_by('-avg_engagement_rate')[:7]
    
    return patterns

def analyze_content_performance(user, days=30):
    from .models import Post
    
    date_from = timezone.now() - timedelta(days=days)
    
    performance = Post.objects.filter(
        social_account__user=user,
        posted_at__gte=date_from
    ).values('content_type').annotate(
        total_posts=Count('id'),
        avg_engagement=Avg('metrics__engagement_rate'),
        avg_likes=Avg('metrics__likes_count'),
        avg_comments=Avg('metrics__comments_count')
    ).order_by('-avg_engagement')
    
    return performance

def generate_content_recommendations(social_account):
    from .models import Post
    
    best_posts = Post.objects.filter(
        social_account=social_account
    ).order_by('-metrics__engagement_rate')[:10]
    
    content_types = {}
    for post in best_posts:
        if post.content_type not in content_types:
            content_types[post.content_type] = 0
        content_types[post.content_type] += 1
    
    recommendations = []
    for content_type, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
        recommendations.append({
            'content_type': content_type,
            'frequency': count,
            'suggestion': f'Post more {content_type} content'
        })
    
    return recommendations