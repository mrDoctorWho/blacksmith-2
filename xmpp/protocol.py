##   protocol.py
##
##   Copyright (C) 2003-2005 Alexey "Snake" Nezhdanov
##
##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 2, or (at your option)
##   any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.

# $Id: protocol.py, v1.63 2013/12/06 alkorgun Exp $

"""
Protocol module contains tools that is needed for processing of
xmpp-related data structures.
"""

from .simplexml import Node, XML_ls, XMLescape, ustr # ustr might need review for Py3

import time

# XMPP Namespaces (Constants are already PEP 8 compliant)
NS_ACTIVITY = "http://jabber.org/protocol/activity"  # XEP-0108
NS_ADDRESS = "http://jabber.org/protocol/address"  # XEP-0033
NS_ADMIN = "http://jabber.org/protocol/admin"  # XEP-0133
NS_ADMIN_ADD_USER = NS_ADMIN + "#add-user"
NS_ADMIN_DELETE_USER = NS_ADMIN + "#delete-user"
NS_ADMIN_DISABLE_USER = NS_ADMIN + "#disable-user"
NS_ADMIN_REENABLE_USER = NS_ADMIN + "#reenable-user"
NS_ADMIN_END_USER_SESSION = NS_ADMIN + "#end-user-session"
NS_ADMIN_GET_USER_PASSWORD = NS_ADMIN + "#get-user-password"
NS_ADMIN_CHANGE_USER_PASSWORD = NS_ADMIN + "#change-user-password"
NS_ADMIN_GET_USER_ROSTER = NS_ADMIN + "#get-user-roster"
NS_ADMIN_GET_USER_LASTLOGIN = NS_ADMIN + "#get-user-lastlogin"
NS_ADMIN_USER_STATS = NS_ADMIN + "#user-stats"
NS_ADMIN_EDIT_BLACKLIST = NS_ADMIN + "#edit-blacklist"
NS_ADMIN_EDIT_WHITELIST = NS_ADMIN + "#edit-whitelist"
NS_ADMIN_REGISTERED_USERS_NUM = NS_ADMIN + "#get-registered-users-num"
NS_ADMIN_DISABLED_USERS_NUM = NS_ADMIN + "#get-disabled-users-num"
NS_ADMIN_ONLINE_USERS_NUM = NS_ADMIN + "#get-online-users-num"
NS_ADMIN_ACTIVE_USERS_NUM = NS_ADMIN + "#get-active-users-num"
NS_ADMIN_IDLE_USERS_NUM = NS_ADMIN + "#get-idle-users-num"
NS_ADMIN_REGISTERED_USERS_LIST = NS_ADMIN + "#get-registered-users-list"
NS_ADMIN_DISABLED_USERS_LIST = NS_ADMIN + "#get-disabled-users-list"
NS_ADMIN_ONLINE_USERS_LIST = NS_ADMIN + "#get-online-users-list"
NS_ADMIN_ACTIVE_USERS_LIST = NS_ADMIN + "#get-active-users-list"
NS_ADMIN_IDLE_USERS_LIST = NS_ADMIN + "#get-idle-users-list"
NS_ADMIN_ANNOUNCE = NS_ADMIN + "#announce"
NS_ADMIN_SET_MOTD = NS_ADMIN + "#set-motd"
NS_ADMIN_EDIT_MOTD = NS_ADMIN + "#edit-motd"
NS_ADMIN_DELETE_MOTD = NS_ADMIN + "#delete-motd"
NS_ADMIN_SET_WELCOME = NS_ADMIN + "#set-welcome"
NS_ADMIN_DELETE_WELCOME = NS_ADMIN + "#delete-welcome"
NS_ADMIN_EDIT_ADMIN = NS_ADMIN + "#edit-admin"
NS_ADMIN_RESTART = NS_ADMIN + "#restart"
NS_ADMIN_SHUTDOWN = NS_ADMIN + "#shutdown"
NS_AGENTS = "jabber:iq:agents"  # XEP-0094 (historical)
NS_AMP = "http://jabber.org/protocol/amp"  # XEP-0079
NS_AMP_ERRORS = NS_AMP + "#errors"  # XEP-0079
NS_AUTH = "jabber:iq:auth"  # XEP-0078
NS_AVATAR = "jabber:iq:avatar"  # XEP-0008 (historical)
NS_BIND = "urn:ietf:params:xml:ns:xmpp-bind"  # RFC 3920
NS_BROWSE = "jabber:iq:browse"  # XEP-0011 (historical)
NS_BYTESTREAM = "http://jabber.org/protocol/bytestreams"  # XEP-0065
NS_CAPS = "http://jabber.org/protocol/caps"  # XEP-0115
NS_CAPTCHA = "urn:xmpp:captcha"  # XEP-0158
NS_CHATSTATES = "http://jabber.org/protocol/chatstates"  # XEP-0085
NS_CLIENT = "jabber:client"  # RFC 3921
NS_COMMANDS = "http://jabber.org/protocol/commands"  # XEP-0050
NS_COMPONENT_ACCEPT = "jabber:component:accept"  # XEP-0114
NS_COMPONENT_1 = "http://jabberd.jabberstudio.org/ns/component/1.0"  # Jabberd2
NS_COMPRESS = "http://jabber.org/protocol/compress"  # XEP-0138
NS_DATA = "jabber:x:data"  # XEP-0004
NS_DATA_LAYOUT = "http://jabber.org/protocol/xdata-layout"  # XEP-0141
NS_DATA_VALIDATE = "http://jabber.org/protocol/xdata-validate"  # XEP-0122
NS_DELAY = "jabber:x:delay"  # XEP-0091 (deprecated)
NS_DIALBACK = "jabber:server:dialback"  # RFC 3921
NS_DISCO = "http://jabber.org/protocol/disco"  # XEP-0030
NS_DISCO_INFO = NS_DISCO + "#info"  # XEP-0030
NS_DISCO_ITEMS = NS_DISCO + "#items"  # XEP-0030
NS_ENCRYPTED = "jabber:x:encrypted"  # XEP-0027
NS_EVENT = "jabber:x:event"  # XEP-0022 (deprecated)
NS_FEATURE = "http://jabber.org/protocol/feature-neg"  # XEP-0020
NS_FILE = "http://jabber.org/protocol/si/profile/file-transfer"  # XEP-0096
NS_GATEWAY = "jabber:iq:gateway"  # XEP-0100
NS_GEOLOC = "http://jabber.org/protocol/geoloc"  # XEP-0080
NS_GROUPCHAT = "gc-1.0"  # XEP-0045
NS_HTTP_BIND = "http://jabber.org/protocol/httpbind"  # XEP-0124
NS_IBB = "http://jabber.org/protocol/ibb"  # XEP-0047
NS_INVISIBLE = "presence-invisible"  # Jabberd2
NS_IQ = "iq"  # Jabberd2
NS_LAST = "jabber:iq:last"  # XEP-0012
NS_MEDIA = "urn:xmpp:media-element"  # XEP-0158
NS_MESSAGE = "message"  # Jabberd2
NS_MOOD = "http://jabber.org/protocol/mood"  # XEP-0107
NS_MUC = "http://jabber.org/protocol/muc"  # XEP-0045
NS_MUC_ADMIN = NS_MUC + "#admin"  # XEP-0045
NS_MUC_OWNER = NS_MUC + "#owner"  # XEP-0045
NS_MUC_UNIQUE = NS_MUC + "#unique"  # XEP-0045
NS_MUC_USER = NS_MUC + "#user"  # XEP-0045
NS_MUC_REGISTER = NS_MUC + "#register"  # XEP-0045
NS_MUC_REQUEST = NS_MUC + "#request"  # XEP-0045
NS_MUC_ROOMCONFIG = NS_MUC + "#roomconfig"  # XEP-0045
NS_MUC_ROOMINFO = NS_MUC + "#roominfo"  # XEP-0045
NS_MUC_ROOMS = NS_MUC + "#rooms"  # XEP-0045
NS_MUC_TRAFIC = NS_MUC + "#traffic"  # XEP-0045
NS_NICK = "http://jabber.org/protocol/nick"  # XEP-0172
NS_OFFLINE = "http://jabber.org/protocol/offline"  # XEP-0013
NS_PHYSLOC = "http://jabber.org/protocol/physloc"  # XEP-0112
NS_PRESENCE = "presence"  # Jabberd2
NS_PRIVACY = "jabber:iq:privacy"  # RFC 3921
NS_PRIVATE = "jabber:iq:private"  # XEP-0049
NS_PUBSUB = "http://jabber.org/protocol/pubsub"  # XEP-0060
NS_REGISTER = "jabber:iq:register"  # XEP-0077
NS_RC = "http://jabber.org/protocol/rc"  # XEP-0146
NS_ROSTER = "jabber:iq:roster"  # RFC 3921
NS_ROSTERX = "http://jabber.org/protocol/rosterx"  # XEP-0144
NS_RPC = "jabber:iq:rpc"  # XEP-0009
NS_SASL = "urn:ietf:params:xml:ns:xmpp-sasl"  # RFC 3920
NS_SEARCH = "jabber:iq:search"  # XEP-0055
NS_SERVER = "jabber:server"  # RFC 3921
NS_SESSION = "urn:ietf:params:xml:ns:xmpp-session"  # RFC 3921
NS_SI = "http://jabber.org/protocol/si"  # XEP-0096
NS_SI_PUB = "http://jabber.org/protocol/sipub"  # XEP-0137
NS_SIGNED = "jabber:x:signed"  # XEP-0027
NS_STANZAS = "urn:ietf:params:xml:ns:xmpp-stanzas"  # RFC 3920
NS_STREAMS = "http://etherx.jabber.org/streams"  # RFC 3920
NS_TIME = "jabber:iq:time"  # XEP-0090 (deprecated)
NS_TLS = "urn:ietf:params:xml:ns:xmpp-tls"  # RFC 3920
NS_VACATION = "http://jabber.org/protocol/vacation"  # XEP-0109
NS_VCARD = "vcard-temp"  # XEP-0054
NS_VCARD_UPDATE = "vcard-temp:x:update"  # XEP-0153
NS_VERSION = "jabber:iq:version"  # XEP-0092
NS_WAITINGLIST = "http://jabber.org/protocol/waitinglist"  # XEP-0130
NS_XHTML_IM = "http://jabber.org/protocol/xhtml-im"  # XEP-0071
NS_XMPP_STREAMS = "urn:ietf:params:xml:ns:xmpp-streams"  # RFC 3920
NS_STATS = "http://jabber.org/protocol/stats"  # XEP-0039
NS_PING = "urn:xmpp:ping"  # XEP-0199
NS_MUC_FILTER = "http://jabber.ru/muc-filter"
NS_URN_TIME = "urn:xmpp:time"  # XEP-0202
NS_RECEIPTS = "urn:xmpp:receipts"  # XEP-0184
NS_OOB = "jabber:x:oob"  # XEP-0066
NS_URN_ATTENTION = "urn:xmpp:attention:0"  # XEP-0224
NS_URN_OOB = "urn:xmpp:bob"  # XEP-0158

