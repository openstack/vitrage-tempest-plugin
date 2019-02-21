# Copyright 2015 - Alcatel-Lucent
# Copyright 2016 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

AODH_DATASOURCE = 'aodh'
CINDER_VOLUME_DATASOURCE = 'cinder.volume'
HEAT_STACK_DATASOURCE = 'heat.stack'
NEUTRON_NETWORK_DATASOURCE = 'neutron.network'
NEUTRON_PORT_DATASOURCE = 'neutron.port'
NOVA_HOST_DATASOURCE = 'nova.host'
NOVA_INSTANCE_DATASOURCE = 'nova.instance'
NOVA_ZONE_DATASOURCE = 'nova.zone'
OPENSTACK_CLUSTER = 'openstack.cluster'
VITRAGE_DATASOURCE = 'vitrage'

DOCTOR_DATASOURCE = 'doctor'


class VertexProperties(object):
    VITRAGE_CATEGORY = 'vitrage_category'
    VITRAGE_TYPE = 'vitrage_type'
    VITRAGE_ID = 'vitrage_id'
    VITRAGE_STATE = 'vitrage_state'
    VITRAGE_IS_DELETED = 'vitrage_is_deleted'
    VITRAGE_IS_PLACEHOLDER = 'vitrage_is_placeholder'
    VITRAGE_SAMPLE_TIMESTAMP = 'vitrage_sample_timestamp'
    VITRAGE_AGGREGATED_STATE = 'vitrage_aggregated_state'
    VITRAGE_OPERATIONAL_STATE = 'vitrage_operational_state'
    VITRAGE_AGGREGATED_SEVERITY = 'vitrage_aggregated_severity'
    VITRAGE_OPERATIONAL_SEVERITY = 'vitrage_operational_severity'
    VITRAGE_RESOURCE_ID = 'vitrage_resource_id'
    ID = 'id'
    STATE = 'state'
    PROJECT_ID = 'project_id'
    UPDATE_TIMESTAMP = 'update_timestamp'
    NAME = 'name'
    SEVERITY = 'severity'
    IS_MARKED_DOWN = 'is_marked_down'
    INFO = 'info'
    GRAPH_INDEX = 'graph_index'
    RAWTEXT = 'rawtext'
    RESOURCE_ID = 'resource_id'
    RESOURCE_NAME = 'resource_name'
    VITRAGE_RESOURCE_TYPE = 'vitrage_resource_type'
    RESOURCE = 'resource'
    IS_REAL_VITRAGE_ID = 'is_real_vitrage_id'


class EdgeProperties(object):
    RELATIONSHIP_TYPE = 'relationship_type'
    VITRAGE_IS_DELETED = 'vitrage_is_deleted'
    UPDATE_TIMESTAMP = 'update_timestamp'


class EdgeLabel(object):
    """Define *some* edge labels

    Note that edge labels are not restricted to the values in this class, and
    other datasources can defined their own edge labels.
    """
    ON = 'on'
    CONTAINS = 'contains'
    CAUSES = 'causes'
    ATTACHED = 'attached'
    ATTACHED_PUBLIC = 'attached_public'
    ATTACHED_PRIVATE = 'attached_private'
    CONNECT = 'connect'
    MANAGED_BY = 'managed_by'
    COMPRISED = 'comprised'

    @staticmethod
    def labels():
        return [value for label, value in vars(EdgeLabel).items()
                if not label.startswith(('_', 'labels'))]


class DatasourceAction(object):
    SNAPSHOT = 'snapshot'
    INIT_SNAPSHOT = 'init_snapshot'
    UPDATE = 'update'


class UpdateMethod(object):
    NONE = 'none'
    PULL = 'pull'
    PUSH = 'push'


class EntityCategory(object):
    RESOURCE = 'RESOURCE'
    ALARM = 'ALARM'

    @staticmethod
    def categories():
        return [value for category, value in vars(EntityCategory).items()
                if not category.startswith(('_', 'categories'))]


class DatasourceProperties(object):
    ENTITY_TYPE = 'vitrage_entity_type'
    DATASOURCE_ACTION = 'vitrage_datasource_action'
    SAMPLE_DATE = 'vitrage_sample_date'
    EVENT_TYPE = 'vitrage_event_type'


class GraphAction(object):
    CREATE_ENTITY = 'create_entity'
    DELETE_ENTITY = 'delete_entity'
    UPDATE_ENTITY = 'update_entity'
    DELETE_RELATIONSHIP = 'delete_relationship'
    UPDATE_RELATIONSHIP = 'update_relationship'
    REMOVE_DELETED_ENTITY = 'remove_deleted_entity'
    END_MESSAGE = 'end_message'


