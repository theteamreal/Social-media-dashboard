from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Sum, Count, Q, F, Max, Min
from django.utils import timezone
from datetime import timedelta
from .models import *
from .serializers import *
from accounts.models import SocialMediaAccount

class SocialMediaAccountViewSet(viewsets.ModelViewSet):
    serializer_class = SocialMediaAccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['platform', 'is_active']
    search_fields = ['account_username']
    
    def get_queryset(self):
        return SocialMediaAccount.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        account = self.get_object()
        return Response({'status': 'sync initiated', 'account_id': account.id})
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        accounts = self.get_queryset()
        overview_data = []
        
        for account in accounts:
            latest_audience = account.audience.order_by('-recorded_at').first()
            posts_count = account.posts.count()
            
            total_metrics = PostMetrics.objects.filter(
                post__social_account=account
            ).aggregate(
                total_likes=Sum('likes_count'),
                total_comments=Sum('comments_count'),
                total_shares=Sum('shares_count'),
                avg_engagement=Avg('engagement_rate')
            )
            
            overview_data.append({
                'account_id': account.id,
                'platform': account.platform,
                'username': account.account_username,
                'followers': latest_audience.followers_count if latest_audience else 0,
                'posts_count': posts_count,
                'total_likes': total_metrics['total_likes'] or 0,
                'total_comments': total_metrics['total_comments'] or 0,
                'total_shares': total_metrics['total_shares'] or 0,
                'avg_engagement_rate': total_metrics['avg_engagement'] or 0,
            })
        
        return Response(overview_data)

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['content_type', 'social_account__platform', 'social_account']
    search_fields = ['caption', 'post_id']
    ordering_fields = ['posted_at', 'metrics__engagement_rate', 'metrics__likes_count']
    ordering = ['-posted_at']
    
    def get_queryset(self):
        return Post.objects.filter(social_account__user=self.request.user).select_related('social_account').prefetch_related('metrics')
    
    @action(detail=False, methods=['get'])
    def top_performing(self, request):
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        content_type = request.query_params.get('content_type')
        platform = request.query_params.get('platform')
        
        date_from = timezone.now() - timedelta(days=days)
        queryset = self.get_queryset().filter(posted_at__gte=date_from)
        
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        if platform:
            queryset = queryset.filter(social_account__platform=platform)
        
        posts_with_metrics = []
        for post in queryset:
            latest_metric = post.metrics.first()
            if latest_metric:
                posts_with_metrics.append({
                    'post': post,
                    'engagement_rate': latest_metric.engagement_rate
                })
        
        posts_with_metrics.sort(key=lambda x: x['engagement_rate'], reverse=True)
        top_posts = [item['post'] for item in posts_with_metrics[:limit]]
        
        serializer = self.get_serializer(top_posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def content_comparison(self, request):
        days = int(request.query_params.get('days', 30))
        platform = request.query_params.get('platform')
        date_from = timezone.now() - timedelta(days=days)
        
        queryset = Post.objects.filter(
            social_account__user=request.user,
            posted_at__gte=date_from
        )
        
        if platform:
            queryset = queryset.filter(social_account__platform=platform)
        
        comparison = queryset.values('content_type').annotate(
            total_posts=Count('id'),
            avg_engagement=Avg('metrics__engagement_rate'),
            avg_likes=Avg('metrics__likes_count'),
            avg_comments=Avg('metrics__comments_count'),
            avg_shares=Avg('metrics__shares_count'),
            avg_reach=Avg('metrics__reach'),
            avg_views=Avg('metrics__views_count'),
            total_likes=Sum('metrics__likes_count'),
            total_comments=Sum('metrics__comments_count'),
            total_shares=Sum('metrics__shares_count')
        ).order_by('-avg_engagement')
        
        return Response(list(comparison))
    
    @action(detail=False, methods=['get'])
    def timeline_analytics(self, request):
        days = int(request.query_params.get('days', 30))
        platform = request.query_params.get('platform')
        date_from = timezone.now() - timedelta(days=days)
        
        queryset = Post.objects.filter(
            social_account__user=request.user,
            posted_at__gte=date_from
        )
        
        if platform:
            queryset = queryset.filter(social_account__platform=platform)
        
        timeline_data = []
        current_date = date_from
        
        while current_date <= timezone.now():
            day_posts = queryset.filter(
                posted_at__date=current_date.date()
            )
            
            day_metrics = PostMetrics.objects.filter(
                post__in=day_posts
            ).aggregate(
                total_likes=Sum('likes_count'),
                total_comments=Sum('comments_count'),
                total_shares=Sum('shares_count'),
                total_reach=Sum('reach'),
                avg_engagement=Avg('engagement_rate'),
                posts_count=Count('post', distinct=True)
            )
            
            timeline_data.append({
                'date': current_date.date().isoformat(),
                'posts_count': day_metrics['posts_count'] or 0,
                'total_likes': day_metrics['total_likes'] or 0,
                'total_comments': day_metrics['total_comments'] or 0,
                'total_shares': day_metrics['total_shares'] or 0,
                'total_reach': day_metrics['total_reach'] or 0,
                'avg_engagement_rate': day_metrics['avg_engagement'] or 0,
            })
            
            current_date += timedelta(days=1)
        
        return Response(timeline_data)
    
    @action(detail=True, methods=['get'])
    def detailed_analytics(self, request, pk=None):
        post = self.get_object()
        
        all_metrics = post.metrics.all().order_by('-recorded_at')
        
        comments = post.comments.all()
        
        sentiment_data = comments.aggregate(
            avg_sentiment=Avg('sentiment_score'),
            positive_count=Count('id', filter=Q(sentiment_score__gte=0.5)),
            neutral_count=Count('id', filter=Q(sentiment_score__gt=-0.5, sentiment_score__lt=0.5)),
            negative_count=Count('id', filter=Q(sentiment_score__lte=-0.5))
        )
        
        hashtags = [ph.hashtag.tag for ph in post.post_hashtags.all()]
        
        metrics_history = PostMetricsSerializer(all_metrics, many=True).data
        
        return Response({
            'post': PostSerializer(post).data,
            'metrics_history': metrics_history,
            'comments_count': comments.count(),
            'sentiment_analysis': sentiment_data,
            'hashtags': hashtags
        })

class PostMetricsViewSet(viewsets.ModelViewSet):
    serializer_class = PostMetricsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post']
    
    def get_queryset(self):
        return PostMetrics.objects.filter(post__social_account__user=self.request.user)

class CommentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['post']
    search_fields = ['text', 'username']
    
    def get_queryset(self):
        return Comment.objects.filter(post__social_account__user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def sentiment_analysis(self, request):
        post_id = request.query_params.get('post_id')
        days = int(request.query_params.get('days', 30))
        
        queryset = self.get_queryset()
        
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        else:
            date_from = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(posted_at__gte=date_from)
        
        sentiment_data = queryset.aggregate(
            avg_sentiment=Avg('sentiment_score'),
            positive_count=Count('id', filter=Q(sentiment_score__gte=0.5)),
            neutral_count=Count('id', filter=Q(sentiment_score__gt=-0.5, sentiment_score__lt=0.5)),
            negative_count=Count('id', filter=Q(sentiment_score__lte=-0.5)),
            total_comments=Count('id')
        )
        
        return Response(sentiment_data)
    
    @action(detail=False, methods=['get'])
    def top_commenters(self, request):
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 10))
        date_from = timezone.now() - timedelta(days=days)
        
        top_commenters = self.get_queryset().filter(
            posted_at__gte=date_from
        ).values('username').annotate(
            comment_count=Count('id'),
            avg_sentiment=Avg('sentiment_score')
        ).order_by('-comment_count')[:limit]
        
        return Response(list(top_commenters))

class HashtagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HashtagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['tag']
    
    def get_queryset(self):
        return Hashtag.objects.filter(
            post_hashtags__post__social_account__user=self.request.user
        ).annotate(usage_count=Count('post_hashtags')).distinct()
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        days = int(request.query_params.get('days', 30))
        limit = int(request.query_params.get('limit', 20))
        date_from = timezone.now() - timedelta(days=days)
        
        trending = Hashtag.objects.filter(
            post_hashtags__post__social_account__user=request.user,
            post_hashtags__post__posted_at__gte=date_from
        ).annotate(
            usage_count=Count('post_hashtags'),
            avg_engagement=Avg('post_hashtags__post__metrics__engagement_rate'),
            total_likes=Sum('post_hashtags__post__metrics__likes_count')
        ).order_by('-usage_count', '-avg_engagement')[:limit]
        
        result = []
        for hashtag in trending:
            result.append({
                'id': hashtag.id,
                'tag': hashtag.tag,
                'usage_count': hashtag.usage_count,
                'avg_engagement': hashtag.avg_engagement or 0,
                'total_likes': hashtag.total_likes or 0
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        hashtag_id = request.query_params.get('hashtag_id')
        
        if not hashtag_id:
            return Response({'error': 'hashtag_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        hashtag = Hashtag.objects.get(id=hashtag_id)
        
        posts_with_hashtag = Post.objects.filter(
            post_hashtags__hashtag=hashtag,
            social_account__user=request.user
        )
        
        performance = posts_with_hashtag.aggregate(
            total_posts=Count('id'),
            avg_engagement=Avg('metrics__engagement_rate'),
            avg_likes=Avg('metrics__likes_count'),
            avg_comments=Avg('metrics__comments_count'),
            avg_reach=Avg('metrics__reach'),
            max_engagement=Max('metrics__engagement_rate')
        )
        
        return Response({
            'hashtag': hashtag.tag,
            'performance': performance
        })

class AudienceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AudienceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['social_account']
    
    def get_queryset(self):
        return Audience.objects.filter(social_account__user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def demographics(self, request):
        account_id = request.query_params.get('account_id')
        
        queryset = self.get_queryset()
        if account_id:
            queryset = queryset.filter(social_account_id=account_id)
        
        latest_audience = queryset.order_by('-recorded_at').first()
        
        if not latest_audience:
            return Response({'error': 'No audience data found'}, status=status.HTTP_404_NOT_FOUND)
        
        demographics = {
            'age_distribution': {
                '13-17': latest_audience.age_range_13_17,
                '18-24': latest_audience.age_range_18_24,
                '25-34': latest_audience.age_range_25_34,
                '35-44': latest_audience.age_range_35_44,
                '45-54': latest_audience.age_range_45_54,
                '55+': latest_audience.age_range_55_plus,
            },
            'gender_distribution': {
                'male': latest_audience.gender_male,
                'female': latest_audience.gender_female,
                'other': latest_audience.gender_other,
            },
            'top_countries': latest_audience.top_countries,
            'top_cities': latest_audience.top_cities,
            'followers_count': latest_audience.followers_count,
            'following_count': latest_audience.following_count,
            'recorded_at': latest_audience.recorded_at
        }
        
        return Response(demographics)
    
    @action(detail=False, methods=['get'])
    def growth_trend(self, request):
        account_id = request.query_params.get('account_id')
        days = int(request.query_params.get('days', 90))
        
        queryset = self.get_queryset()
        if account_id:
            queryset = queryset.filter(social_account_id=account_id)
        
        date_from = timezone.now() - timedelta(days=days)
        audience_history = queryset.filter(
            recorded_at__gte=date_from
        ).order_by('recorded_at')
        
        growth_data = []
        for audience in audience_history:
            growth_data.append({
                'date': audience.recorded_at.date().isoformat(),
                'followers': audience.followers_count,
                'following': audience.following_count
            })
        
        return Response(growth_data)

class EngagementPatternViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EngagementPatternSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['social_account']
    
    def get_queryset(self):
        return EngagementPattern.objects.filter(social_account__user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def optimal_times(self, request):
        account_id = request.query_params.get('account_id')
        limit = int(request.query_params.get('limit', 10))
        
        queryset = self.get_queryset()
        if account_id:
            queryset = queryset.filter(social_account_id=account_id)
        
        optimal = queryset.order_by('-avg_engagement_rate')[:limit]
        
        serializer = self.get_serializer(optimal, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def heatmap(self, request):
        account_id = request.query_params.get('account_id')
        
        queryset = self.get_queryset()
        if account_id:
            queryset = queryset.filter(social_account_id=account_id)
        
        heatmap_data = {}
        for pattern in queryset:
            day = pattern.day_of_week
            hour = pattern.hour_of_day
            
            if day not in heatmap_data:
                heatmap_data[day] = {}
            
            heatmap_data[day][hour] = {
                'engagement_rate': pattern.avg_engagement_rate,
                'likes': pattern.avg_likes,
                'comments': pattern.avg_comments,
                'shares': pattern.avg_shares,
                'post_count': pattern.post_count
            }
        
        return Response(heatmap_data)
    
    @action(detail=False, methods=['get'])
    def best_posting_schedule(self, request):
        account_id = request.query_params.get('account_id')
        posts_per_week = int(request.query_params.get('posts_per_week', 7))
        
        queryset = self.get_queryset()
        if account_id:
            queryset = queryset.filter(social_account_id=account_id)
        
        top_slots = queryset.order_by('-avg_engagement_rate')[:posts_per_week]
        
        schedule = []
        days_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        
        for slot in top_slots:
            schedule.append({
                'day': days_map[slot.day_of_week],
                'hour': slot.hour_of_day,
                'expected_engagement_rate': slot.avg_engagement_rate,
                'avg_likes': slot.avg_likes,
                'avg_comments': slot.avg_comments
            })
        
        return Response(schedule)

class AIInsightViewSet(viewsets.ModelViewSet):
    serializer_class = AIInsightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['insight_type', 'is_read', 'social_account']
    ordering_fields = ['priority', 'created_at']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        return AIInsight.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        insight = self.get_object()
        insight.is_read = True
        insight.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all insights marked as read'})

class QueryViewSet(viewsets.ModelViewSet):
    serializer_class = QuerySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Query.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def execute(self, request):
        query_text = request.data.get('query_text', '')
        
        if not query_text:
            return Response({'error': 'query_text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        start_time = timezone.now()
        
        response_data = {
            'query': query_text,
            'results': [],
            'message': 'Query processed successfully'
        }
        
        Query.objects.create(
            user=request.user,
            query_text=query_text,
            response=response_data['message'],
            response_data=response_data,
            execution_time=(timezone.now() - start_time).total_seconds()
        )
        
        return Response(response_data)

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report_type', 'status', 'format']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        report = self.get_object()
        report.status = 'processing'
        report.save()
        
        return Response({'status': 'report generation started', 'report_id': report.id})
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        report = self.get_object()
        
        if report.status != 'completed':
            return Response({'error': 'Report is not ready yet'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not report.file:
            return Response({'error': 'Report file not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'download_url': report.file.url})

class CompetitorViewSet(viewsets.ModelViewSet):
    serializer_class = CompetitorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['platform', 'is_active']
    search_fields = ['account_username']
    
    def get_queryset(self):
        return Competitor.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def comparison(self, request):
        competitor_ids = request.query_params.getlist('competitor_ids[]')
        
        if not competitor_ids:
            return Response({'error': 'competitor_ids are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        competitors = self.get_queryset().filter(id__in=competitor_ids)
        
        comparison_data = []
        
        for competitor in competitors:
            latest_metrics = competitor.metrics.order_by('-recorded_at').first()
            
            if latest_metrics:
                comparison_data.append({
                    'competitor_id': competitor.id,
                    'username': competitor.account_username,
                    'platform': competitor.platform,
                    'followers': latest_metrics.followers_count,
                    'following': latest_metrics.following_count,
                    'posts': latest_metrics.posts_count,
                    'avg_engagement_rate': latest_metrics.avg_engagement_rate,
                    'avg_likes': latest_metrics.avg_likes,
                    'avg_comments': latest_metrics.avg_comments
                })
        
        return Response(comparison_data)
    
    @action(detail=True, methods=['get'])
    def growth_trend(self, request, pk=None):
        competitor = self.get_object()
        days = int(request.query_params.get('days', 30))
        date_from = timezone.now() - timedelta(days=days)
        
        metrics_history = competitor.metrics.filter(
            recorded_at__gte=date_from
        ).order_by('recorded_at')
        
        trend_data = []
        for metrics in metrics_history:
            trend_data.append({
                'date': metrics.recorded_at.date().isoformat(),
                'followers': metrics.followers_count,
                'posts': metrics.posts_count,
                'avg_engagement': metrics.avg_engagement_rate
            })
        
        return Response(trend_data)

class CompetitorMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompetitorMetricsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['competitor']
    
    def get_queryset(self):
        return CompetitorMetrics.objects.filter(competitor__user=self.request.user)

class ContentStrategyViewSet(viewsets.ModelViewSet):
    serializer_class = ContentStrategySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['social_account', 'is_active']
    
    def get_queryset(self):
        return ContentStrategy.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        strategy = self.get_object()
        
        ContentStrategy.objects.filter(
            social_account=strategy.social_account
        ).update(is_active=False)
        
        strategy.is_active = True
        strategy.save()
        
        return Response({'status': 'strategy activated'})
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        account_id = request.data.get('account_id')
        
        if not account_id:
            return Response({'error': 'account_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            social_account = SocialMediaAccount.objects.get(id=account_id, user=request.user)
        except SocialMediaAccount.DoesNotExist:
            return Response({'error': 'Social account not found'}, status=status.HTTP_404_NOT_FOUND)
        
        strategy = ContentStrategy.objects.create(
            user=request.user,
            social_account=social_account,
            title=f"AI Generated Strategy - {timezone.now().strftime('%Y-%m-%d')}",
            description="Auto-generated content strategy based on performance analysis",
            recommendations=[],
            optimal_times=[],
            content_mix={},
            hashtag_strategy={}
        )
        
        serializer = self.get_serializer(strategy)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        user = request.user
        days = int(request.query_params.get('days', 30))
        date_from = timezone.now() - timedelta(days=days)
        
        total_accounts = SocialMediaAccount.objects.filter(user=user).count()
        
        total_posts = Post.objects.filter(
            social_account__user=user,
            posted_at__gte=date_from
        ).count()
        
        metrics_aggregate = PostMetrics.objects.filter(
            post__social_account__user=user,
            recorded_at__gte=date_from
        ).aggregate(
            total_likes=Sum('likes_count'),
            total_comments=Sum('comments_count'),
            total_shares=Sum('shares_count'),
            total_reach=Sum('reach'),
            avg_engagement=Avg('engagement_rate')
        )
        
        latest_audience = Audience.objects.filter(
            social_account__user=user
        ).order_by('-recorded_at').first()
        
        total_followers = latest_audience.followers_count if latest_audience else 0
        
        unread_insights = AIInsight.objects.filter(
            user=user,
            is_read=False
        ).count()
        
        overview_data = {
            'period_days': days,
            'total_accounts': total_accounts,
            'total_posts': total_posts,
            'total_followers': total_followers,
            'total_likes': metrics_aggregate['total_likes'] or 0,
            'total_comments': metrics_aggregate['total_comments'] or 0,
            'total_shares': metrics_aggregate['total_shares'] or 0,
            'total_reach': metrics_aggregate['total_reach'] or 0,
            'avg_engagement_rate': metrics_aggregate['avg_engagement'] or 0,
            'unread_insights': unread_insights
        }
        
        return Response(overview_data)
    
    @action(detail=False, methods=['get'])
    def platform_breakdown(self, request):
        user = request.user
        days = int(request.query_params.get('days', 30))
        date_from = timezone.now() - timedelta(days=days)
        
        platforms = SocialMediaAccount.objects.filter(user=user).values_list('platform', flat=True).distinct()
        
        breakdown = []
        
        for platform in platforms:
            posts = Post.objects.filter(
                social_account__user=user,
                social_account__platform=platform,
                posted_at__gte=date_from
            )
            
            metrics = PostMetrics.objects.filter(post__in=posts).aggregate(
                total_likes=Sum('likes_count'),
                total_comments=Sum('comments_count'),
                total_shares=Sum('shares_count'),
                avg_engagement=Avg('engagement_rate'),
                total_reach=Sum('reach')
            )

            breakdown.append({
                'platform': platform,
                'posts_count': posts.count(),
                'total_likes': metrics['total_likes'] or 0,
                'total_comments': metrics['total_comments'] or 0,
                'total_shares': metrics['total_shares'] or 0,
                'avg_engagement_rate': metrics['avg_engagement'] or 0,
                'total_reach': metrics['total_reach'] or 0
            })