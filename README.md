python-django-cloudslave
========================

I have a number of different applications that need to fire up instances in the
cloud to do various things. This module is supposed to be generically useful
for that purpose.

What is it?
-----------
It's an incredibly simple way to fire up instances in the cloud with very
little effort. It fires up instances of a predefined flavor based on a
predefined image.

What is it not?
---------------
A generic wrapper around the various OpenStack client libraries. It does one
thing and does it well.


How to use it?
--------------
First, you configure a cloud:

    >>> from cloudslave.models import Cloud
    >>> cloud = Cloud(user_name='user_name',
                      tenant_name='tenant_name',
                      password='v3rysecret',
                      endpoint='http://auth/url/v2.0',
                      region='XX-YY', # <-- Optional
                      flavor_name = 'm1.small',
                      image_name = 'regex that matches the name of the image (first match will be used)')
    >>> cloud.slave()


Then create a reservation:

    >>> res = cloud.create_reservation(5)  # Starts 5 instances
    >>> res.start()
    >>> res.update_state()
    1
    >>> res.get_state_display()
    'Booting'
    >>> res.update_state()
    2
    >>> res.get_state_display()
    'Ready'
    >>> [slave.run_cmd('hostname').strip() for slave in res.slave_set.all()]
    ['cloudslave-nthdnsrn', 'cloudslave-blhhmncq', 'cloudslave-vygfls4t']

Lovely.

Once you're done with them, terminate the reservation:

    >>> res.terminate()

That's it.
