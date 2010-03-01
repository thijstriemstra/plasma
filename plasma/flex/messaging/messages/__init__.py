# Copyright The Plasma Project.
# See LICENSE.txt for details.

"""
Flex Messaging implementation.

This module contains the message classes used with Flex Data Services.

.. seealso:: `RemoteObject on OSFlash
    <http://osflash.org/documentation/amf3#remoteobject>`_

.. versionadded: 0.1
"""

import uuid

import pyamf

from plasma.flex.messaging.messages import operations

from errors import MessageError, InvalidOperationError, OperationNotImplementedError

__all__ = [
    'AsyncMessage',
    'RemotingMessage',
    'CommandMessage',
    'AcknowledgeMessage',
    'ErrorMessage']

NAMESPACE = 'flex.messaging.messages'

class AbstractMessage(object):
    """
    Abstract base class for all Flex messages.

    Messages have two customizable sections; headers and data. The headers
    property provides access to specialized meta information for a specific
    message instance. The data property contains the instance specific data
    that needs to be delivered and processed by the decoder.

    .. seealso:: `AbstractMessage on Livedocs
        <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AbstractMessage.html>`_

    :ivar body: Specific data that needs to be delivered to the remote
        destination.
    :type body: `mixed`
    :ivar clientId: Indicates which client sent the message.
    :type clientId: `str`
    :ivar destination: Message destination.
    :type destination: `str`
    :ivar headers: Message headers. Core header names start with DS.
    :type headers: `dict`
    :ivar messageId: Unique Message ID.
    :type messageId: `str`
    :ivar timeToLive: How long the message should be considered valid and
        deliverable.
    :type timeToLive: `int`
    :ivar timestamp: Timestamp when the message was generated.
    :type timestamp: `int`
    :ivar context: Message metadata
    :type context: :class:`MessageContext`
    """

    DESTINATION_CLIENT_ID = 'DSDstClientId'

    ENDPOINT = 'DSEndpoint'

    FLEX_CLIENT_ID = 'DSId'

    PRIORTY = 'DSPriority'

    REMOTE_CREDENTIALS = 'DSRemoteCredentials'

    REMOTE_CREDENTIALS_CHARSET = 'DSRemoteCredentialsCharset'

    REQUEST_TIMEOUT = 'DSRequestTimeout'

    STATUS = 'DSStatusCode'

    VALIDATE_ENDPOINT = 'DSValidateEndpoint'

    SUBTOPIC = 'DSSubtopic'

    ERROR_HINT = 'DSErrorHint'

    RETRYABLE_ERROR_HINT = 'DSRetryableErrorHint'

    SELECTOR = 'DSSelector'

    @staticmethod
    def generateId():
        """
        Generates an ID suitable for use as a
        FLEX_CLIENT_ID, clientId, messageId, etc...

        :rtype: str
        """
        return str(uuid.uuid4())


    class __amf__:
        static = ('body', 'clientId', 'destination', 'headers', 'messageId',
            'timestamp', 'timeToLive')

    __slots__ = ['context']
    __slots__.extend(__amf__.static)

    def __init__(self, **kwargs):
        self.body = kwargs.pop('body', None)
        self.clientId = kwargs.pop('clientId', None)
        self.destination = kwargs.pop('destination', None)
        self.headers = kwargs.pop('headers', {})
        self.messageId = kwargs.pop('messageId', None)
        self.timestamp = kwargs.pop('timestamp', None)
        self.timeToLive = kwargs.pop('timeToLive', None)
        self.context = kwargs.pop('context', None)

    def __repr__(self):
        m = '<%s' % self.__class__.__name__

        for k in self.__slots__:
            m += ' %s=%r' % (k, getattr(self, k))

        return m + " />"

    def getSmallMessage(self):
        """
        Return an `ISmallMessage` representation of this object. If one is not
        available, `NotImplementedError` will be raised.
        """
        raise NotImplementedError

    def acknowledge(self, msg):
        """
        Set FLEX_CLIENT_ID, clientId and correlationId
        with values from an existing message.

        :param msg: AbstractMessage to acknowledge
        :type  msg: :class:`AbstractMessage`
        """

        # CorrelationId is == to
        # the messageId of the message
        # being acknowledged.
        self.correlationId = msg.messageId

        # FLEXT_CLIENT_ID identifies
        # a client connection.
        self.headers[self.FLEX_CLIENT_ID] = msg.headers.get(self.FLEX_CLIENT_ID, None) 

        # clientId identifies the
        # individual MessageAgent sending
        # or recieving the message.
        if msg.clientId is None:
            self.clientId = self.generateId()
        else:
            self.clientId = msg.clientId

    def respond(self):
        """
        Invoked when message is received.
        Override in sub-class.

        :raises: :class:`InvalidOperationError`
        """
        raise MessageError("Cannot respond to AbstractMessage.")

