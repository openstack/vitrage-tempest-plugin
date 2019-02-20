#!/usr/bin/env bash
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

source $BASE/new/devstack/functions
sudo chown -R $USER:stack $BASE/new/tempest

DEVSTACK_PATH="$BASE/new"
TEMPEST_CONFIG=$BASE/new/tempest/etc/tempest.conf

iniset $TEMPEST_CONFIG service_available vitrage true

if [ "$1" = "mock" ]; then
  iniset $TEMPEST_CONFIG root_cause_analysis_service zabbix_alarms_per_host 8
  iniset $TEMPEST_CONFIG root_cause_analysis_service instances_per_host 50
  iniset $TEMPEST_CONFIG root_cause_analysis_service snapshots_interval 60
else
  iniset $TEMPEST_CONFIG root_cause_analysis_service zabbix_alarms_per_host 2
  iniset $TEMPEST_CONFIG root_cause_analysis_service instances_per_host 2
  iniset $TEMPEST_CONFIG root_cause_analysis_service snapshots_interval 120
fi


#Argument is received from Zuul
if [ "$1" = "api" ]; then
  TESTS="topology|test_rca|test_alarms|test_resources|test_template|test_webhook|test_service"
elif [ "$1" = "datasources" ]; then
  TESTS="datasources|test_events|notifiers|e2e|database"
elif [ "$1" = "mock" ]; then
  TESTS="mock_datasource"
else
  TESTS="topology"
fi

if [ "$DEVSTACK_GATE_USE_PYTHON3" == "True" ]; then
        export PYTHON=python3
fi

sudo cp -rf $DEVSTACK_PATH/tempest/etc/logging.conf.sample $DEVSTACK_PATH/tempest/etc/logging.conf

cd $DEVSTACK_PATH/tempest/
sudo -E stestr init

echo "Listing existing Tempest tests"
sudo -E stestr list vitrage_tempest_plugin | grep -E "$TESTS" | sort | tee /tmp/vitrage_tempest_tests.list
echo "Testing $1: $TESTS..."
sudo -E stestr run --serial --subunit --load-list=/tmp/vitrage_tempest_tests.list | subunit-trace --fails --no-failure-debug
