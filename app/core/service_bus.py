"""
service_bus.py — Azure Service Bus client and publisher for NIWI asynchronous messaging.
Connects to Azure Service Bus using Managed Identity (DefaultAzureCredential).
"""
import os
import json
import logging
import threading
from typing import Optional, Dict, Any

from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusSender

logger = logging.getLogger(__name__)

# Service Bus Configuration
SERVICE_BUS_FQDN = os.environ.get("SERVICE_BUS_FQDN", "niwi-bus.servicebus.windows.net")
SERVICE_BUS_QUEUE_NAME = os.environ.get("SERVICE_BUS_QUEUE_NAME", "niwi-submission-queue")

_client: Optional[ServiceBusClient] = None
_sender: Optional[ServiceBusSender] = None
_lock = threading.Lock()


def get_service_bus_client() -> ServiceBusClient:
    """Get or initialize singleton ServiceBusClient using DefaultAzureCredential."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                logger.info("Initializing Azure Service Bus client for namespace: %s", SERVICE_BUS_FQDN)
                credential = DefaultAzureCredential()
                _client = ServiceBusClient(
                    fully_qualified_namespace=SERVICE_BUS_FQDN,
                    credential=credential,
                    logging_enable=False
                )
    return _client


def get_service_bus_sender(queue_name: str = SERVICE_BUS_QUEUE_NAME) -> ServiceBusSender:
    """Get ServiceBusSender for the submission queue."""
    client = get_service_bus_client()
    return client.get_queue_sender(queue_name=queue_name)


def publish_event(
    event_type: str,
    aggregate_id: str,
    payload: Dict[str, Any],
    message_id: Optional[str] = None
) -> str:
    """
    Publish an event message to the Service Bus submission queue.
    
    Args:
        event_type: Type of the event (e.g., 'SUBMISSION_CREATED')
        aggregate_id: Entity UUID (e.g., submission_id)
        payload: Event data dictionary
        message_id: Custom message ID for duplicate detection (defaults to sub-{aggregate_id}-{event_type})
        
    Returns:
        message_id string used for publishing.
    """
    msg_id = message_id or f"sub-{aggregate_id}-{event_type}"
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
    
    sender = get_service_bus_sender(queue_name=SERVICE_BUS_QUEUE_NAME)
    if hasattr(sender, "__enter__"):
        with sender:
            sender.send_messages(message)
    else:
        sender.send_messages(message)
    logger.info("Published event %s (id: %s) to Service Bus queue %s", event_type, msg_id, SERVICE_BUS_QUEUE_NAME)
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