class AsyncMessage(AbstractMessage):
    """
    I am the base class for all asynchronous messages.

    .. seealso:: `AsyncMessage on Livedocs
        <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AsyncMessage.html>`_

    :ivar correlationId: Correlation id of the message.
    :type correlationId: `str`
    """

    class __amf__:
        static = ('correlationId',)

    __slots__ = __amf__.static

    def __init__(self, **kwargs):
        AbstractMessage.__init__(self, **kwargs)

        self.correlationId = kwargs.pop('correlationId', None)

    def getSmallMessage(self):
        """
        Return an `ISmallMessage` representation of this async message.
        """
        from plasma.flex.messaging.messages import small

        return small.AsyncMessageExt(self)


class AcknowledgeMessage(AsyncMessage):
    """
    I acknowledge the receipt of a message that was sent previously.

    Every message sent within the messaging system must receive an
    acknowledgement.

    .. seealso:: `AcknowledgeMessage on Livedocs
        <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AcknowledgeMessage.html>`_
    """

    __slots__ = ()

    def getSmallMessage(self):
        """
        Return an ISmallMessage representation of this acknowledge message.
        """
        from plasma.flex.messaging.messages import small

        return small.AcknowledgeMessageExt(self)


class CommandMessage(AsyncMessage):
    """
    Provides a mechanism for sending commands related to publish/subscribe
    messaging, ping, and cluster operations.

    .. seealso:: `CommandMessage on Livedocs
        <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/CommandMessage.html>`_

    :ivar operation: The command
    :type operation: `str`
    :ivar messageRefType: Remote destination belonging to a specific service,
        based upon whether this message type matches the message type the
        service handles.
    :type messageRefType: `str`
    """

    class __amf__:
        static = ('operation',)

    __slots__ = __amf__.static

    def __init__(self, **kwargs):
        AsyncMessage.__init__(self, **kwargs)

        self.operation = kwargs.pop('operation', operations.unknown)

    def getSmallMessage(self):
        """
        Return an C{ISmallMessage} representation of this command message.
        """
        from plasma.flex.messaging.messages import small

        return small.CommandMessageExt(self)

    def respond(self):
        """
        :raises: :class:`InvalidOperationError`

        :rtype: :class:`Deferred`
        """
        if self.operation < 0 or \
            self.operation > len(self.__class__._operation_map):
            raise InvalidOperationError(
                "Invalid command operation: '%s'" % self.operation)

        return self._operation_map[self.operation](self)

    def operationNotImplemented(self):
        """
        Place holder for operations that haven't been implemented yet.
        """
        raise OperationNotImplementedError(
            "Not operation not implemented: '%s'" % self.operation)

    def ping(self):
        """
        Used to test the connectivity over the current channel.
        """
        msg = AcknowledgeMessage()
        msg.acknowledge(self)
        return [msg]

    _operation_map = (
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
        ping,
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
        operationNotImplemented,
    )

class ErrorMessage(AcknowledgeMessage):
    """
    I am the Flex error message to be returned to the client.

    This class is used to report errors within the messaging system.

    :ivar extendedData: Extended data that the remote destination has chosen
        to associate with this error to facilitate custom error processing on
        the client.
    :ivar faultCode: Fault code for the error.
    :type faultCode: `str`
    :ivar faultDetail: Detailed description of what caused the error.
    :ivar faultString: A simple description of the error.
    :ivar rootCause: Should a traceback exist for the error, this property
        contains the message.

    .. seealso:: `ErrorMessage on Livedocs
        http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/ErrorMessage.html`_
    """

    #: If a message may not have been delivered, the faultCode will contain
    #: this constant.
    DELIVERY_IN_DOUBT = "Client.Error.DeliveryInDoubt"

    class __amf__:
        static = ('extendedData', 'faultCode', 'faultDetail', 'faultString',
            'rootCause')

    __slots__ = __amf__.static

    def __init__(self, **kwargs):
        AcknowledgeMessage.__init__(self, **kwargs)

        self.extendedData = kwargs.pop('extendedData', {})
        self.faultCode = kwargs.pop('faultCode', None)
        self.faultDetail = kwargs.pop('faultDetail', None)
        self.faultString = kwargs.pop('faultString', None)
        self.rootCause = kwargs.pop('rootCause', {})

    def getSmallMessage(self):
        raise NotImplementedError


class RemotingMessage(AbstractMessage):
    """
    I am used to send RPC requests to a remote endpoint.

    :ivar operation: Name of the remote method/operation that should be called.
    :ivar source: Name of the service to be called including package name.
        This property is provided for backwards compatibility.

    .. seealso:: `RemotingMessage on Livedocs
        <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/RemotingMessage.html>`_
    """

    class __amf__:
        static = ('operation', 'source')

    __slots__ = __amf__.static

    def __init__(self, **kwargs):
        AbstractMessage.__init__(self, **kwargs)

        self.operation = kwargs.pop('operation', None)
        self.source = kwargs.pop('source', None)


pyamf.register_package(globals(), package=NAMESPACE)