# Stream Error Conditions (Constants are already PEP 8 compliant)
STREAM_NOT_AUTHORIZED = NS_XMPP_STREAMS + " not-authorized"
STREAM_REMOTE_CONNECTION_FAILED = NS_XMPP_STREAMS + " remote-connection-failed"
SASL_MECHANISM_TOO_WEAK = NS_SASL + " mechanism-too-weak"
STREAM_XML_NOT_WELL_FORMED = NS_XMPP_STREAMS + " xml-not-well-formed"
ERR_JID_MALFORMED = NS_STANZAS + " jid-malformed"
STREAM_SEE_OTHER_HOST = NS_XMPP_STREAMS + " see-other-host"
STREAM_BAD_NAMESPACE_PREFIX = NS_XMPP_STREAMS + " bad-namespace-prefix"
ERR_SERVICE_UNAVAILABLE = NS_STANZAS + " service-unavailable"
STREAM_CONNECTION_TIMEOUT = NS_XMPP_STREAMS + " connection-timeout"
STREAM_UNSUPPORTED_VERSION = NS_XMPP_STREAMS + " unsupported-version"
STREAM_IMPROPER_ADDRESSING = NS_XMPP_STREAMS + " improper-addressing"
STREAM_UNDEFINED_CONDITION = NS_XMPP_STREAMS + " undefined-condition"
SASL_NOT_AUTHORIZED = NS_SASL + " not-authorized"
ERR_GONE = NS_STANZAS + " gone"
SASL_TEMPORARY_AUTH_FAILURE = NS_SASL + " temporary-auth-failure"
ERR_REMOTE_SERVER_NOT_FOUND = NS_STANZAS + " remote-server-not-found"
ERR_UNEXPECTED_REQUEST = NS_STANZAS + " unexpected-request"
ERR_RECIPIENT_UNAVAILABLE = NS_STANZAS + " recipient-unavailable"
ERR_CONFLICT = NS_STANZAS + " conflict"
STREAM_SYSTEM_SHUTDOWN = NS_XMPP_STREAMS + " system-shutdown"
STREAM_BAD_FORMAT = NS_XMPP_STREAMS + " bad-format"
ERR_SUBSCRIPTION_REQUIRED = NS_STANZAS + " subscription-required"
STREAM_INTERNAL_SERVER_ERROR = NS_XMPP_STREAMS + " internal-server-error"
ERR_NOT_AUTHORIZED = NS_STANZAS + " not-authorized"
SASL_ABORTED = NS_SASL + " aborted"
ERR_REGISTRATION_REQUIRED = NS_STANZAS + " registration-required"
ERR_INTERNAL_SERVER_ERROR = NS_STANZAS + " internal-server-error"
SASL_INCORRECT_ENCODING = NS_SASL + " incorrect-encoding"
STREAM_HOST_GONE = NS_XMPP_STREAMS + " host-gone"
STREAM_POLICY_VIOLATION = NS_XMPP_STREAMS + " policy-violation"
STREAM_INVALID_XML = NS_XMPP_STREAMS + " invalid-xml"
STREAM_CONFLICT = NS_XMPP_STREAMS + " conflict"
STREAM_RESOURCE_CONSTRAINT = NS_XMPP_STREAMS + " resource-constraint"
STREAM_UNSUPPORTED_ENCODING = NS_XMPP_STREAMS + " unsupported-encoding"
ERR_NOT_ALLOWED = NS_STANZAS + " not-allowed"
ERR_ITEM_NOT_FOUND = NS_STANZAS + " item-not-found"
ERR_NOT_ACCEPTABLE = NS_STANZAS + " not-acceptable"
STREAM_INVALID_FROM = NS_XMPP_STREAMS + " invalid-from"
ERR_FEATURE_NOT_IMPLEMENTED = NS_STANZAS + " feature-not-implemented"
ERR_BAD_REQUEST = NS_STANZAS + " bad-request"
STREAM_INVALID_ID = NS_XMPP_STREAMS + " invalid-id"
STREAM_HOST_UNKNOWN = NS_XMPP_STREAMS + " host-unknown"
ERR_UNDEFINED_CONDITION = NS_STANZAS + " undefined-condition"
SASL_INVALID_MECHANISM = NS_SASL + " invalid-mechanism"
STREAM_RESTRICTED_XML = NS_XMPP_STREAMS + " restricted-xml"
ERR_RESOURCE_CONSTRAINT = NS_STANZAS + " resource-constraint"
ERR_REMOTE_SERVER_TIMEOUT = NS_STANZAS + " remote-server-timeout"
SASL_INVALID_AUTHZID = NS_SASL + " invalid-authzid"
ERR_PAYMENT_REQUIRED = NS_STANZAS + " payment-required"
STREAM_INVALID_NAMESPACE = NS_XMPP_STREAMS + " invalid-namespace"
ERR_REDIRECT = NS_STANZAS + " redirect"
STREAM_UNSUPPORTED_STANZA_TYPE = NS_XMPP_STREAMS + " unsupported-stanza-type"
ERR_FORBIDDEN = NS_STANZAS + " forbidden"

