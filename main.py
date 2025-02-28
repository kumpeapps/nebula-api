"""Nebula API server to verify and generate host certificates."""

import subprocess
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from loguru import logger
from models.host import Host
from models.ca import CA
from models.certificate import Certificate
from database_config import session, Base, engine
import worker_functions as worker


app = Flask(__name__)

CA_TTL_DAYS = os.environ.get("NEBULA_CA_TTL_DAYS", "365")  # Default 1 year
CA_NAME = os.environ.get("NEBULA_CA_NAME", "Nebula CA")
CA_ROTATION_GROUP = os.environ.get("NEBULA_CA_ROTATION_GROUP", "default")


@app.route("/api/config", methods=["POST"])
def get_config():
    """Get the host configuration."""
    logger.info("Received request for host configuration")

    data = request.json
    host_token = data.get("host_token")
    private_key = data.get("private_key")
    host_cert = data.get("host_cert", "")

    if not host_token or not private_key:
        logger.error("host_token and private_key are required")
        return jsonify({"error": "host_token and private_key are required"}), 400

    host: Host = session.query(Host).filter_by(host_token=host_token).first()

    if not host:
        logger.error(f"Host not found for token: {host_token}")
        return jsonify({"error": "Host not found"}), 404

    worker.rm_host_certs(host)

    try:
        with open(f"{host.hostname}.pub", "w", encoding="utf-8") as f:
            f.write(data.get("private_key"))
    except IOError as e:
        logger.error(f"Failed to write private key to file: {e}")
        return jsonify({"error": "Failed to write private key to file"}), 500

    if not os.path.exists("ca.crt") or not os.path.exists("ca.key"):
        logger.info(
            "CA certificate or key file does not exist, generating a new CA certificate"
        )
        worker.generate_ca(CA_TTL_DAYS, CA_NAME, CA_ROTATION_GROUP)

    # Check if the CA certificate is within 90 days of expiration
    ca_cert = session.query(CA).order_by(CA.issued_at.desc()).first()
    if ca_cert:
        expiration_date = ca_cert.expires_at
        days_to_expiration = (expiration_date - datetime.now()).days
        logger.debug(f"CA certificate expires in {days_to_expiration} days")

        if days_to_expiration <= 90:
            logger.info(
                "CA certificate is within 90 days of expiration, generating a new CA certificate"
            )
            worker.generate_ca(CA_TTL_DAYS, CA_NAME, CA_ROTATION_GROUP)
    else:
        logger.info("No CA certificate found, generating a new CA certificate")
        worker.generate_ca(CA_TTL_DAYS, CA_NAME, CA_ROTATION_GROUP)

    if host_cert:
        logger.info("Verifying the host certificate")
        # Verify the host certificate
        verify_cmd = [
            "nebula-cert",
            "verify",
            "-ca",
            "ca.crt",
            "-crt",
            f"{host.hostname}.crt",
        ]

        f = open(f"{host.hostname}.crt", "w")
        f.write(data.get("host_cert"))
        f.close()
        result = subprocess.run(verify_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Invalid or expired host certificate")
            logger.debug(result.stderr)
            logger.info("Generating a new host certificate")
            host_cert = worker.generate_host_cert(host, ca_cert)
            worker.rm_host_certs(host)
        else:
            logger.info("Host certificate is valid")

        worker.rm_host_certs(host)
        latest_cert = (
            session.query(Certificate)
            .filter_by(id_host=host.id)
            .order_by(Certificate.expires_at.desc())
            .first()
        )
        return (
            jsonify(
                {
                    "host_cert": latest_cert.certificate,
                    "config_template": latest_cert.config(private_key),
                }
            ),
            200,
        )
    else:
        logger.info("Generating a new host certificate")
        host_cert = worker.generate_host_cert(host, ca_cert)
        worker.rm_host_certs(host)

        logger.info("New host certificate generated and updated in the database")

        return (
            jsonify(
                {
                    "host_cert": host_cert.certificate,
                    "config_template": host_cert.config(private_key),
                }
            ),
            201,
        )


if __name__ == "__main__":
    logger.trace("Creating database tables")
    Base.metadata.create_all(engine)
    logger.trace("Database tables created")
    logger.info(f"Starting Nebula API server for CA: {CA_NAME}")
    app.run(debug=True)
