"""
service_bus.py — Azure Service Bus client and publisher for NIWI asynchronous messaging.
Supports dual-mode configuration:
1. Local: Connection string (SERVICE_BUS_CONNECTION_STRING)
2. Production: Managed Identity (DefaultAzureCredential) via SERVICE_BUS_FQDN
3. Offline: Graceful fallback when neither is available
"""
import os
import json
import logging
import threading
from typing import Optional, Dict, Any

from app.core.config import APP_ENV, IS_PRODUCTION

logger = logging.getLogger(__name__)

# Service Bus Environment Configurations
SERVICE_BUS_CONNECTION_STRING = os.environ.get("SERVICE_BUS_CONNECTION_STRING", os.environ.get("SERVICE-BUS-CONNECTION-STRING", "")).strip()
SERVICE_BUS_FQDN = os.environ.get("SERVICE_BUS_FQDN", os.environ.get("SERVICE-BUS-FQDN", "")).strip()
SERVICE_BUS_QUEUE_NAME = os.environ.get("SERVICE_BUS_QUEUE_NAME", os.environ.get("SERVICE-BUS-QUEUE-NAME", "niwi-submission-queue")).strip()
SERVICE_BUS_ENABLED = os.environ.get("SERVICE_BUS_ENABLED", os.environ.get("SERVICE-BUS-ENABLED", "true")).lower() in ("true", "1")

SERVICE_BUS_MAX_DELIVERY_COUNT = int(os.environ.get("SERVICE_BUS_MAX_DELIVERY_COUNT", "10"))
SERVICE_BUS_LOCK_DURATION_SECONDS = int(os.environ.get("SERVICE_BUS_LOCK_DURATION_SECONDS", "60"))
SERVICE_BUS_CONCURRENCY = int(os.environ.get("SERVICE_BUS_CONCURRENCY", "4"))

_client: Optional[Any] = None
_sender: Optional[Any] = None
_lock = threading.Lock()
_init_attempted = False
_is_available = False


def is_service_bus_configured() -> bool:
    """
    Check if Service Bus is configured and ready to use:
    1. Local mode: SERVICE_BUS_CONNECTION_STRING is non-empty
    2. Production mode: IS_PRODUCTION is True and SERVICE_BUS_FQDN is non-empty
    3. Fallback: False (offline DB-outbox worker)
    """
    if not SERVICE_BUS_ENABLED:
        return False
    if SERVICE_BUS_CONNECTION_STRING:
        return True
    if IS_PRODUCTION and SERVICE_BUS_FQDN:
        return True
    return False


def get_service_bus_client() -> Optional[Any]:
    """
    Get or initialize singleton ServiceBusClient.
    Priority 1: SERVICE_BUS_CONNECTION_STRING (local dev/test)
    Priority 2: SERVICE_BUS_FQDN via DefaultAzureCredential (production)
    Fallback: None (offline DB-outbox fallback)
    """
    global _client, _init_attempted, _is_available

    if not SERVICE_BUS_ENABLED:
        return None

    if _client is not None:
        return _client

    with _lock:
        if _client is not None:
            return _client

        from azure.servicebus import ServiceBusClient

        if SERVICE_BUS_CONNECTION_STRING:
            try:
                logger.info("Initializing Azure Service Bus client via connection string for queue: %s", SERVICE_BUS_QUEUE_NAME)
                _client = ServiceBusClient.from_connection_string(
                    SERVICE_BUS_CONNECTION_STRING,
                    logging_enable=False
                )
                _is_available = True
                return _client
            except Exception as e:
                logger.warning("Failed to initialize Service Bus client via connection string: %s", e)
                _client = None
                return None

        elif SERVICE_BUS_FQDN:
            try:
                logger.info("Initializing Azure Service Bus client via Managed Identity for FQDN: %s", SERVICE_BUS_FQDN)
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                _client = ServiceBusClient(
                    fully_qualified_namespace=SERVICE_BUS_FQDN,
                    credential=credential,
                    logging_enable=False
                )
                _is_available = True
                return _client
            except Exception as e:
                logger.warning("Failed to initialize Service Bus client via DefaultAzureCredential: %s", e)
                _client = None
                return None
        else:
            logger.info("No Azure Service Bus credentials configured. Running in offline DB-outbox fallback mode.")
            return None


def get_service_bus_sender(queue_name: Optional[str] = None) -> Optional[Any]:
    """Get ServiceBusSender for the specified queue (defaults to SERVICE_BUS_QUEUE_NAME)."""
    target_queue = queue_name or SERVICE_BUS_QUEUE_NAME
    client = get_service_bus_client()
    if not client:
        return None
    return client.get_queue_sender(queue_name=target_queue)


def publish_event(
    event_type: str,
    aggregate_id: str,
    payload: Dict[str, Any],
    message_id: Optional[str] = None,
    queue_name: Optional[str] = None
) -> Optional[str]:
    """
    Publish an event message to the Service Bus submission queue.
    Ensures MessageId = submission_id for Azure Service Bus duplicate detection.
    
    Returns:
        message_id string used for publishing, or None if Service Bus is unconfigured.
    """
    from azure.servicebus import ServiceBusMessage

    target_queue = queue_name or SERVICE_BUS_QUEUE_NAME
    sender = get_service_bus_sender(queue_name=target_queue)
    if not sender:
        logger.debug("Service Bus sender not available; event %s (%s) will use DB fallback", event_type, aggregate_id)
        return None

    # Requirement: Duplicate detection enabled with MessageId = submission_id
    msg_id = message_id or str(aggregate_id)
    body = json.dumps(payload, default=str)

    message = ServiceBusMessage(
        body=body,
        message_id=msg_id,
        correlation_id=str(aggregate_id),
        content_type="application/json",
        application_properties={
            "event_type": event_type,
            "aggregate_id": str(aggregate_id)
        }
    )

    if hasattr(sender, "__enter__"):
        with sender:
            sender.send_messages(message)
    else:
        sender.send_messages(message)

    logger.info("Published event %s (MessageId: %s) to Service Bus queue '%s'", event_type, msg_id, target_queue)
    return msg_id


def close_service_bus() -> None:
    """Gracefully close sender and client connections."""
    global _client, _sender
    with _lock:
        if _sender is not None:
            try:
                _sender.close()
                logger.info("Service Bus sender closed.")
            except Exception as e:
                logger.warning("Error closing Service Bus sender: %s", e)
            finally:
                _sender = None

        if _client is not None:
            try:
                _client.close()
                logger.info("Service Bus client closed.")
            except Exception as e:
                logger.warning("Error closing Service Bus client: %s", e)
            finally:
                _client = None
