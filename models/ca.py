"""Certificate Authority model."""

import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from database_config import Base


class CA(Base):
    """CA model."""

    __tablename__ = "certificate_authorities"
    id = Column("id_ca", Integer, primary_key=True, autoincrement=True, nullable=False)
    certificate = Column("certificate", Text(500), nullable=False)
    active = Column("active", Boolean, nullable=False, default=True)
    name = Column("name", String(50), nullable=False)
    issued_at = Column(
        "issued", DateTime, nullable=False, default=datetime.datetime.now
    )
    expires_at = Column("expires", DateTime, nullable=False)
    rotation_group = Column("rotation_group", String(255), nullable=False)
    
    certificates = relationship("Certificate", back_populates="ca")

    @property
    def is_active(self):
        """Check if the CA is active."""
        return self.active

    @property
    def is_expired(self):
        """Check if the CA is expired."""
        return datetime.datetime.now() > self.expires_at

    def __init__(self, certificate, name, rotation_group, expires_at):
        """Initialize CA model."""
        self.certificate = certificate
        self.name = name
        self.rotation_group = rotation_group
        self.expires_at = expires_at

    def __repr__(self):
        """Return CA model object."""
        return f"<CA {self.name}>"

    def to_dict(self):
        """Convert CA model to dictionary."""
        return {
            "id": self.id,
            "certificate": self.certificate,
            "active": self.active,
            "name": self.name,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "rotation_group": self.rotation_group,
        }

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, CA):
            return self.certificate == other.certificate
        return self.certificate == other