ERROR_CONDITIONS_MAP = { # Renamed ERRORS
	"urn:ietf:params:xml:ns:xmpp-sasl not-authorized": ["", "", "The authentication failed because the initiating entity did not provide valid credentials (this includes but is not limited to the case of an unknown username); sent in reply to a <response/> element or an <auth/> element with initial response data."],
	"urn:ietf:params:xml:ns:xmpp-stanzas payment-required": ["402", "auth", "The requesting entity is not authorized to access the requested service because payment is required."],
	"urn:ietf:params:xml:ns:xmpp-sasl mechanism-too-weak": ["", "", "The mechanism requested by the initiating entity is weaker than server policy permits for that initiating entity; sent in reply to a <response/> element or an <auth/> element with initial response data."],
	"urn:ietf:params:xml:ns:xmpp-streams unsupported-encoding": ["", "", "The initiating entity has encoded the stream in an encoding that is not supported by the server."],
	"urn:ietf:params:xml:ns:xmpp-stanzas remote-server-timeout": ["504", "wait", "A remote server or service specified as part or all of the JID of the intended recipient could not be contacted within a reasonable amount of time."],
	"urn:ietf:params:xml:ns:xmpp-streams remote-connection-failed": ["", "", "The server is unable to properly connect to a remote resource that is required for authentication or authorization."],
	"urn:ietf:params:xml:ns:xmpp-streams restricted-xml": ["", "", "The entity has attempted to send restricted XML features such as a comment, processing instruction, DTD, entity reference, or unescaped character."],
	"urn:ietf:params:xml:ns:xmpp-streams see-other-host": ["", "", "The server will not provide service to the initiating entity but is redirecting traffic to another host."],
	"urn:ietf:params:xml:ns:xmpp-streams xml-not-well-formed": ["", "", "The initiating entity has sent XML that is not well-formed."],
	"urn:ietf:params:xml:ns:xmpp-stanzas subscription-required": ["407", "auth", "The requesting entity is not authorized to access the requested service because a subscription is required."],
	"urn:ietf:params:xml:ns:xmpp-streams internal-server-error": ["", "", "The server has experienced a misconfiguration or an otherwise-undefined internal error that prevents it from servicing the stream."],
	"urn:ietf:params:xml:ns:xmpp-sasl invalid-mechanism": ["", "", "The initiating entity did not provide a mechanism or requested a mechanism that is not supported by the receiving entity; sent in reply to an <auth/> element."],
	"urn:ietf:params:xml:ns:xmpp-streams policy-violation": ["", "", "The entity has violated some local service policy."],
	"urn:ietf:params:xml:ns:xmpp-stanzas conflict": ["409", "cancel", "Access cannot be granted because an existing resource or session exists with the same name or address."],
	"urn:ietf:params:xml:ns:xmpp-streams unsupported-stanza-type": ["", "", "The initiating entity has sent a first-level child of the stream that is not supported by the server."],
	"urn:ietf:params:xml:ns:xmpp-sasl incorrect-encoding": ["", "", "The data provided by the initiating entity could not be processed because the [BASE64]Josefsson, S., The Base16, Base32, and Base64 Data Encodings, July 2003. encoding is incorrect (e.g., because the encoding does not adhere to the definition in Section 3 of [BASE64]Josefsson, S., The Base16, Base32, and Base64 Data Encodings, July 2003.); sent in reply to a <response/> element or an <auth/> element with initial response data."],
	"urn:ietf:params:xml:ns:xmpp-stanzas registration-required": ["407", "auth", "The requesting entity is not authorized to access the requested service because registration is required."],
	"urn:ietf:params:xml:ns:xmpp-streams invalid-id": ["", "", "The stream ID or dialback ID is invalid or does not match an ID previously provided."],
	"urn:ietf:params:xml:ns:xmpp-sasl invalid-authzid": ["", "", "The authzid provided by the initiating entity is invalid, either because it is incorrectly formatted or because the initiating entity does not have permissions to authorize that ID; sent in reply to a <response/> element or an <auth/> element with initial response data."],
	"urn:ietf:params:xml:ns:xmpp-stanzas bad-request": ["400", "modify", "The sender has sent XML that is malformed or that cannot be processed."],
	"urn:ietf:params:xml:ns:xmpp-streams not-authorized": ["", "", "The entity has attempted to send data before the stream has been authenticated, or otherwise is not authorized to perform an action related to stream negotiation."],
	"urn:ietf:params:xml:ns:xmpp-stanzas forbidden": ["403", "auth", "The requesting entity does not possess the required permissions to perform the action."],
	"urn:ietf:params:xml:ns:xmpp-sasl temporary-auth-failure": ["", "", "The authentication failed because of a temporary error condition within the receiving entity; sent in reply to an <auth/> element or <response/> element."],
	"urn:ietf:params:xml:ns:xmpp-streams invalid-namespace": ["", "", "The streams namespace name is something other than \http://etherx.jabber.org/streams\" or the dialback namespace name is something other than \"jabber:server:dialback\"."],
	"urn:ietf:params:xml:ns:xmpp-stanzas feature-not-implemented": ["501", "cancel", "The feature requested is not implemented by the recipient or server and therefore cannot be processed."],
	"urn:ietf:params:xml:ns:xmpp-streams invalid-xml": ["", "", "The entity has sent invalid XML over the stream to a server that performs validation."],
	"urn:ietf:params:xml:ns:xmpp-stanzas item-not-found": ["404", "cancel", "The addressed JID or item requested cannot be found."],
	"urn:ietf:params:xml:ns:xmpp-streams host-gone": ["", "", "The value of the \"to\" attribute provided by the initiating entity in the stream header corresponds to a hostname that is no longer hosted by the server."],
	"urn:ietf:params:xml:ns:xmpp-stanzas recipient-unavailable": ["404", "wait", "The intended recipient is temporarily unavailable."],
	"urn:ietf:params:xml:ns:xmpp-stanzas not-acceptable": ["406", "cancel", "The recipient or server understands the request but is refusing to process it because it does not meet criteria defined by the recipient or server."],
	"urn:ietf:params:xml:ns:xmpp-streams invalid-from": ["cancel", "", "The JID or hostname provided in a \"from\" address does not match an authorized JID or validated domain negotiated between servers via SASL or dialback, or between a client and a server via authentication and resource authorization."],
	"urn:ietf:params:xml:ns:xmpp-streams bad-format": ["", "", "The entity has sent XML that cannot be processed."],
	"urn:ietf:params:xml:ns:xmpp-streams resource-constraint": ["", "", "The server lacks the system resources necessary to service the stream."],
	"urn:ietf:params:xml:ns:xmpp-stanzas undefined-condition": ["500", "", ""],
	"urn:ietf:params:xml:ns:xmpp-stanzas redirect": ["302", "modify", "The recipient or server is redirecting requests for this information to another entity."],
	"urn:ietf:params:xml:ns:xmpp-streams bad-namespace-prefix": ["", "", "The entity has sent a namespace prefix that is unsupported, or has sent no namespace prefix on an element that requires such a prefix."],
	"urn:ietf:params:xml:ns:xmpp-streams system-shutdown": ["", "", "The server is being shut down and all active streams are being closed."],
	"urn:ietf:params:xml:ns:xmpp-streams conflict": ["", "", "The server is closing the active stream for this entity because a new stream has been initiated that conflicts with the existing stream."],
	"urn:ietf:params:xml:ns:xmpp-streams connection-timeout": ["", "", "The entity has not generated any traffic over the stream for some period of time."],
	"urn:ietf:params:xml:ns:xmpp-stanzas jid-malformed": ["400", "modify", "The value of the \"to\" attribute in the sender's stanza does not adhere to the syntax defined in Addressing Scheme."],
	"urn:ietf:params:xml:ns:xmpp-stanzas resource-constraint": ["500", "wait", "The server or recipient lacks the system resources necessary to service the request."],
	"urn:ietf:params:xml:ns:xmpp-stanzas remote-server-not-found": ["404", "cancel", "A remote server or service specified as part or all of the JID of the intended recipient does not exist."],
	"urn:ietf:params:xml:ns:xmpp-streams unsupported-version": ["", "", "The value of the \"version\" attribute provided by the initiating entity in the stream header specifies a version of XMPP that is not supported by the server."],
	"urn:ietf:params:xml:ns:xmpp-streams host-unknown": ["", "", "The value of the \"to\" attribute provided by the initiating entity in the stream header does not correspond to a hostname that is hosted by the server."],
	"urn:ietf:params:xml:ns:xmpp-stanzas unexpected-request": ["400", "wait", "The recipient or server understood the request but was not expecting it at this time (e.g., the request was out of order)."],
	"urn:ietf:params:xml:ns:xmpp-streams improper-addressing": ["", "", "A stanza sent between two servers lacks a \"to\" or \"from\" attribute (or the attribute has no value)."],
	"urn:ietf:params:xml:ns:xmpp-stanzas not-allowed": ["405", "cancel", "The recipient or server does not allow any entity to perform the action."],
	"urn:ietf:params:xml:ns:xmpp-stanzas internal-server-error": ["500", "wait", "The server could not process the stanza because of a misconfiguration or an otherwise-undefined internal server error."],
	"urn:ietf:params:xml:ns:xmpp-stanzas gone": ["302", "modify", "The recipient or server can no longer be contacted at this address."],
	"urn:ietf:params:xml:ns:xmpp-streams undefined-condition": ["", "", "The error condition is not one of those defined by the other conditions in this list."],
	"urn:ietf:params:xml:ns:xmpp-stanzas service-unavailable": ["503", "cancel", "The server or recipient does not currently provide the requested service."],
	"urn:ietf:params:xml:ns:xmpp-stanzas not-authorized": ["401", "auth", "The sender must provide proper credentials before being allowed to perform the action, or has provided improper credentials."],
	"urn:ietf:params:xml:ns:xmpp-sasl aborted": ["", "", "The receiving entity acknowledges an <abort/> element sent by the initiating entity; sent in reply to the <abort/> element."]
}

