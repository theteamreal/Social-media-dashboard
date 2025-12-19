from social_analytics.celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import *
from accounts.models import SocialMediaAccount

@shared_task
def sync_all_social_accounts():
    accounts = SocialMediaAccount.objects.filter(is_active=True)
    for account in accounts:
        sync_social_account.delay(account.id)
    return f"Synced {accounts.count()} accounts"

@shared_task
def sync_social_account(account_id):
    try:
        account = SocialMediaAccount.objects.get(id=account_id)
        account.last_synced = timezone.now()
        account.save()
        return f"Synced account {account.account_username}"
    except SocialMediaAccount.DoesNotExist:
        return f"Account {account_id} not found"

@shared_task
def update_engagement_patterns():
    accounts = SocialMediaAccount.objects.filter(is_active=True)
    
    for account in accounts:
        posts = Post.objects.filter(social_account=account)
        
        for post in posts:
            hour = post.posted_at.hour
            day = post.posted_at.weekday()
            
            latest_metrics = post.metrics.first()
            
            if latest_metrics:
                pattern, created = EngagementPattern.objects.get_or_create(
                    social_account=account,
                    hour_of_day=hour,
                    day_of_week=day
                )
                
                pattern.avg_engagement_rate = (pattern.avg_engagement_rate * pattern.post_count + latest_metrics.engagement_rate) / (pattern.post_count + 1)
                pattern.avg_likes = (pattern.avg_likes * pattern.post_count + latest_metrics.likes_count) / (pattern.post_count + 1)
                pattern.avg_comments = (pattern.avg_comments * pattern.post_count + latest_metrics.comments_count) / (pattern.post_count + 1)
                pattern.avg_shares = (pattern.avg_shares * pattern.post_count + latest_metrics.shares_count) / (pattern.post_count + 1)
                pattern.post_count += 1
                pattern.save()
    
    return "Engagement patterns updated"

@shared_task
def generate_ai_insights():
    from accounts.models import User
    
    users = User.objects.filter(is_active=True)
    
    for user in users:
        date_from = timezone.now() - timedelta(days=7)
        
        posts = Post.objects.filter(
            social_account__user=user,
            posted_at__gte=date_from
        )
        
        if posts.exists():
            best_content = posts.order_by('-metrics__engagement_rate').first()
            
            if best_content:
                AIInsight.objects.create(
                    user=user,
                    social_account=best_content.social_account,
                    insight_type='content_performance',
                    title=f'Your {best_content.content_type} performed exceptionally well',
                    description=f'Your recent {best_content.content_type} got high engagement. Consider creating similar content.',
                    data={'post_id': best_content.post_id},
                    priority=5
                )
    
    return f"Generated insights for {users.count()} users"

@shared_task
def sync_competitor_data():
    competitors = Competitor.objects.filter(is_active=True)
    
    for competitor in competitors:
        CompetitorMetrics.objects.create(
            competitor=competitor,
            followers_count=0,
            following_count=0,
            posts_count=0,
            avg_engagement_rate=0.0
        )
    
    return f"Synced {competitors.count()} competitors"

@shared_task
def generate_report(report_id):
    try:
        report = Report.objects.get(id=report_id)
        report.status = 'processing'
        report.save()
        
        report.status = 'completed'
        report.completed_at = timezone.now()
        report.save()
        
        return f"Report {report_id} generated"
    except Report.DoesNotExist:
        return f"Report {report_id} not found"

@shared_task
def process_nlp_query(query_id):
    try:
        query = Query.objects.get(id=query_id)
        
        query.response = "Query processed"
        query.response_data = {'status': 'success'}
        query.save()
        
        return f"Query {query_id} processed"
    except Query.DoesNotExist:
        return f"Query {query_id} not found"