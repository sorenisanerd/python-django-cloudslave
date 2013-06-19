#
#   Copyright 2013 Cisco Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import datetime
import logging
import random
import re
import string

from django.db import models
from cloudslave import exc

from novaclient.v1_1 import client
from novaclient import exceptions as novaclient_exceptions


logger = logging.getLogger(__name__)


class Cloud(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    endpoint = models.URLField(max_length=200)
    user_name = models.CharField(max_length=200)
    tenant_name = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    region = models.CharField(max_length=200, blank=True)
    flavor_name = models.CharField(max_length=200)
    image_name = models.CharField(max_length=200)

    def __init__(self, *args, **kwargs):
        self._client = None
        return super(Cloud, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.name

    @property
    def client(self):
        if self._client is None:
            kwargs = {}
            if self.region:
                kwargs['region_name'] = self.region

            self._client = client.Client(self.user_name,
                                         self.password,
                                         self.tenant_name,
                                         self.endpoint,
                                         service_type="compute",
                                         **kwargs)
            self._client.cloud = self

        return self._client

    def _random_string(self, length=8):
        alphabet = string.letters + string.digits
        return ''.join([random.choice(alphabet) for x in range(length)])

    def _get_unique_name(self, mgr):
        existing_names = set(kp.name for kp in mgr.list())
        while True:
            name = 'cloudslave-%s' % (self._random_string(),)
            if name not in existing_names:
                return name

    def _get_unique_slave_name(self):
        return self._get_unique_name(self.client.servers)

    def _get_unique_keypair_name(self):
        return self._get_unique_name(self.client.keypairs)

    @property
    def image(self):
        rx = re.compile(self.image_name)
        for image in self.client.images.list():
            if rx.match(image.name):
                return image
        raise exc.NoMatchingImage(self.image_name)

    @property
    def flavor(self):
        for flavor in self.client.flavors.list():
            if flavor.name == self.flavor_name:
                return flavor
        raise exc.NoMatchingFlavor(self.flavor_name)

    @property
    def keypair(self):
        if self.keypair_set.count() < 1:
            logger.info('Cloud %s does not have a keypair yet. '
                        'Creating' % (self,))
            name = self._get_unique_keypair_name()
            kp = self.client.keypairs.create(name=name)
            keypair = KeyPair(cloud=self, name=name,
                              private_key=kp.private_key,
                              public_key=kp.public_key)
            keypair.save()
            logger.info('KeyPair %s created' % (keypair,))
        return self.keypair_set.all()[0]

    def create_reservation(self, count=1):
        res = Reservation(cloud=self, number_of_slaves=count)
        res.save()
        return res


class KeyPair(models.Model):
    cloud = models.ForeignKey(Cloud)
    name = models.CharField(max_length=200)
    private_key = models.TextField()
    public_key = models.TextField()

    def __unicode__(self):
        return '%s@%s' % (self.name, self.cloud)

    class Meta:
        verbose_name_plural = "series"
        unique_together = ('cloud', 'name')


class Reservation(models.Model):
    DEFAULT_TIMEOUT = 180  # 3 minutes

    NEW = 0
    BOOTING = 1
    READY = 2
    SHUTTING_DOWN = 3
    TERMINATED = 4
    FAILED_TO_START = 5
    RESERVATION_STATES = (
        (NEW, 'Newly created'),
        (BOOTING, 'Booting'),
        (READY, 'Ready'),
        (SHUTTING_DOWN, 'Shutting down'),
        (TERMINATED, 'Terminated'),
        (FAILED_TO_START, 'Failed to start')
    )

    cloud = models.ForeignKey(Cloud)
    number_of_slaves = models.IntegerField()
    state = models.SmallIntegerField(default=NEW,
                                     choices=RESERVATION_STATES)
    timeout = models.DateTimeField(blank=False, null=False)

    def __unicode__(self):
        return '%s' % self.pk

    def save(self, **kwargs):
        if self.timeout is None:
            self.timeout = (datetime.datetime.now()
                            + datetime.timedelta(seconds=self.DEFAULT_TIMEOUT))
        return super(Reservation, self).save(**kwargs)

    def start(self):
        try:
            for x in range(self.number_of_slaves):
                name = self.cloud._get_unique_slave_name()
                logger.info('Creating server %s on cloud %s' %
                            (name, self.cloud))
                srv = self.cloud.client.servers.create(name, self.cloud.image,
                                                       self.cloud.flavor,
                                                       key_name=self.cloud.keypair.name)
                slave = Slave(name=name, reservation=self, cloud_node_id=srv.id)
                slave.save()
        except novaclient_exceptions.ClientException, e1:
            logger.error("Failed to start one or more slaves", exc_info=e1)
            self.set_state(self.FAILED_TO_START)
            raise

        self.set_state(self.BOOTING)

    def terminate(self):
        for slave in self.slave_set.all():
            try:
                slave.delete()
            except Exception, e2:
                logger.error("Failed to delete slave %s" % slave, exc_info=e2)

        self.set_state(self.TERMINATED)

    def set_state(self, state):
        self.state = state
        self.save(update_fields=['state'])

    def update_status(self):
        active_count = 0
        for slave in self.slave_set.all():
            slave.update_status()
            if slave.status == 'ERROR':
                logger.info("%r went into ERROR state. Terminating reservation.")
                self.set_state(self.FAILED_TO_START)
                self.terminate()
                break
            elif slave.status == 'BUILD':
                if datetime.datetime.now() > self.timeout:
                    self.set_state(self.FAILED_TO_START)
                    self.terminate()
                    break
                self.set_state(self.BOOTING)
                break
            elif slave.status == 'ACTIVE':
                active_count += 1

        if active_count == self.slave_set.count():
            self.set_state(self.READY)

        return self.state


class Slave(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    reservation = models.ForeignKey(Reservation)
    cloud_node_id = models.CharField(max_length=200)
    status = models.CharField(max_length=15, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        self.status = None
        return super(Slave, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.name

    @property
    def cloud_server(self):
        cloud = self.reservation.cloud
        client = cloud.client
        return client.servers.get(self.cloud_node_id)

    def delete(self):
        logger.info('Deleting server %s on cloud %s.' % (self, self.reservation.cloud))
        try:
            self.cloud_server.delete()
        except novaclient_exceptions.NotFound:
            logger.info('Node already gone, unable to delete it')

        super(Slave, self).delete()

    def _fetch_current_status(self):
        return self.cloud_server.status

    def update_status(self):
        self.status = self._fetch_current_status()
        self.save(update_fields=['status'])

