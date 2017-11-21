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

from vitrage import keystone_client
from vitrage import os_clients
from vitrageclient import client as vc


class TempestClients(object):
    @classmethod
    def class_init(cls, conf):
        cls._conf = conf
        cls._vitrage = None
        cls._ceilometer = None
        cls._nova = None
        cls._cinder = None
        cls._glance = None
        cls._neutron = None
        cls._heat = None
        cls._mistral = None
        cls._aodh = None

    @classmethod
    def vitrage(cls):
        """vitrage client

        :rtype: vitrageclient.v1.client.Client
        """
        if not cls._vitrage:
            cls._vitrage = vc.Client(
                '1', session=keystone_client.get_session(cls._conf))
        return cls._vitrage

    @classmethod
    def ceilometer(cls):
        """ceilometer client

        :rtype: ceilometerclient.v2.client.Client
        """
        if not cls._ceilometer:
            cls._ceilometer = os_clients.ceilometer_client(cls._conf)
        return cls._ceilometer

    @classmethod
    def nova(cls):
        """nova client

        :rtype: novaclient.v2.client.Client
        """
        if not cls._nova:
            cls._nova = os_clients.nova_client(cls._conf)
        return cls._nova

    @classmethod
    def cinder(cls):
        """cinder client

        :rtype: cinderclient.v2.client.Client
        """
        if not cls._cinder:
            cls._cinder = os_clients.cinder_client(cls._conf)
        return cls._cinder

    @classmethod
    def glance(cls):
        """glance client

        :rtype: glanceclient.v2.client.Client
        """
        if not cls._glance:
            cls._glance = os_clients.glance_client(cls._conf)
        return cls._glance

    @classmethod
    def neutron(cls):
        """neutron client

        :rtype: neutronclient.v2_0.client.Client
        """
        if not cls._neutron:
            cls._neutron = os_clients.neutron_client(cls._conf)
        return cls._neutron

    @classmethod
    def heat(cls):
        """heat client

        :rtype: heatclient.v1.client.Client
        """
        if not cls._heat:
            cls._heat = os_clients.heat_client(cls._conf)
        return cls._heat

    @classmethod
    def mistral(cls):
        """mistral client

        :rtype: mistralclient.v2.client.Client
        """
        if not cls._mistral:
            cls._mistral = os_clients.mistral_client(cls._conf)
        return cls._mistral

    @classmethod
    def aodh(cls):
        """aodh client

        :rtype: aodhclient.v2.client.Client
        """
        if not cls._aodh:
            cls._aodh = os_clients.aodh_client(cls._conf)
        return cls._aodh
