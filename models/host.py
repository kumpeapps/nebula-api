"""Host model."""

import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database_config import Base, session
from models.ca import CA
from models.config_template import ConfigTemplate


class Host(Base):
    """Host model."""

    __tablename__ = "hosts"
    id = Column("id_hosts", Integer, primary_key=True, autoincrement=True)
    hostname = Column("hostname", String(255), unique=True, nullable=False)
    nebula_ip = Column("nebula_ip", String(255), nullable=False)
    tags = Column("tags", String(255), nullable=False)
    config_template = Column("config_template", String(255), nullable=False)
    allow_download = Column("allow_download", Boolean, nullable=False, default=True)
    active = Column("active", Boolean, nullable=False, default=True)
    host_token = Column("host_token", String(255), unique=True, nullable=False)
    ca_rotation_group = Column("ca_rotation_group", String(255), nullable=False)
    last_updated = Column(
        "last_updated", DateTime, nullable=False, default=datetime.datetime.now
    )

    certificates = relationship("Certificate", back_populates="host")

    @property
    def is_active(self):
        """Check if the host is active."""
        return self.active

    @property
    def cas(self):
        """Get the CAs in the host's rotation group that are not expired."""
        return session.query(CA).filter(
            CA.rotation_group == self.ca_rotation_group,
            CA.expires_at > datetime.datetime.now(),
        ).all()

    def __init__(
        self,
        hostname,
        nebula_ip,
        tags,
        config_template,
        host_token,
        ca_rotation_group,
    ):
        """Initialize Host model."""
        self.hostname = hostname
        self.nebula_ip = nebula_ip
        self.tags = tags
        self.config_template = config_template
        self.host_token = host_token
        self.ca_rotation_group = ca_rotation_group
        self.last_updated = datetime.datetime.now()

    def __repr__(self):
        """Return Host model object."""
        return f"<Host {self.hostname}>"

    def to_dict(self):
        """Convert Host model to dictionary."""
        return {
            "id": self.id,
            "hostname": self.hostname,
            "nebula_ip": self.nebula_ip,
            "tags": self.tags,
            "config_template": self.config_template,
            "allow_download": self.allow_download,
            "active": self.active,
            "host_token": self.host_token,
            "ca_rotation_group": self.ca_rotation_group,
            "last_updated": self.last_updated,
        }

    def __str__(self):
        return self.hostname
