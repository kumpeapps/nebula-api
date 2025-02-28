"""Certificate model."""

import datetime
from string import Template
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from loguru import logger
from database_config import Base, session
from models.host import Host
from models.ca import CA
from models.config_template import ConfigTemplate


class Certificate(Base):
    """Certificate model."""

    __tablename__ = "certificates"
    id = Column(
        "id_certificate", Integer, primary_key=True, autoincrement=True, nullable=False
    )
    id_host = Column("id_host", Integer, ForeignKey(Host.id), nullable=False)
    fingerprint = Column("fingerprint", String(100), nullable=False)
    active = Column("active", Boolean, nullable=False, default=True)
    blocked = Column("blocked", Boolean, nullable=False, default=False)
    issued_at = Column(
        "issue_date", DateTime, nullable=False, default=datetime.datetime.now
    )
    id_ca = Column("id_ca", Integer, ForeignKey(CA.id), nullable=False)
    expires_at = Column("expiration_date", DateTime, nullable=False)
    certificate = Column("certificate", Text(500), nullable=False)

    host = relationship("Host", back_populates="certificates")
    ca = relationship("CA", back_populates="certificates")

    @property
    def is_active(self):
        """Check if the certificate is active."""
        return self.active

    @property
    def is_expired(self):
        """Check if the certificate is expired."""
        return datetime.datetime.now() > self.expires_at

    def config(self, private_key):
        """Build Config Template for the host."""
        logger.debug("Building config template for host")
        config_template = (
            session.query(ConfigTemplate)
            .filter_by(template_name=self.host.config_template)
            .first()
        )
        template = Template(f"{config_template.config}")
        # template.replace("{ host_cert }", self.certificate)
        # template.replace("{ host_key }", private_key)
        ca_block = ""
        for ca in self.host.cas:
            ca_block += f"ca: |\n{ca.certificate}\n"
        template = template.safe_substitute(
            host_cert=self.certificate,
            host_key=private_key,
            ca_block=ca_block,
        )
        return template

    def __init__(self, certificate, fingerprint, expires_at, id_host, id_ca):
        """Initialize Certificate model."""
        self.certificate = certificate
        self.fingerprint = fingerprint
        self.expires_at = expires_at
        self.id_host = id_host
        self.id_ca = id_ca

    def __repr__(self):
        """Return Certificate model object."""
        return f"<Certificate {self.host.hostname}>"

    def to_dict(self):
        """Convert Certificate model to dictionary."""
        return {
            "id": self.id,
            "fingerprint": self.fingerprint,
            "active": self.active,
            "blocked": self.blocked,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "certificate": self.certificate,
        }

    def __str__(self):
        return self.fingerprint

    def __eq__(self, other):
        if isinstance(other, Certificate):
            return self.certificate == other.certificate
        return self.certificate == other