_ERROR_CODE_TO_CONDITION_MAP = { # Renamed _errorcodes
	"302": "redirect",
	"400": "unexpected-request",
	"401": "not-authorized",
	"402": "payment-required",
	"403": "forbidden",
	"404": "remote-server-not-found",
	"405": "not-allowed",
	"406": "not-acceptable",
	"407": "subscription-required",
	"409": "conflict",
	"500": "undefined-condition",
	"501": "feature-not-implemented",
	"503": "service-unavailable",
	"504": "remote-server-timeout"
}

def is_result_node(node_obj): # Renamed isResultNode, node
	"""
	Returns true if the node is a positive reply.
	"""
	return (node_obj and node_obj.getType() == "result")

def is_get_node(node_obj): # Renamed isGetNode, node
	"""
	Returns true if the node is a positive reply.
	"""
	return (node_obj and node_obj.getType() == "get")

def is_set_node(node_obj): # Renamed isSetNode, node
	"""
	Returns true if the node is a positive reply.
	"""
	return (node_obj and node_obj.getType() == "set")

def is_error_node(node_obj): # Renamed isErrorNode, node
	"""
	Returns true if the node is a negative reply.
	"""
	return (node_obj and node_obj.getType() == "error")

class NodeProcessed(Exception):
	"""
	Exception that should be raised by handler when the handling should be stopped.
	"""

class StreamError(Exception):
	"""
	Base exception class for stream errors.
	"""

class BadFormatError(StreamError): pass # Renamed BadFormat
class BadNamespacePrefixError(StreamError): pass # Renamed BadNamespacePrefix
class ConflictError(StreamError): pass # Renamed Conflict
class ConnectionTimeoutError(StreamError): pass # Renamed ConnectionTimeout
class HostGoneError(StreamError): pass # Renamed HostGone
class HostUnknownError(StreamError): pass # Renamed HostUnknown
class ImproperAddressingError(StreamError): pass # Renamed ImproperAddressing
class InternalServerErrorError(StreamError): pass # Renamed InternalServerError (avoid double "Error" if base is Error)
class InvalidFromError(StreamError): pass # Renamed InvalidFrom
class InvalidIdError(StreamError): pass # Renamed InvalidID
class InvalidNamespaceError(StreamError): pass # Renamed InvalidNamespace
class InvalidXmlError(StreamError): pass # Renamed InvalidXML
class NotAuthorizedError(StreamError): pass # Renamed NotAuthorized
class PolicyViolationError(StreamError): pass # Renamed PolicyViolation
class RemoteConnectionFailedError(StreamError): pass # Renamed RemoteConnectionFailed
class ResourceConstraintError(StreamError): pass # Renamed ResourceConstraint
class RestrictedXmlError(StreamError): pass # Renamed RestrictedXML
class SeeOtherHostError(StreamError): pass # Renamed SeeOtherHost
class SystemShutdownError(StreamError): pass # Renamed SystemShutdown
class UndefinedConditionError(StreamError): pass # Renamed UndefinedCondition
class UnsupportedEncodingError(StreamError): pass # Renamed UnsupportedEncoding
class UnsupportedStanzaTypeError(StreamError): pass # Renamed UnsupportedStanzaType
class UnsupportedVersionError(StreamError): pass # Renamed UnsupportedVersion
class XmlNotWellFormedError(StreamError): pass # Renamed XMLNotWellFormed

STREAM_ERROR_EXCEPTION_MAP = { # Renamed stream_exceptions
	"bad-format": BadFormatError,
	"bad-namespace-prefix": BadNamespacePrefixError,
	"conflict": ConflictError,
	"connection-timeout": ConnectionTimeoutError,
	"host-gone": HostGoneError,
	"host-unknown": HostUnknownError,
	"improper-addressing": ImproperAddressingError,
	"internal-server-error": InternalServerErrorError,
	"invalid-from": InvalidFromError,
	"invalid-id": InvalidIdError,
	"invalid-namespace": InvalidNamespaceError,
	"invalid-xml": InvalidXmlError,
	"not-authorized": NotAuthorizedError,
	"policy-violation": PolicyViolationError,
	"remote-connection-failed": RemoteConnectionFailedError,
	"resource-constraint": ResourceConstraintError,
	"restricted-xml": RestrictedXmlError,
	"see-other-host": SeeOtherHostError,
	"system-shutdown": SystemShutdownError,
	"undefined-condition": UndefinedConditionError,
	"unsupported-encoding": UnsupportedEncodingError,
	"unsupported-stanza-type": UnsupportedStanzaTypeError,
	"unsupported-version": UnsupportedVersionError,
	"xml-not-well-formed": XmlNotWellFormedError
}

