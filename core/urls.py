from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("tags", views.TagsModelViewSet)

urlpatterns = [
    path('api/login/', views.LoginView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
    path('api/signup/', views.SignUpView.as_view(), name='sign-up'),
    path('api/follow/', views.FollowCreateApiView.as_view(), name='follow'),
    path('api/commments/<int:pk>', views.CommentDetailView.as_view(), name='comment detail'),
    path('api/view/', views.ArticleViewCreateApiView.as_view(), name='view-create'),
    path('api/feed/', views.FeedApiView.as_view(), name='feed'),
    path('api/profile/<slug:username>', views.ProfileDetailView.as_view(), name='profile'),
    path('api/articles/<int:pk>', views.ArticleDetailPublicView.as_view(), name='article public view'),
    path('api/user-info/', views.ProfileUpdateView.as_view(), name='user info'),
    path('api/user/articles', views.UserArticleListCreateApiView.as_view(), name='articles'),
    path('api/articles/<int:article_id>/comments', views.CommentListCreateApiView.as_view(), name='comments'),
    path('api/articles/<int:article_id>/reactions', views.ArticleReactionCreateDeleteApiView.as_view(), name='reactions'),
    path('api/user/articles/<int:pk>', views.UserArticleDetailView.as_view(), name='article-detail'),
    path('api/', include(router.urls)),
]
