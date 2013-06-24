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
import mock
import re

from django.test import TestCase
import novaclient.exceptions

import cloudslave.models
from cloudslave import exc
from cloudslave.models import Cloud, KeyPair, Reservation, Slave

class CloudTests(TestCase):
    test_user = 'testuser1'
    test_tenant = 'testtenant1'
    test_password = 'testpassword1'
    test_endpoint = 'http://example.com/v2.0'

    def _create(self, name='testcloud1', **kwargs):
        cloud = Cloud(name=name,
                      endpoint=self.test_endpoint,
                      user_name=self.test_user,
                      tenant_name=self.test_tenant,
                      password=self.test_password,
                      **kwargs)
        cloud.save()
        return cloud

    def test_create_without_region(self):
        self._create()

    def test_create_with_region(self):
        self._create(region='RegionTwo')

    def test_get_random(self):
        self._create(name='cloud1')
        self._create(name='cloud2')
        self._create(name='cloud3')
        # There's a 0.03% chance this test will fail. I'm OK with those
        # odds.
        them_all = set([Cloud.get_random() for x in range(20)])
        self.assertEqual(len(them_all), 3)

    def test_cloud_client_without_region(self):
        cloud = self._create()
        with mock.patch('cloudslave.models.client') as client:
            cloud.client
            client.Client.assert_called_with(self.test_user,
                                             self.test_password,
                                             self.test_tenant,
                                             self.test_endpoint,
                                             service_type='compute')

    def test_cloud_client_with_region(self):
        cloud = self._create(region='RegionTwo')
        with mock.patch('cloudslave.models.client') as client:
            cloud.client
            client.Client.assert_called_with(self.test_user,
                                             self.test_password,
                                             self.test_tenant,
                                             self.test_endpoint,
                                             service_type='compute',
                                             region_name='RegionTwo')

    def test_cloud_client_conn_is_cached(self):
        cloud = self._create()
        with mock.patch('cloudslave.models.client') as client:
            cloud.client
            cloud.client
            self.assertEquals(client.Client.call_count, 1)

    def test_unicode(self):
        cloud = self._create()
        self.assertEquals('%s' % (cloud,), 'testcloud1')

    def _test_get_unique_name(self, method_name):
        cloud = self._create()
        with mock.patch('cloudslave.models.client') as client:
            name = getattr(cloud, method_name)()
            self.assertTrue(re.match('cloudslave-[a-zA-Z0-9]*', name) is not None)

    def test_get_unique_slave_name(self):
        self._test_get_unique_name('_get_unique_slave_name')

    def test_get_unique_keypair_name(self):
        self._test_get_unique_name('_get_unique_keypair_name')

    def _test_image(self, name):
        cloud = self._create(image_name=name)

        class Image(object):
            def __init__(self, name):
                self.name = name

        foo = Image('foo')
        bar = Image('bar')
        images = [foo, bar]
        with mock.patch.object(cloud.client, 'images') as images_mock:
            images_mock.list.return_value = images
            return cloud.image

    def test_image_not_found(self):
        self.assertRaises(exc.NoMatchingImage, self._test_image, 'baz')

    def test_image_is_found(self):
        self.assertEquals(self._test_image('foo').name, 'foo')

    def test_image_is_found_with_regex(self):
        self.assertEquals(self._test_image('b.*').name, 'bar')

    def _test_flavor(self, name):
        cloud = self._create(flavor_name=name)

        class Flavor(object):
            def __init__(self, name):
                self.name = name

        foo = Flavor('foo')
        bar = Flavor('bar')
        flavors = [foo, bar]
        with mock.patch.object(cloud.client, 'flavors') as flavors_mock:
            flavors_mock.list.return_value = flavors
            return cloud.flavor

    def test_flavor_not_found(self):
        self.assertRaises(exc.NoMatchingFlavor, self._test_flavor, 'frob')

    def test_flavor_is_found(self):
        self.assertEquals(self._test_flavor('foo').name, 'foo')

    def test_keypair_gets_created(self):
        cloud = self._create()
        with mock.patch.object(cloud.client, 'keypairs') as keypairs_mock:
            self.assertEquals(type(cloud.keypair), KeyPair)

    def test_keypair_is_reused(self):
        cloud = self._create()
        with mock.patch.object(cloud.client, 'keypairs') as keypairs_mock:
            stored_keypair = cloud.keypair
            self.assertEquals(cloud.keypair, stored_keypair)

    def test_create_reservation(self):
        cloud = self._create()
        res = cloud.create_reservation()
        self.assertEquals(type(res), Reservation)
        self.assertEquals(res.number_of_slaves, 1,
                          "Default number of slaves should be 1")

        res = cloud.create_reservation(count=15)
        self.assertEquals(type(res), Reservation)
        self.assertEquals(res.number_of_slaves, 15)


class KeyPairTests(TestCase):
    fixtures = ['test_cloud.yaml']

    def _create(self):
        cloud = Cloud.objects.get(pk='test_cloud')

        with open('cloudslave/fixtures/test-ssh-key') as fp:
            private_key = fp.read()

        with open('cloudslave/fixtures/test-ssh-key.pub') as fp:
            public_key = fp.read()

        keypair = KeyPair(name='keypair1',
                          cloud=cloud,
                          private_key=private_key,
                          public_key=public_key)

        keypair.save()
        return keypair

    def test_create(self):
        self._create()

    def test_unicode(self):
        keypair = self._create()
        self.assertEquals('%s' % (keypair,), 'keypair1@test_cloud')