class Jid(object): # Renamed JID
	"""
	JID object. JID can be built from string, modified, compared, serialized into string.
	"""
	def __init__(self, jid_str_or_obj=None, node_str="", domain_str="", resource_str=""): # Renamed jid, node, domain, resource
		"""
		Constructor. JID can be specified as string (jid_str_or_obj argument) or as separate parts.
		Examples:
		Jid("node@domain/resource")
		Jid(node_str="node", domain_str="domain.org")
		"""
		if not jid_str_or_obj and not domain_str:
			raise ValueError("JID must contain at least domain name")
		elif isinstance(jid_str_or_obj, self.__class__):
			self.node, self.domain, self.resource = jid_str_or_obj.node, jid_str_or_obj.domain, jid_str_or_obj.resource
		elif domain_str: # Parts provided
			self.node, self.domain, self.resource = node_str, domain_str, resource_str
		else: # String JID provided
			temp_jid_str = jid_str_or_obj # Renamed jid
			if "@" in temp_jid_str: # Use in operator
				self.node, temp_jid_str = temp_jid_str.split("@", 1)
			else:
				self.node = ""
			if "/" in temp_jid_str: # Use in operator
				self.domain, self.resource = temp_jid_str.split("/", 1)
			else:
				self.domain, self.resource = temp_jid_str, ""

	def get_node(self): # Renamed getNode
		"""
		Return the node part of the JID.
		"""
		return self.node

	def set_node(self, node_str): # Renamed setNode, node
		"""
		Set the node part of the JID to new value. Specify None to remove the node part.
		"""
		self.node = node_str.lower() if node_str else "" # Ensure node is string or empty

	def get_domain(self): # Renamed getDomain
		"""
		Return the domain part of the JID.
		"""
		return self.domain

	def set_domain(self, domain_str): # Renamed setDomain, domain
		"""
		Set the domain part of the JID to new value.
		"""
		if not domain_str: # Domain cannot be empty
			raise ValueError("JID domain cannot be empty")
		self.domain = domain_str.lower()

	def get_resource(self): # Renamed getResource
		"""
		Return the resource part of the JID.
		"""
		return self.resource

	def set_resource(self, resource_str): # Renamed setResource, resource
		"""
		Set the resource part of the JID to new value. Specify None to remove the resource part.
		"""
		self.resource = resource_str if resource_str else "" # Ensure resource is string or empty

	def get_stripped_jid(self): # Renamed getStripped
		"""
		Return the bare representation of JID. I.e. string value w/o resource.
		"""
		return self.__str__(include_resource=False) # Renamed wresource

	def __eq__(self, other_jid): # Renamed other
		"""
		Compare the JID to another instance or to string for equality.
		"""
		try:
			if not isinstance(other_jid, self.__class__):
				other_jid = Jid(other_jid) # Convert if not already Jid object
		except ValueError:
			return False # Cannot be parsed as JID
		return self.resource == other_jid.resource and self.node == other_jid.node and self.domain == other_jid.domain

	def __ne__(self, other_jid): # Renamed other
		"""
		Compare the JID to another instance or to string for non-equality.
		"""
		return not self.__eq__(other_jid)

	def bare_match(self, other_jid): # Renamed bareMatch
		"""
		Compare the node and domain parts of the JID's for equality.
		"""
		try:
			if not isinstance(other_jid, self.__class__):
				other_jid = Jid(other_jid)
		except ValueError:
			return False
		return self.node == other_jid.node and self.domain == other_jid.domain

	def __str__(self, include_resource=True): # Renamed wresource
		"""
		Serialize JID into string.
		"""
		jid_parts = []
		if self.node:
			jid_parts.append(self.node)
			jid_parts.append("@")
		jid_parts.append(self.domain)

		jid_string = "".join(jid_parts)

		if include_resource and self.resource:
			jid_string = "/".join((jid_string, self.resource))
		return jid_string

	def __hash__(self):
		"""
		Produce hash of the JID, Allows to use JID objects as keys of the dictionary.
		"""
		return hash(self.__str__(include_resource=True)) # Hash full JID

class Stanza(Node): # Renamed Protocol
	"""
	A "stanza" object class. Contains methods that are common for presences, iqs and messages.
	"""
	def __init__(self, name=None, to_jid=None, stanza_type=None, from_jid=None, attrs_dict={}, payload_list=[], timestamp_str=None, xmlns_str=None, source_node=None): # Renamed params
		"""
		Constructor, name is the name of the stanza i.e. "message" or "presence" or "iq".
		"""
		if not attrs_dict: # Ensure attrs_dict is a dict
			attrs_dict = {}
		if to_jid:
			attrs_dict["to"] = str(to_jid) # Ensure JID is string for attr
		if from_jid:
			attrs_dict["from"] = str(from_jid) # Ensure JID is string for attr
		if stanza_type:
			attrs_dict["type"] = stanza_type

		Node.__init__(self, tag=name, attrs=attrs_dict, payload=payload_list, node=source_node)

		if not source_node and xmlns_str:
			self.setNamespace(xmlns_str)
		if self.getAttr("to"): # Check if attribute exists
			self.set_to(self.getAttr("to")) # Use new method name
		if self.getAttr("from"):
			self.set_from(self.getAttr("from")) # Use new method name

		# Prevent ID copying when creating a reply from another stanza of the same type
		if source_node and isinstance(source_node, self.__class__) and self.__class__ == source_node.__class__ and "id" in self.attrs:
			del self.attrs["id"]

		self.timestamp = None # Initialize timestamp attribute
		# Try to find an existing delay tag
		for delay_tag_node in self.getTags("x", namespace=NS_DELAY): # Renamed x to delay_tag_node
			try:
				stamp_attr = delay_tag_node.getAttr("stamp")
				if not self.get_timestamp() or stamp_attr < self.get_timestamp(): # Use new method name
					self.set_timestamp(stamp_attr) # Use new method name
			except Exception: # Catch more specific errors if possible
				pass
		if timestamp_str is not None: # Allow explicit timestamp setting
			self.set_timestamp(timestamp_str) # Use new method name

	def get_to(self): # Renamed getTo
		""" Return value of the "to" attribute as a Jid object or None. """
		to_attr = self.getAttr("to")
		return Jid(to_attr) if to_attr else None

	def get_from(self): # Renamed getFrom
		""" Return value of the "from" attribute as a Jid object or None. """
		from_attr = self.getAttr("from")
		return Jid(from_attr) if from_attr else None

	def get_timestamp(self): # Renamed getTimestamp
		""" Return the timestamp in the "yyyymmddThhmmss" format. """
		return self.timestamp

	def get_id(self): # Renamed getID
		""" Return the value of the "id" attribute. """
		return self.getAttr("id")

	def set_to(self, jid_val): # Renamed setTo, val
		""" Set the value of the "to" attribute. """
		self.setAttr("to", str(Jid(jid_val))) # Ensure Jid object and convert to string

	def get_type(self): # Renamed getType
		""" Return the value of the "type" attribute. """
		return self.getAttr("type")

	def set_from(self, jid_val): # Renamed setFrom, val
		""" Set the value of the "from" attribute. """
		self.setAttr("from", str(Jid(jid_val))) # Ensure Jid object and convert to string

	def set_type(self, type_val): # Renamed setType, val
		""" Set the value of the "type" attribute. """
		self.setAttr("type", type_val)

	def set_id(self, id_val): # Renamed setID, val
		""" Set the value of the "id" attribute. """
		self.setAttr("id", id_val)

	def get_error_condition_node(self): # Renamed getError
		""" Return the error condition Node (if present) or None. """
		error_tag_node = self.getTag("error") # Renamed errtag
		if error_tag_node:
			for child_node in error_tag_node.getChildren(): # Renamed tag
				# The first child that is not 'text' is the condition
				if child_node.getNameSpace() != NS_STANZAS and child_node.getName() != "text": # Check NS too
					return child_node
			# Fallback for older error text if no specific condition tag found
			error_text_data = error_tag_node.getData()
			if error_text_data: return Node(tag="text", payload=[error_text_data]) # Wrap in a node for consistency
		return None

	def get_error_text(self):
		""" Returns the human-readable error text, if any. """
		error_tag_node = self.getTag("error")
		if error_tag_node:
			text_node = error_tag_node.getTag("text", namespace=NS_STANZAS) # Standard error text namespace
			if text_node:
				return text_node.getData()
			# Fallback for non-namespaced or older text if any
			return error_tag_node.getData() # This might get the condition if no specific text tag
		return None

	def get_error_code(self): # Renamed getErrorCode
		""" Return the error code (legacy). """
		return self.getTagAttr("error", "code")

	def set_error(self, error_condition_node_or_name, legacy_code_str=None): # Renamed setError, error, code
		"""
		Set the error. error_condition_node_or_name can be an ErrorNode or a string name of the condition.
		"""
		if isinstance(error_condition_node_or_name, str):
			# If legacy_code_str is provided, try to use it for older style error
			if legacy_code_str and str(legacy_code_str) in _ERROR_CODE_TO_CONDITION_MAP:
				# This path seems to create an error based on a numeric code and a text message
				# It's a bit confusing as error_condition_node_or_name would be the text here.
				error_node_obj = XMPPErrorNode(_ERROR_CODE_TO_CONDITION_MAP[str(legacy_code_str)],
											   code=legacy_code_str,
											   typ="cancel", # Default type
											   text=error_condition_node_or_name)
			else: # Create error from condition name string
				error_node_obj = XMPPErrorNode(error_condition_node_or_name)
		elif isinstance(error_condition_node_or_name, Node): # Assume it's an ErrorNode or similar
			error_node_obj = error_condition_node_or_name
		else:
			raise TypeError("error argument must be a string condition name or an ErrorNode instance")

		self.set_type("error")
		# Ensure only one error child
		existing_error_node = self.getTag("error")
		if existing_error_node:
			self.delChild(existing_error_node)
		self.addChild(node=error_node_obj)


	def set_timestamp(self, timestamp_val_str=None): # Renamed setTimestamp, val
		"""
		Set the timestamp. timestamp_val_str should be the yyyymmddThhmmss string or None for current time.
		"""
		if not timestamp_val_str: # If None or empty string, generate current time
			timestamp_val_str = time.strftime("%Y%m%dT%H:%M:%S", time.gmtime())
		self.timestamp = timestamp_val_str
		# Remove existing delay tags before adding a new one
		for delay_tag in self.getTags("x", namespace=NS_DELAY):
			self.delChild(delay_tag)
		self.setTag("x", {"stamp": self.timestamp}, namespace=NS_DELAY)

	def get_child_namespaces(self): # Renamed getProperties
		"""
		Return the list of unique namespaces of the direct child elements.
		"""
		namespaces_list = [] # Renamed props
		for child_node in self.getChildren(): # Renamed child
			namespace_uri = child_node.getNamespace() # Renamed prop
			if namespace_uri not in namespaces_list:
				namespaces_list.append(namespace_uri)
		return namespaces_list

	def __setitem__(self, item_key, item_value): # Renamed item, val
		"""
		Set the item "item_key" to the value "item_value".
		"""
		if item_key in ["to", "from"]:
			item_value = Jid(item_value) # Ensure JID object
		return self.setAttr(item_key, str(item_value)) # Store as string

