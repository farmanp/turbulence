"""Utilities for gRPC reflection and dynamic message handling."""

import logging
from typing import Any

import grpc
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc

logger = logging.getLogger(__name__)


class GrpcReflectionClient:
    """Client for interacting with gRPC reflection service."""

    def __init__(self, channel: grpc.aio.Channel):
        """Initialize with an open async channel."""
        self.channel = channel
        self.stub = reflection_pb2_grpc.ServerReflectionStub(channel)
        self.pool = descriptor_pool.DescriptorPool()
        self.factory = message_factory.MessageFactory(self.pool)
        self._loaded_files: set[str] = set()

    async def resolve_service(self, service_name: str) -> bool:
        """Resolve a service and its dependencies into the descriptor pool.
        
        Args:
            service_name: Full service name (e.g. 'pkg.Service')
            
        Returns:
            True if service was resolved, False otherwise.
        """
        try:
            request = reflection_pb2.ServerReflectionRequest(
                file_containing_symbol=service_name
            )
            # ServerReflection is a bidi stream, but for these requests
            # we can just send one and get one or more back.
            # Using async iterator for the stream.

            call = self.stub.ServerReflectionInfo(iter([request]))
            async for response in call:
                if response.HasField("error_response"):
                    logger.error(f"Reflection error for {service_name}: {response.error_response.error_message}")
                    return False

                if response.HasField("file_descriptor_response"):
                    for fd_proto_data in response.file_descriptor_response.file_descriptor_proto:
                        fd_proto = descriptor_pb2.FileDescriptorProto()
                        fd_proto.ParseFromString(fd_proto_data)

                        if fd_proto.name not in self._loaded_files:
                            try:
                                self.pool.Add(fd_proto)
                                self._loaded_files.add(fd_proto.name)
                            except Exception as e:
                                # Often happens if already added via another path
                                logger.debug(f"Failed to add {fd_proto.name} to pool: {e}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Reflection call failed for {service_name}: {e}")
            return False

    def get_message_classes(self, service_name: str, method_name: str) -> tuple[Any, Any] | None:
        """Get request and response message classes for a method.
        
        Args:
            service_name: Full service name.
            method_name: Method name.
            
        Returns:
            Tuple of (RequestClass, ResponseClass) or None.
        """
        try:
            service_desc = self.pool.FindServiceByName(service_name)
            method_desc = service_desc.FindMethodByName(method_name)

            request_class = self.factory.GetMessageClass(method_desc.input_type)
            response_class = self.factory.GetMessageClass(method_desc.output_type)

            return request_class, response_class
        except Exception as e:
            logger.error(f"Failed to find method {service_name}/{method_name}: {e}")
            return None
