"""
Social platform models for ANIP.
Covers: Users, Communities, Posts, Comments, Votes, Notifications, Bookmarks, Alerts, User Settings.
"""
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey, Table, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from anip.shared.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    bio = Column(Text)
    avatar_url = Column(Text)
    karma = Column(Integer, default=0)
    preferred_language = Column(String(10), default="en")
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    votes = relationship("Vote", back_populates="user")
    notifications = relationship("Notification", back_populates="user", foreign_keys="Notification.user_id")
    bookmarks = relationship("Bookmark", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    member_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="community")


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    community_id = Column(Integer, ForeignKey("communities.id"))
    article_id = Column(Integer, ForeignKey("newsarticle.id"), nullable=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    post_type = Column(String(20), default="discussion")  # discussion, link, article_share, alert
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    importance_score = Column(Integer, default=50)
    importance_breakdown = Column(JSON, nullable=True)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    community = relationship("Community", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"))
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")


class Vote(Base):
    __tablename__ = "votes"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    votable_id = Column(UUID(as_uuid=True), primary_key=True)
    votable_type = Column(String(20), primary_key=True)  # 'post', 'comment'
    vote_type = Column(Integer)  # 1 for upvote, -1 for downvote
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="votes")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Who triggered it
    type = Column(String(30), nullable=False)  # 'vote', 'comment', 'reply', 'mention', 'alert', 'system'
    title = Column(Text, nullable=False)
    message = Column(Text)
    link = Column(Text)  # URL to navigate to
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(String(100), nullable=False)  # post_id or article_id
    target_type = Column(String(20), nullable=False)  # 'post' or 'article'
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookmarks")


class DisasterAlert(Base):
    __tablename__ = "disaster_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(Integer, ForeignKey("newsarticle.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # earthquake, flood, hurricane, wildfire, tsunami, etc.
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    title = Column(Text, nullable=False)
    description = Column(Text)
    location = Column(Text)  # Affected area
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source_count = Column(Integer, default=1)  # How many sources report this
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    theme = Column(String(20), default="dark")  # dark, light, auto
    language = Column(String(10), default="en")  # en, es, fr, de, zh, ar, hi, pt, ja, ko
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    whatsapp_notifications = Column(Boolean, default=True)
    notify_on_votes = Column(Boolean, default=True)
    notify_on_comments = Column(Boolean, default=True)
    notify_on_replies = Column(Boolean, default=True)
    notify_on_alerts = Column(Boolean, default=True)
    feed_sort = Column(String(20), default="hot")  # hot, new, top
    show_sentiment = Column(Boolean, default=True)
    show_ai_analysis = Column(Boolean, default=True)

    user = relationship("User", back_populates="settings")