class Message(Stanza): # Renamed Message, Protocol to Stanza
	"""
	XMPP Message stanza - "push" mechanism.
	"""
	def __init__(self, to_jid=None, body_text=None, message_type=None, subject_text=None, attrs_dict={}, from_jid=None, payload_list=[], timestamp_str=None, xmlns_str=NS_CLIENT, source_node=None): # Renamed params
		Stanza.__init__(self, "message", to_jid=to_jid, stanza_type=message_type, attrs_dict=attrs_dict, from_jid=from_jid, payload_list=payload_list, timestamp_str=timestamp_str, xmlns_str=xmlns_str, source_node=source_node)
		if body_text:
			self.set_body(body_text)
		if subject_text:
			self.set_subject(subject_text)

	def get_body(self): # Renamed getBody
		return self.getTagData("body")

	def get_subject(self): # Renamed getSubject
		return self.getTagData("subject")

	def get_thread(self): # Renamed getThread
		return self.getTagData("thread")

	def set_body(self, body_val): # Renamed setBody, val
		self.setTagData("body", body_val)

	def set_subject(self, subject_val): # Renamed setSubject, val
		self.setTagData("subject", subject_val)

	def set_thread(self, thread_val): # Renamed setThread, val
		self.setTagData("thread", thread_val)

	def build_reply(self, body_text_reply=None): # Renamed buildReply, text
		""" Builds and returns another Message object with specified text. """
		reply_msg = Message(to_jid=self.get_from(), from_jid=self.get_to(), body_text=body_text_reply) # Use new names
		thread_id = self.get_thread() # Renamed thr
		if thread_id:
			reply_msg.set_thread(thread_id)
		return reply_msg

class Presence(Stanza): # Renamed Presence, Protocol to Stanza
	"""
	XMPP Presence object.
	"""
	def __init__(self, to_jid=None, presence_type=None, priority_val=None, show_val=None, status_text=None, attrs_dict={}, from_jid=None, timestamp_str=None, payload_list=[], xmlns_str=NS_CLIENT, source_node=None): # Renamed params
		Stanza.__init__(self, "presence", to_jid=to_jid, stanza_type=presence_type, attrs_dict=attrs_dict, from_jid=from_jid, payload_list=payload_list, timestamp_str=timestamp_str, xmlns_str=xmlns_str, source_node=source_node)
		if priority_val:
			self.set_priority(priority_val)
		if show_val:
			self.set_show(show_val)
		if status_text:
			self.set_status(status_text)

	def get_priority(self): # Renamed getPriority
		return self.getTagData("priority")

	def get_show(self): # Renamed getShow
		return self.getTagData("show")

	def get_status(self): # Renamed getStatus
		return self.getTagData("status")

	def set_priority(self, priority_val): # Renamed setPriority, val
		self.setTagData("priority", str(priority_val)) # Ensure string for XML

	def set_show(self, show_val): # Renamed setShow, val
		self.setTagData("show", show_val)

	def set_status(self, status_text): # Renamed setStatus, val
		self.setTagData("status", status_text)

	def _get_muc_item_attribute(self, item_tag_name, attribute_name): # Renamed _muc_getItemAttr, tag, attr
		for x_tag_node in self.getTags("x", namespace=NS_MUC_USER): # Renamed xtag
			for child_node in x_tag_node.getTags(item_tag_name): # Renamed child
				return child_node.getAttr(attribute_name)
		return None # Return None if not found

	def _get_muc_subtag_data_and_attribute(self, sub_tag_name, attribute_name_to_get): # Renamed _muc_getSubTagDataAttr, tag, attr
		for x_tag_node in self.getTags("x", namespace=NS_MUC_USER): # Renamed xtag
			for item_node in x_tag_node.getTags("item"): # Renamed child
				for actual_sub_tag_node in item_node.getTags(sub_tag_name): # Renamed cchild
					return actual_sub_tag_node.getData(), actual_sub_tag_node.getAttr(attribute_name_to_get)
		return None, None

	def get_muc_role(self): # Renamed getRole
		return self._get_muc_item_attribute("item", "role")

	def get_muc_affiliation(self): # Renamed getAffiliation
		return self._get_muc_item_attribute("item", "affiliation")

	def get_muc_nick(self): # Renamed getNick
		return self._get_muc_item_attribute("item", "nick")

	def get_muc_jid(self): # Renamed getJid
		jid_str = self._get_muc_item_attribute("item", "jid")
		return Jid(jid_str) if jid_str else None

	def get_muc_reason(self): # Renamed getReason
		return self._get_muc_subtag_data_and_attribute("reason", "")[0]

	def get_muc_actor_jid(self): # Renamed getActor
		actor_jid_str = self._get_muc_subtag_data_and_attribute("actor", "jid")[1]
		return Jid(actor_jid_str) if actor_jid_str else None

	def get_muc_status_code(self): # Renamed getStatusCode
		return self._get_muc_item_attribute("status", "code")

class Iq(Stanza): # Renamed Iq, Protocol to Stanza
	"""
	XMPP Iq object - get/set dialog mechanism.
	"""
	def __init__(self, iq_type=None, query_namespace=None, attrs_dict={}, to_jid=None, from_jid=None, payload_list=[], xmlns_str=NS_CLIENT, source_node=None): # Renamed params
		Stanza.__init__(self, "iq", to_jid=to_jid, stanza_type=iq_type, attrs_dict=attrs_dict, from_jid=from_jid, xmlns_str=xmlns_str, source_node=source_node)
		if payload_list: # payload should be for query tag
			self.set_query_payload(payload_list)
		if query_namespace: # This should be set after payload if payload creates the query tag
			self.set_query_namespace(query_namespace)
		# If no query tag from payload or ns, create one if needed
		if not self.getTag("query") and (query_namespace or payload_list):
		    query_tag = self.setTag("query")
		    if query_namespace: query_tag.setNamespace(query_namespace)
		    if payload_list: query_tag.setPayload(payload_list)


	def get_query_namespace(self): # Renamed getQueryNS
		query_tag_node = self.getTag("query") # Renamed tag
		if query_tag_node:
			return query_tag_node.getNamespace()
		return None

	def get_query_node_attribute(self): # Renamed getQuerynode
		return self.getTagAttr("query", "node")

	def get_query_payload(self): # Renamed getQueryPayload
		query_tag_node = self.getTag("query")
		if query_tag_node:
			return query_tag_node.getPayload()
		return None

	def get_query_children(self): # Renamed getQueryChildren
		query_tag_node = self.getTag("query")
		if query_tag_node:
			return query_tag_node.getChildren()
		return []

	def set_query_namespace(self, namespace_uri): # Renamed setQueryNS, namespace
		self.setTag("query").setNamespace(namespace_uri)

	def set_query_payload(self, payload_list_or_node): # Renamed setQueryPayload, payload
		self.setTag("query").setPayload(payload_list_or_node)

	def set_query_node_attribute(self, node_attr_val): # Renamed setQuerynode, node
		self.setTagAttr("query", "node", node_attr_val)

	def build_reply(self, reply_type_str): # Renamed buildReply, typ
		""" Builds and returns another Iq object of specified type. """
		reply_iq = Iq(iq_type=reply_type_str, to_jid=self.get_from(), from_jid=self.get_to(), attrs_dict={"id": self.get_id()}) # Use new names
		if self.getTag("query"): # Copy query namespace and node if present
			reply_iq.set_query_namespace(self.get_query_namespace())
			query_node_attr = self.get_query_node_attribute()
			if query_node_attr:
				reply_iq.set_query_node_attribute(query_node_attr)
		return reply_iq

