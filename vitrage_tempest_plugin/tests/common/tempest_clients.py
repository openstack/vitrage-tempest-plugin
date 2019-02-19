# Copyright 2016 Nokia
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from keystoneauth1 import loading as ka_loading
from keystoneauth1 import session as ka_session
from keystoneclient.v3 import client as ks_client_v3
from neutronclient.v2_0 import client as neutron_client
from oslo_utils import importutils as utils
from tempest.common import credentials_factory as common_creds
from tempest import config
from vitrageclient import client as vc

CONF = config.CONF

_client_modules = {
    'aodh': 'aodhclient.client',
    'ceilometer': 'ceilometerclient.client',
    'nova': 'novaclient.client',
    'cinder': 'cinderclient.client',
    'glance': 'glanceclient.client',
    'neutron': 'neutronclient.v2_0.client',
    'heat': 'heatclient.client',
    'mistral': 'mistralclient.api.v2.client',
    'gnocchi': 'gnocchiclient.v1.client',
    'trove': 'troveclient.v1.client'
}


def driver_module(driver):
    mod_name = _client_modules[driver]
    module = utils.import_module(mod_name)
    return module


class TempestClients(object):
    @classmethod
    def class_init(cls, creds):
        cls.creds = creds
        cls._vitrage = None
        cls._ceilometer = None
        cls._nova = None
        cls._cinder = None
        cls._glance = None
        cls._neutron = None
        cls._heat = None
        cls._mistral = None
        cls._aodh = None
        cls._keystone = None
        cls._gnocchi = None

    @classmethod
    def vitrage(cls):
        """vitrage client

        :rtype: vitrageclient.v1.client.Client
        """
        if not cls._vitrage:
            cls._vitrage = vc.Client(
                '1', session=cls._get_session_for_admin())
        return cls._vitrage

    @classmethod
    def vitrage_client_for_user(cls):
        """vitrage client for a specific user and tenant

        :rtype: vitrageclient.v1.client.Client
        """
        session = cls._get_session_for_user()
        return vc.Client('1', session=session)

    @classmethod
    def neutron_client_for_user(cls):
        session = cls._get_session_for_user()
        return neutron_client.Client(session=session)

    @classmethod
    def ceilometer(cls):
        """ceilometer client

        :rtype: ceilometerclient.v2.client.Client
        """
        if not cls._ceilometer:
            cm_client = driver_module('ceilometer')
            client = cm_client.get_client(
                version=CONF.root_cause_analysis_service.ceilometer_version,
                session=cls._get_session_for_admin(),
            )
            cls._ceilometer = client
        return cls._ceilometer

    @classmethod
    def nova(cls):
        """nova client

        :rtype: novaclient.v2.client.Client
        """
        if not cls._nova:
            n_client = driver_module('nova')
            client = n_client.Client(
                version=CONF.root_cause_analysis_service.nova_version,
                session=cls._get_session_for_admin(),
            )
            cls._nova = client
        return cls._nova

    @classmethod
    def cinder(cls):
        """cinder client

        :rtype: cinderclient.v2.client.Client
        """
        if not cls._cinder:
            cin_client = driver_module('cinder')
            client = cin_client.Client(
                version=CONF.root_cause_analysis_service.cinder_version,
                session=cls._get_session_for_admin(),
            )
            cls._cinder = client
        return cls._cinder

    @classmethod
    def glance(cls):
        """glance client

        :rtype: glanceclient.v2.client.Client
        """
        if not cls._glance:

            glan_client = driver_module('glance')
            client = glan_client.Client(
                version=CONF.root_cause_analysis_service.glance_version,
                session=cls._get_session_for_admin(),
            )
            cls._glance = client
        return cls._glance

    @classmethod
    def neutron(cls):
        """neutron client

        :rtype: neutronclient.v2_0.client.Client
        """
        if not cls._neutron:
            ne_client = driver_module('neutron')
            client = ne_client.Client(
                session=cls._get_session_for_admin()
            )
            cls._neutron = client
        return cls._neutron

    @classmethod
    def heat(cls):
        """heat client

        :rtype: heatclient.v1.client.Client
        """
        if not cls._heat:
            he_client = driver_module('heat')
            client = he_client.Client(
                version=CONF.root_cause_analysis_service.heat_version,
                session=cls._get_session_for_admin()
            )
            cls._heat = client
        return cls._heat

    @classmethod
    def mistral(cls):
        """mistral client

        :rtype: mistralclient.v2.client.Client
        """
        if not cls._mistral:
            mi_client = driver_module('mistral')
            client = mi_client.Client(
                session=cls._get_session_for_admin(),
            )
            cls._mistral = client
        return cls._mistral

    @classmethod
    def aodh(cls):
        """aodh client

        :rtype: aodhclient.v2.client.Client
        """
        if not cls._aodh:
            ao_client = driver_module('aodh')
            client = ao_client.Client(
                CONF.root_cause_analysis_service.aodh_version,
                session=cls._get_session_for_admin())
            cls._aodh = client
        return cls._aodh

    @classmethod
    def keystone(cls):
        """keystone client

        :rtype: keystoneclient.v3.client.Client
        """
        if not cls._keystone:
            sess = cls._get_session_for_admin()
            cls._keystone = ks_client_v3.Client(session=sess)
        return cls._keystone

    @classmethod
    def gnocchi(cls):
        """gnocchi client

        :rtype: gnocchiclient.v1.client.Client
        """
        if not cls._gnocchi:
            gn_client = driver_module('gnocchi')
            client = gn_client.Client(
                session=cls._get_session_for_admin())
            cls._gnocchi = client
        return cls._gnocchi

    @classmethod
    def _get_session_for_admin(cls):
        admin_creds = common_creds.get_configured_admin_credentials()
        password = admin_creds.password
        username = admin_creds.username
        user_domain_id = admin_creds.user_domain_id
        project_name = admin_creds.project_name
        project_domain_id = admin_creds.project_domain_id

        return cls._get_session(username, password, user_domain_id,
                                project_name, project_domain_id)

    @classmethod
    def _get_session_for_user(cls):
        username = cls.creds.username
        password = cls.creds.password
        user_domain_id = cls.creds.user_domain_id
        project_name = cls.creds.project_name
        project_domain_id = cls.creds.project_domain_id

        return cls._get_session(username, password, user_domain_id,
                                project_name, project_domain_id)

    @classmethod
    def _get_session(cls, username, password, user_domain_id, project_name,
                     project_domain_id):
        loader = ka_loading.get_plugin_loader('password')
        auth_url = CONF.identity.uri_v3
        auth_plugin = loader.load_from_options(
            auth_url=auth_url,
            username=username, password=password, project_name=project_name,
            project_domain_id=project_domain_id,
            user_domain_id=user_domain_id)
        return ka_session.Session(auth=auth_plugin)
