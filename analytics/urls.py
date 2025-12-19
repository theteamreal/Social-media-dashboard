from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'social-accounts', SocialMediaAccountViewSet, basename='social-accounts')
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'post-metrics', PostMetricsViewSet, basename='post-metrics')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'hashtags', HashtagViewSet, basename='hashtags')
router.register(r'audience', AudienceViewSet, basename='audience')
router.register(r'engagement-patterns', EngagementPatternViewSet, basename='engagement-patterns')
router.register(r'insights', AIInsightViewSet, basename='insights')
router.register(r'queries', QueryViewSet, basename='queries')
router.register(r'reports', ReportViewSet, basename='reports')
router.register(r'competitors', CompetitorViewSet, basename='competitors')
router.register(r'competitor-metrics', CompetitorMetricsViewSet, basename='competitor-metrics')
router.register(r'content-strategies', ContentStrategyViewSet, basename='content-strategies')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]