class ReservationTests(TestCase):
    fixtures = ['test_cloud.yaml']

    def _create(self, *args, **kwargs):
        cloud = Cloud.objects.get(pk='test_cloud')
        return cloud.create_reservation(*args, **kwargs)

    def test_unicode(self):
        res = self._create()

        self.assertEquals('%s' % (res,), str(res.pk))

    def _fake_novaclient(self):
        client_mock = mock.MagicMock()
        client_mock.images = self._image_manager_fake()
        client_mock.flavors = self._flavor_manager_fake()
        return client_mock

    def _flavor_manager_fake(self):
        class Flavor(object):
            def __init__(self, name):
                self.name = name

        class FlavorMgrFake(object):
            def __init__(self):
                self.flavors = []

            def list(self):
                return self.flavors

            def add(self, img):
                self.flavors.append(img)

        fake_flavor_manager = FlavorMgrFake()
        fake_flavor_manager.add(Flavor('foo'))
        fake_flavor_manager.add(Flavor('bar'))
        return fake_flavor_manager

    def _image_manager_fake(self):
        class Image(object):
            def __init__(self, name):
                self.name = name

        class ImageMgrFake(object):
            def __init__(self):
                self.images = []

            def list(self):
                return self.images

            def add(self, img):
                self.images.append(img)

        fake_image_manager = ImageMgrFake()
        fake_image_manager.add(Image('foo'))
        fake_image_manager.add(Image('bar'))
        return fake_image_manager

    def test_start_single_succesful(self):
        res = self._create()

        res.cloud._client = None
        with mock.patch.object(res.cloud, '_client',
                               new_callable=self._fake_novaclient) as client:
            res.start()
            self.assertEquals(res.state, res.BOOTING)

    def test_start_single_failed(self):
        res = self._create()

        res.cloud._client = None
        with mock.patch.object(res.cloud, '_client',
                               new_callable=self._fake_novaclient) as client:
            client.servers.create.side_effect = novaclient.exceptions.ClientException('Did not work')
            self.assertRaises(novaclient.exceptions.ClientException, res.start)
            self.assertEquals(res.state, res.FAILED_TO_START)

    def test_start_many_with_single_failure(self):
        res = self._create(10)

        with mock.patch.object(res.cloud, '_client',
                               new_callable=self._fake_novaclient) as client:
            global counter
            counter = 0
            def side_effect(name, image, flavor, key_name, seen_names=set(), *args, **kwargs):
                global counter
                self.assertNotIn(name, seen_names, "Same name seen more than once")
                seen_names.add(name)

                counter += 1
                if counter < 6:
                    return mock.MagicMock()
                if counter == 6:
                    raise novaclient.exceptions.ClientException('Did not work')
                self.assertTrue(False, "Should not be called after one failure")

            client.servers.create.side_effect = side_effect
            self.assertRaises(novaclient.exceptions.ClientException, res.start)
            self.assertEquals(res.state, res.FAILED_TO_START)

    def test_terminate(self):
        res = self._create(10)

        with mock.patch.object(res.cloud, '_client',
                               new_callable=self._fake_novaclient) as client:
            res.start()
            slave_pks = [s.pk for s in res.slave_set.all()]

            res.terminate()
            self.assertEquals(Slave.objects.filter(pk__in=slave_pks).count(), 0)

    def test_terminate_fails(self):
        res = self._create(10)

        with mock.patch.object(res.cloud, '_client',
                               new_callable=self._fake_novaclient) as client:
            global counter
            counter = 0

            class Server(object):
                def __init__(self, *args, **kwargs):
                    pass

                def delete(self):
                    global counter
                    counter += 1
                    # Fail the last four times
                    if counter >= 6:
                        raise novaclient.exceptions.ClientException('Did not work')

            client.servers.get.side_effect = Server
            res.start()
            res.terminate()
            self.assertEquals(counter, 10)

    def _create_res(self):
        res = Reservation(cloud=Cloud.objects.get(), number_of_slaves=10)
        res.save()

        for x in range(10):
            slave = Slave('slave-%d' % (x,),
                          reservation=res,
                          cloud_node_id='slave-%d' % (x,))
            slave.save()
        return res

    def test_update_status_still_building(self):
        res = self._create_res()

        with mock.patch.object(cloudslave.models.Slave, '_fetch_current_state') as _fetch_current_state:
            _fetch_current_state.side_effect = ['BUILD'] * 10
            res.update_state()
            self.assertEquals(res.state, res.BOOTING)

    def test_update_status_fails(self):
        res = self._create_res()
        res.terminate = lambda: None

        with mock.patch.object(cloudslave.models.Slave, '_fetch_current_state') as _fetch_current_state:
            _fetch_current_state.side_effect = ['ERROR', Exception("Don't keep polling after you've seen a failure")]
            res.update_state()
            self.assertEquals(res.state, res.FAILED_TO_START)

    def test_update_status_times_out(self):
        res = self._create_res()
        res.terminate = lambda: None

        with mock.patch.object(cloudslave.models.Slave, '_fetch_current_state') as _fetch_current_state:
            res.timeout = datetime.datetime.now()
            _fetch_current_state.side_effect = ['BUILD'] * 10
            res.update_state()
            self.assertEquals(res.state, res.FAILED_TO_START)

    def test_update_status_active(self):
        res = self._create_res()
        res.terminate = lambda: None

        with mock.patch.object(cloudslave.models.Slave, '_fetch_current_state') as _fetch_current_state:
            _fetch_current_state.side_effect = ['ACTIVE'] * 10
            res.update_state()
            self.assertEquals(res.state, res.READY)