class NotifierEventTypes(object):
    ACTIVATE_DEDUCED_ALARM_EVENT = 'vitrage.deduced_alarm.activate'
    DEACTIVATE_DEDUCED_ALARM_EVENT = 'vitrage.deduced_alarm.deactivate'
    ACTIVATE_ALARM_EVENT = 'vitrage.alarm.activate'
    DEACTIVATE_ALARM_EVENT = 'vitrage.alarm.deactivate'
    ACTIVATE_MARK_DOWN_EVENT = 'vitrage.mark_down.activate'
    DEACTIVATE_MARK_DOWN_EVENT = 'vitrage.mark_down.deactivate'
    EXECUTE_EXTERNAL_ACTION = 'vitrage.execute_external_action'


class TemplateTopologyFields(object):
    """yaml fields for topology definitions"""
    METADATA = 'metadata'
    DESCRIPTION = 'description'
    NAME = 'name'
    VERSION = 'version'

    DEFINITIONS = 'definitions'

    ENTITIES = 'entities'
    ENTITY = 'entity'
    TYPE = 'type'
    ID = 'id'

    RELATIONSHIPS = 'relationships'
    RELATIONSHIP = 'relationship'
    RELATIONSHIP_TYPE = 'relationship_type'
    SOURCE = 'source'
    TARGET = 'target'


class EventProperties(object):
    TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
    TYPE = 'type'
    TIME = 'time'
    DETAILS = 'details'


class DatasourceOpts(object):
    TRANSFORMER = 'transformer'
    DRIVER = 'driver'
    UPDATE_METHOD = 'update_method'
    CHANGES_INTERVAL = 'changes_interval'
    CONFIG_FILE = 'config_file'


class TemplateTypes(object):
    STANDARD = 'standard'
    DEFINITION = 'definition'
    EQUIVALENCE = 'equivalence'

    @staticmethod
    def types():
        return [value for type, value in vars(TemplateTypes).items()
                if not type.startswith(('_', 'types'))]


class TemplateStatus(object):
    ACTIVE = 'ACTIVE'
    ERROR = 'ERROR'
    DELETING = 'DELETING'
    DELETED = 'DELETED'
    LOADING = 'LOADING'


class TenantProps(object):
    ALL_TENANTS = 'all_tenants'
    TENANT = 'tenant'
    IS_ADMIN = 'is_admin'


class AodhProperties(object):
    ALARM_ID = 'alarm_id'
    DESCRIPTION = 'description'
    ENABLED = 'enabled'
    EVENT = 'event'
    EVENT_RULE = 'event_rule'
    EVENT_TYPE = 'event_type'
    EVENT_RESOURCE_ID = 'traits.resource_id'
    NAME = 'name'
    STATE = 'state'
    PROJECT_ID = 'project_id'
    QUERY = 'query'
    REPEAT_ACTIONS = 'repeat_actions'
    RESOURCE_ID = 'resource_id'
    SEVERITY = 'severity'
    STATE_TIMESTAMP = 'state_timestamp'
    THRESHOLD = 'threshold'
    THRESHOLD_RULE = 'threshold_rule'
    RESOURCES_THRESHOLD = 'gnocchi_aggregation_by_resources_threshold'
    METRICS_THRESHOLD = 'gnocchi_aggregation_by_metrics_threshold'
    METRICS_THRESHOLD_RULE = 'gnocchi_aggregation_by_metrics_threshold_rule'
    TIMESTAMP = 'timestamp'
    TYPE = 'type'
    VITRAGE_ID = 'vitrage_id'
    DETAIL = 'detail'
    RULE = 'rule'
    RESOURCES_THRESHOLD_RULE = \
        'gnocchi_aggregation_by_resources_threshold_rule'
    USER_ID = 'user_id'
    STATE_REASON = 'state_reason'
    ID = 'id'


class OperationalAlarmSeverity(object):
    CRITICAL = 'CRITICAL'
    SEVERE = 'SEVERE'
    WARNING = 'WARNING'
    NA = 'N/A'
    OK = 'OK'


class OperationalResourceState(object):
    NA = 'N/A'
    OK = 'OK'
    TRANSIENT = 'TRANSIENT'
    SUBOPTIMAL = 'SUBOPTIMAL'
    ERROR = 'ERROR'
    DELETED = 'DELETED'