class XMPPErrorNode(Node): # Renamed ErrorNode
	"""
	XMPP-style error element.
	"""
	def __init__(self, condition_name_str, legacy_error_code=None, error_type_str=None, error_text_str=None): # Renamed name, code, typ, text
		"""
		Create new error node object.
		"""
		error_details = ERROR_CONDITIONS_MAP.get(condition_name_str) # Use new map name
		defined_code, defined_ns, defined_type, defined_text = "500", NS_STANZAS, "cancel", ""

		if error_details:
			defined_code, defined_type, defined_text = error_details[0], error_details[1], error_details[2]
			# Infer namespace from condition_name_str if it's a full NS#condition
			if ' ' in condition_name_str:
				defined_ns = condition_name_str.split(' ')[0]
			else: # Assume it's a stanza error if not specified
				defined_ns = NS_STANZAS

		final_type = error_type_str if error_type_str else defined_type
		final_code = str(legacy_error_code) if legacy_error_code else defined_code # Ensure code is string
		final_text = error_text_str if error_text_str is not None else defined_text

		# The error condition tag itself (e.g., <item-not-found xmlns="urn:ietf:params:xml:ns:xmpp-stanzas"/>)
		condition_tag_name = condition_name_str.split()[-1] # Get the actual condition name
		error_payload = [Node(tag=condition_tag_name, namespace=defined_ns)]

		if final_text: # Add text element if present
			error_payload.append(Node(tag="text", namespace=NS_STANZAS, payload=[final_text]))

		attrs = {"type": final_type}
		if final_code: # Only add code if it's not empty (stream errors might not have it)
			attrs["code"] = final_code

		Node.__init__(self, tag="error", attrs=attrs, payload=error_payload)
		# For stream errors, the outer tag is <stream:error> not <error>
		# This class is for stanza errors. StreamError exceptions are used for stream errors.

class ErrorStanza(Stanza): # Renamed Error, Protocol to Stanza
	"""
	Used to quickly transform received stanza into error reply.
	"""
	def __init__(self, original_stanza_node, error_condition_node_or_name, is_reply=True): # Renamed node, error, reply
		"""
		Create error reply based on the received original_stanza_node and the error_condition.
		"""
		if is_reply:
			Stanza.__init__(self, name=original_stanza_node.getName(), to_jid=original_stanza_node.get_from(), from_jid=original_stanza_node.get_to(), source_node=original_stanza_node)
		else:
			Stanza.__init__(self, name=original_stanza_node.getName(), source_node=original_stanza_node)

		self.set_error(error_condition_node_or_name) # Use new name
		if original_stanza_node.get_type() == "error": # Check original type
			self.__str__ = self._duplicate_error_str # Use new name

	def _duplicate_error_str(self, *args): # Renamed __dupstr__
		""" Prevent serializing an error reply to an error stanza. """
		return ""

class DataFormField(Node): # Renamed DataField
	"""
	Represents a field in a jabber:x:data form.
	"""
	def __init__(self, variable_name=None, field_value=None, field_type=None, is_required=False, label_text=None, description_text=None, options_list=[], source_node=None): # Renamed params
		Node.__init__(self, "field", node=source_node)
		if variable_name:
			self.set_variable_name(variable_name)
		if isinstance(field_value, (list, tuple)):
			self.set_values(field_value)
		elif field_value is not None: # Check for None explicitly
			self.set_value(field_value)
		if field_type:
			self.set_type(field_type)
		elif not field_type and not source_node: # Default type if new and not from node
			self.set_type("text-single")
		if is_required:
			self.set_required(True)
		if label_text:
			self.set_label(label_text)
		if description_text:
			self.set_description(description_text)
		if options_list:
			self.set_options(options_list)

	def set_required(self, required_bool=True): # Renamed setRequired, req
		if required_bool:
			self.setTag("required")
		else:
			self.delChild("required", namespace=NS_DATA) # Ensure namespace for safety

	def is_required(self): # Renamed isRequired
		return bool(self.getTag("required")) # Return boolean

	def set_label(self, label_str): # Renamed setLabel, label
		self.setAttr("label", label_str)

	def get_label(self): # Renamed getLabel
		return self.getAttr("label")

	def set_description(self, description_str): # Renamed setDesc, desc
		self.setTagData("desc", description_str)

	def get_description(self): # Renamed getDesc
		return self.getTagData("desc")

	def set_value(self, value_data): # Renamed setValue, val
		self.setTagData("value", ustr(value_data)) # Ensure ustr for payload

	def get_value(self): # Renamed getValue
		return self.getTagData("value")

	def set_values(self, values_iterable): # Renamed setValues, ls
		self.delChild("value", namespace=NS_DATA) # Remove all existing value tags
		for val_item in values_iterable: # Renamed val
			self.add_value(val_item)

	def add_value(self, value_data): # Renamed addValue, val
		self.addChild("value", payload=[ustr(value_data)]) # Ensure ustr

	def get_values(self): # Renamed getValues
		value_nodes = [] # Renamed ret
		for tag_node in self.getTags("value"): # Renamed tag
			value_nodes.append(tag_node.getData())
		return value_nodes

	def get_options(self): # Renamed getOptions
		options_data = [] # Renamed ret
		for option_tag_node in self.getTags("option"): # Renamed tag
			options_data.append([option_tag_node.getAttr("label"), option_tag_node.getTagData("value")])
		return options_data

	def set_options(self, options_iterable): # Renamed setOptions, ls
		self.delChild("option", namespace=NS_DATA) # Remove all existing option tags
		for option_item in options_iterable: # Renamed opt
			self.add_option(option_item)

	def add_option(self, option_item): # Renamed addOption, opt
		if isinstance(option_item, str):
			self.addChild("option").setTagData("value", ustr(option_item))
		else: # Assuming (label, value) tuple/list
			self.addChild("option", {"label": ustr(option_item[0])}).setTagData("value", ustr(option_item[1]))

	def get_type(self): # Renamed getType
		return self.getAttr("type")

	def set_type(self, type_str): # Renamed setType, val
		return self.setAttr("type", type_str)

	def get_variable_name(self): # Renamed getVar
		return self.getAttr("var")

	def set_variable_name(self, var_name_str): # Renamed setVar, val
		return self.setAttr("var", var_name_str)

