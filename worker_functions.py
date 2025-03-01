"""Functions for generating and removing certificates."""

import subprocess
import os
from datetime import datetime, timedelta
from flask import jsonify
from loguru import logger
from models.host import Host
from models.ca import CA
from models.certificate import Certificate
from database_config import session


def rm_host_certs(host: Host):
    """Remove old certificates for the host."""
    old_cert_path = f"{host.hostname}.crt"
    if os.path.exists(old_cert_path):
        try:
            remove_old_cert_cmd = ["rm", old_cert_path]
            subprocess.run(remove_old_cert_cmd)
        except Exception as e:
            logger.error(f"Failed to remove old certificate: {e}")
            return jsonify({"error": "Failed to remove old certificate"}), 500
        else:
            logger.info(f"No certificate found for {host.hostname} to remove.")


def generate_ca(ca_ttl_days: str, ca_name: str, ca_rotation_group: str, ca_folder: str):
    """Generate a new CA certificate."""
    ca_cert_path = f"{ca_folder}/ca.crt"
    ca_key_path = f"{ca_folder}/ca.key"
    ca_ttl = f"{int(ca_ttl_days) * 24}h"
    generate_ca_cmd = [
        "nebula-cert",
        "ca",
        "-name",
        ca_name,
        "-duration",
        ca_ttl,
        "-out-crt",
        ca_cert_path,
        "-out-key",
        ca_key_path,
    ]
    if os.path.exists(ca_cert_path) and os.path.exists(ca_key_path):
        remove_ca_cmd = ["rm", ca_cert_path, ca_key_path]
        subprocess.run(remove_ca_cmd)
    else:
        logger.warning("CA certificate or key file does not exist, skipping removal")
    result = subprocess.run(generate_ca_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("Failed to generate new CA certificate")
        logger.debug(result.stderr)
        return jsonify({"error": "Failed to generate new CA certificate"}), 500

    logger.info("New CA certificate generated successfully")

    # Update the CA certificate in the database
    with open(ca_cert_path, "r") as cert_file:
        new_ca_cert = cert_file.read()

    ca_cert: CA = CA(
        new_ca_cert,
        ca_name,
        ca_rotation_group,
        datetime.now() + timedelta(days=int(ca_ttl_days)),
    )
    session.add(ca_cert)
    session.commit()

    logger.info("CA certificate updated in the database")


def generate_host_cert(host: Host, ca_cert: CA, ca_folder: str) -> Certificate:
    """Generate a new host certificate."""
    rm_host_certs(host)
    host_cert_path = f"{host.hostname}.crt"
    generate_cmd = [
        "nebula-cert",
        "sign",
        "-ca-crt",
        f"{ca_folder}/ca.crt",
        "-ca-key",
        f"{ca_folder}/ca.key",
        "-in-pub",
        f"{host.hostname}.pub",
        "-name",
        host.hostname,
        "-ip",
        host.nebula_ip,
        "-groups",
        host.tags,
        "-out-crt",
        host_cert_path,
    ]
    result = subprocess.run(generate_cmd, capture_output=True, text=True)  # type: ignore

    if result.returncode != 0:
        logger.error("Failed to generate host certificate")
        logger.debug(result.stderr)
        raise Exception("Failed to generate host certificate")

    with open(host_cert_path, "r") as cert_file:
        new_host_cert = cert_file.read()

    # Update the host certificate in the database
    host_cert = Certificate(
        new_host_cert,
        host.hostname,
        datetime.now() + timedelta(days=365),
        host.id,
        ca_cert.id,
    )
    session.add(host_cert)
    session.commit()
    delete_cmd = ["rm", host_cert_path]
    subprocess.run(delete_cmd)

    logger.info("New host certificate generated and updated in the database")

    return host_cert
