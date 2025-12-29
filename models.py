"""
Database models for CVAnalyzer application.
Defines User, CVUpload, JobSearch, and SavedJob models with relationships.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """
    User model for stored authenticated user information.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    profile_picture = Column(String(512))
    
    # OAuth provider information
    oauth_provider = Column(String(50), nullable=False)  # google, github, linkedin
    oauth_id = Column(String(255), nullable=False)  # Provider's user ID
    
    # Preferences
    default_region = Column(String(100), default='Remote')
    default_job_source = Column(String(50), default='jobicy')  # jobicy or jobspy
    email_notifications = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    cv_uploads = relationship("CVUpload", back_populates="user", cascade="all, delete-orphan")
    job_searches = relationship("JobSearch", back_populates="user", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")
    
    # Unique constraint on oauth_provider + oauth_id
    __table_args__ = (
        Index('idx_oauth', 'oauth_provider', 'oauth_id', unique=True),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', provider='{self.oauth_provider}')>"
    
    def to_dict(self):
        """Convert user to dictionary for API responses."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'profile_picture': self.profile_picture,
            'oauth_provider': self.oauth_provider,
            'default_region': self.default_region,
            'default_job_source': self.default_job_source,
            'email_notifications': self.email_notifications,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class CVUpload(Base):
    """
    Model for storing uploaded CV files and their metadata.
    """
    __tablename__ = 'cv_uploads'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)  # Path to stored file
    file_size = Column(Integer)  # Size in bytes
    
    # Extracted profile information (cached for performance)
    profile_data = Column(Text)  # JSON string of extracted CV profile
    
    # Metadata
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used = Column(DateTime(timezone=True))  # Track when CV was last used for job search
    
    # Relationships
    user = relationship("User", back_populates="cv_uploads")
    job_searches = relationship("JobSearch", back_populates="cv_upload")
    
    def __repr__(self):
        return f"<CVUpload(id={self.id}, user_id={self.user_id}, filename='{self.filename}')>"
    
    def to_dict(self):
        """Convert CV upload to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
        }


class JobSearch(Base):
    """
    Model for storing job search history and parameters.
    """
    __tablename__ = 'job_searches'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    cv_upload_id = Column(Integer, ForeignKey('cv_uploads.id'), nullable=True)
    
    # Search parameters
    job_source = Column(String(50), nullable=False)  # jobicy or jobspy
    region = Column(String(100))
    job_title = Column(String(255))  # For JobSpy searches
    jobspy_sites = Column(String(255))  # Comma-separated sites for JobSpy
    
    # Search results metadata
    total_jobs_found = Column(Integer, default=0)
    jobs_above_threshold = Column(Integer, default=0)
    average_match_score = Column(Float)
    highest_match_score = Column(Float)
    
    # Timing
    search_duration_seconds = Column(Float)  # How long the search took
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="job_searches")
    cv_upload = relationship("CVUpload", back_populates="job_searches")
    
    def __repr__(self):
        return f"<JobSearch(id={self.id}, user_id={self.user_id}, source='{self.job_source}', jobs={self.total_jobs_found})>"
    
    def to_dict(self):
        """Convert job search to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'cv_upload_id': self.cv_upload_id,
            'job_source': self.job_source,
            'region': self.region,
            'job_title': self.job_title,
            'jobspy_sites': self.jobspy_sites,
            'total_jobs_found': self.total_jobs_found,
            'jobs_above_threshold': self.jobs_above_threshold,
            'average_match_score': self.average_match_score,
            'highest_match_score': self.highest_match_score,
            'search_duration_seconds': self.search_duration_seconds,
            'searched_at': self.searched_at.isoformat() if self.searched_at else None,
        }


class SavedJob(Base):
    """
    Model for storing jobs saved/bookmarked by users.
    """
    __tablename__ = 'saved_jobs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Job information (denormalized for persistence even if source changes)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255))
    location = Column(String(255))
    job_url = Column(String(1024), nullable=False)
    description = Column(Text)
    job_type = Column(String(100))  # Full-time, Part-time, Contract, etc.
    
    # Match information
    match_score = Column(Float)
    match_reasons = Column(Text)  # JSON array of reasons
    
    # User notes and status
    notes = Column(Text)  # User's personal notes about the job
    application_status = Column(String(50), default='saved')  # saved, applied, interview, rejected, accepted
    applied_at = Column(DateTime(timezone=True))
    
    # Metadata
    saved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_jobs")
    
    def __repr__(self):
        return f"<SavedJob(id={self.id}, user_id={self.user_id}, title='{self.job_title}', status='{self.application_status}')>"
    
    def to_dict(self):
        """Convert saved job to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_title': self.job_title,
            'company': self.company,
            'location': self.location,
            'job_url': self.job_url,
            'description': self.description,
            'job_type': self.job_type,
            'match_score': self.match_score,
            'match_reasons': self.match_reasons,
            'notes': self.notes,
            'application_status': self.application_status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'saved_at': self.saved_at.isoformat() if self.saved_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
