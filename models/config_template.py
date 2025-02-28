"""Nebula Config Template Model."""

import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from database_config import Base


class ConfigTemplate(Base):
    """Config Template model."""

    __tablename__ = "config_templates"
    id = Column(
        "id_configtemplate",
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    template_name = Column("template_name", String(255), nullable=False)
    config = Column("config", Text(100000), nullable=False)
    last_updated = Column(
        "last_updated", DateTime, nullable=False, default=datetime.datetime.now
    )

    def __init__(self, template_name, config):
        """Initialize Config Template model."""
        self.template_name = template_name
        self.config = config
        self.last_updated = datetime.datetime.now()

    def __repr__(self):
        """Return Config Template model object."""
        return f"<ConfigTemplate {self.template_name}>"

    def to_dict(self):
        """Convert Config Template model to dictionary."""
        return {
            "id": self.id,
            "template_name": self.template_name,
            "config": self.config,
            "last_updated": self.last_updated,
        }

    def __str__(self):
        return self.template_name