class DataFormReported(Node): # Renamed DataReported
	"""
	Describes the fields to be returned in a data form result (XEP-0004).
	"""
	def __init__(self, source_node=None): # Renamed node
		Node.__init__(self, "reported", node=source_node)
		if source_node:
			updated_children = [] # Renamed newkids
			for child_n in self.getChildren(): # Renamed n
				if child_n.getName() == "field":
					updated_children.append(DataFormField(source_node=child_n)) # Use new name
				else:
					updated_children.append(child_n)
			self.kids = updated_children

	def get_field(self, field_name_str): # Renamed getField, name
		return self.getTag("field", attrs={"var": field_name_str})

	def set_field(self, field_name_str, field_type=None, label_text=None): # Renamed setField, name, typ, label
		field_node = self.get_field(field_name_str)
		if not field_node:
			field_node = self.addChild(node=DataFormField(variable_name=field_name_str, field_type=field_type, label_text=label_text)) # Use new name
		return field_node

	def as_dict(self): # Renamed asDict
		result_dict = {} # Renamed ret
		for field_node in self.getTags("field"):
			var_name = field_node.getAttr("var")
			field_type_str = field_node.get_type() # Use new name
			if isinstance(field_type_str, str) and field_type_str.endswith("-multi"):
				field_values = [val_node.getData() for val_node in field_node.getTags("value")] # Renamed val, i
			else:
				field_values = field_node.getTagData("value")
			result_dict[var_name] = field_values
		# Instructions are not typically part of 'reported' but keeping if original had it
		if self.getTag("instructions"):
			result_dict["instructions"] = self.getInstructions() # getInstructions needs to be defined or part of Node
		return result_dict

	# Adding __getitem__ and __setitem__ for reported (though usually read-only definition)
	def __getitem__(self, field_name_str):
		field_obj = self.get_field(field_name_str)
		if field_obj:
			# For reported fields, value is usually not present, but type/label are.
			# This might need adjustment based on how it's used.
			return {"type": field_obj.get_type(), "label": field_obj.get_label()}
		raise IndexError("No such field in reported data: %s" % field_name_str)

	def __setitem__(self, field_name_str, field_attributes_dict):
		# field_attributes_dict should be like {"type": "text-single", "label": "My Label"}
		field_obj = self.set_field(field_name_str, field_type=field_attributes_dict.get("type"), label_text=field_attributes_dict.get("label"))
		return field_obj


class DataFormItem(Node): # Renamed DataItem
	"""
	Represents an item in a data form result list (XEP-0004).
	"""
	def __init__(self, source_node=None): # Renamed node
		Node.__init__(self, "item", node=source_node)
		if source_node:
			updated_children = [] # Renamed newkids
			for child_n in self.getChildren(): # Renamed n
				if child_n.getName() == "field":
					updated_children.append(DataFormField(source_node=child_n)) # Use new name
				else:
					updated_children.append(child_n)
			self.kids = updated_children

	def get_field(self, field_name_str): # Renamed getField, name
		return self.getTag("field", attrs={"var": field_name_str})

	def set_field(self, field_name_str, field_value=None, field_type=None): # Renamed setField, name, value, typ
		field_node = self.get_field(field_name_str)
		if not field_node:
			field_node = self.addChild(node=DataFormField(variable_name=field_name_str, field_value=field_value, field_type=field_type)) # Use new name
		elif field_value is not None: # If field exists, update its value
			field_node.set_value(field_value)
		return field_node

	def as_dict(self): # Renamed asDict
		result_dict = {} # Renamed ret
		for field_node in self.getTags("field"):
			var_name = field_node.getAttr("var")
			field_type_str = field_node.get_type() # Use new name
			if isinstance(field_type_str, str) and field_type_str.endswith("-multi"):
				field_values = [val_node.getData() for val_node in field_node.getTags("value")] # Renamed val, i
			else:
				field_values = field_node.getTagData("value")
			result_dict[var_name] = field_values
		# Instructions are not typically part of 'item' itself
		return result_dict

	def __getitem__(self, field_name_str): # Renamed name
		item_field = self.get_field(field_name_str) # Renamed item
		if item_field:
			return item_field.get_value() # Use new name
		raise IndexError("No such field in data item: %s" % field_name_str)

	def __setitem__(self, field_name_str, value_data): # Renamed name, val
		return self.set_field(field_name_str, field_value=value_data).set_value(value_data) # Use new name

class DataForm(Node):
	"""
	DataForm class. Used for manipulating dataforms in XMPP.
	"""
	def __init__(self, form_type=None, data_payload=[], title_text=None, source_node=None): # Renamed typ, data, title, node
		Node.__init__(self, "x", node=source_node)
		if source_node:
			updated_children = [] # Renamed newkids
			for child_n in self.getChildren(): # Renamed n
				if child_n.getName() == "field":
					updated_children.append(DataFormField(source_node=child_n)) # Use new name
				elif child_n.getName() == "item":
					updated_children.append(DataFormItem(source_node=child_n)) # Use new name
				elif child_n.getName() == "reported":
					updated_children.append(DataFormReported(source_node=child_n)) # Use new name
				else:
					updated_children.append(child_n)
			self.kids = updated_children
		if form_type:
			self.set_type(form_type)
		self.setNamespace(NS_DATA)
		if title_text:
			self.set_title(title_text)

		if isinstance(data_payload, dict): # Convert dict to list of DataFormFields
			new_data_payload = [] # Renamed newdata
			for var_name, field_val in data_payload.items(): # Use items()
				new_data_payload.append(DataFormField(variable_name=var_name, field_value=field_val)) # Use new name
			data_payload = new_data_payload

		for child_item in data_payload: # Renamed child
			if isinstance(child_item, str): # Assumed to be instructions
				self.add_instructions(child_item)
			elif isinstance(child_item, (DataFormField, DataFormItem, DataFormReported)): # Use new names
				self.addChild(node=child_item) # Use addChild for Node objects
			else: # Assume it's a node that can be wrapped by DataFormField
				self.addChild(node=DataFormField(source_node=child_item))


	def get_type(self): # Renamed getType
		return self.getAttr("type")

	def set_type(self, type_str): # Renamed setType, typ
		self.setAttr("type", type_str)

	def get_title(self): # Renamed getTitle
		return self.getTagData("title")

	def set_title(self, text_str): # Renamed setTitle, text
		self.setTagData("title", text_str)

	def get_instructions(self): # Renamed getInstructions
		all_instructions = self.getTags("instructions")
		return "\n".join([instr.getData() for instr in all_instructions if instr.getData()]) if all_instructions else None


	def set_instructions(self, text_str): # Renamed setInstructions, text
		# Remove existing instructions
		for instr_node in self.getTags("instructions"):
			self.delChild(instr_node)
		if text_str: # Add new one if text is provided
			self.addChild("instructions", payload=[text_str])

	def add_instructions(self, text_str): # Renamed addInstructions, text
		self.addChild("instructions", payload=[text_str])

	def get_field(self, field_name_str): # Renamed getField, name
		return self.getTag("field", attrs={"var": field_name_str})

	def set_field(self, field_name_str, field_value=None, field_type=None): # Renamed setField, name, value, typ
		field_node = self.get_field(field_name_str)
		if not field_node:
			field_node = self.addChild(node=DataFormField(variable_name=field_name_str, field_value=field_value, field_type=field_type)) # Use new names
		elif field_value is not None: # If field exists and value provided, update it
		    field_node.set_value(field_value)
		return field_node

	def as_dict(self): # Renamed asDict
		result_dict = {} # Renamed ret
		for field_node in self.getTags("field"):
			var_name = field_node.getAttr("var")
			field_type_str = field_node.get_type()
			if isinstance(field_type_str, str) and field_type_str.endswith("-multi"):
				field_values = [val_node.getData() for val_node in field_node.getTags("value")]
			else:
				field_values = field_node.getTagData("value")
			result_dict[var_name] = field_values
		if self.getTag("instructions"): # Check if instructions exist
			result_dict["instructions"] = self.get_instructions()
		return result_dict

	def __getitem__(self, field_name_str): # Renamed name
		item_field = self.get_field(field_name_str) # Renamed item
		if item_field:
			# For a data form, a field can have multiple values if it's a *-multi type
			df_field = DataFormField(source_node=item_field) # Wrap to use its methods
			if df_field.get_type() and df_field.get_type().endswith("-multi"):
				return df_field.get_values()
			return df_field.get_value()
		raise IndexError("No such field in data form: %s" % field_name_str)

	def __setitem__(self, field_name_str, value_data): # Renamed name, val
		# This will create the field if it doesn't exist, or update the first value if it does.
		# For multi-value fields, use set_field().set_values([...])
		field_obj = self.set_field(field_name_str)
		if isinstance(value_data, list) and field_obj.get_type() and field_obj.get_type().endswith("-multi"):
			field_obj.set_values(value_data)
		else:
			field_obj.set_value(value_data)
		return field_obj
