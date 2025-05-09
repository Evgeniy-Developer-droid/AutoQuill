from sqladmin import ModelView
from app.users.models import User, UserSetting, Company
from app.auth.models import AuthSession
from app.channels.models import Channel
from app.posts.models import Post
from app.ai.models import Source, AIConfig, ScheduledAIPost


class AdminModelView(ModelView):
    page_size = 50
    column_default_sort = ("id", True,)


class UserAdmin(AdminModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.is_active,
        User.is_superuser,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.full_name]


class UserSettingAdmin(AdminModelView, model=UserSetting):
    column_list = [UserSetting.id, UserSetting.user_id]
    column_searchable_list = [UserSetting.id, UserSetting.user_id]


class AuthSessionAdmin(AdminModelView, model=AuthSession):
    column_list = [AuthSession.id, AuthSession.user_id, AuthSession.created_at, AuthSession.expired_at]
    column_searchable_list = [AuthSession.id, AuthSession.user_id]


class CompanyAdmin(AdminModelView, model=Company):
    column_list = [
        Company.id,
        Company.name,
        Company.created_at,
    ]
    column_searchable_list = [Company.id, Company.name]
    column_filters = [Company.name]


class ChannelAdmin(AdminModelView, model=Channel):
    column_list = [
        Channel.id,
        Channel.company_id,
        Channel.channel_type,
        Channel.created_at,
    ]
    column_searchable_list = [Channel.id, Channel.company_id, Channel.channel_type]
    column_filters = [Channel.company_id, Channel.channel_type]


class PostAdmin(AdminModelView, model=Post):
    column_list = [
        Post.id,
        Post.channel_id,
        Post.company_id,
        Post.status,
        Post.scheduled_time,
        Post.created_at,
    ]
    column_searchable_list = [Post.id, Post.channel_id, Post.company_id]
    column_filters = [Post.channel_id, Post.company_id]


class SourceAdmin(AdminModelView, model=Source):
    column_list = [
        Source.id,
        Source.channel_id,
        Source.company_id,
        Source.source_type,
        Source.document_id,
        Source.created_at,
    ]
    column_searchable_list = [Source.id, Source.channel_id, Source.company_id, Source.document_id]
    column_filters = [Source.channel_id, Source.company_id]


class AIConfigAdmin(AdminModelView, model=AIConfig):
    column_list = [
        AIConfig.id,
        AIConfig.channel_id,
        AIConfig.company_id,
        AIConfig.created_at,
    ]
    column_searchable_list = [AIConfig.id, AIConfig.channel_id, AIConfig.company_id]
    column_filters = [AIConfig.channel_id, AIConfig.company_id]


class ScheduledAIPostAdmin(AdminModelView, model=ScheduledAIPost):
    column_list = [
        ScheduledAIPost.id,
        ScheduledAIPost.channel_id,
        ScheduledAIPost.company_id,
        ScheduledAIPost.weekdays,
        ScheduledAIPost.times,
        ScheduledAIPost.is_active,
    ]
    column_searchable_list = [ScheduledAIPost.id, ScheduledAIPost.channel_id, ScheduledAIPost.company_id]
    column_filters = [ScheduledAIPost.channel_id, ScheduledAIPost.company_id]




