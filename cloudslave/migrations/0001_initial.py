# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Cloud'
        db.create_table(u'cloudslave_cloud', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
            ('endpoint', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('user_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('tenant_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('flavor_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('image_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('floating_ip_mode', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'cloudslave', ['Cloud'])

        # Adding model 'KeyPair'
        db.create_table(u'cloudslave_keypair', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cloud', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloudslave.Cloud'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('private_key', self.gf('django.db.models.fields.TextField')()),
            ('public_key', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'cloudslave', ['KeyPair'])

        # Adding unique constraint on 'KeyPair', fields ['cloud', 'name']
        db.create_unique(u'cloudslave_keypair', ['cloud_id', 'name'])

        # Adding model 'Reservation'
        db.create_table(u'cloudslave_reservation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cloud', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloudslave.Cloud'])),
            ('number_of_slaves', self.gf('django.db.models.fields.IntegerField')()),
            ('state', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('timeout', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'cloudslave', ['Reservation'])

        # Adding model 'Slave'
        db.create_table(u'cloudslave_slave', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
            ('reservation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloudslave.Reservation'])),
            ('cloud_node_id', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal(u'cloudslave', ['Slave'])


    def backwards(self, orm):
        # Removing unique constraint on 'KeyPair', fields ['cloud', 'name']
        db.delete_unique(u'cloudslave_keypair', ['cloud_id', 'name'])

        # Deleting model 'Cloud'
        db.delete_table(u'cloudslave_cloud')

        # Deleting model 'KeyPair'
        db.delete_table(u'cloudslave_keypair')

        # Deleting model 'Reservation'
        db.delete_table(u'cloudslave_reservation')

        # Deleting model 'Slave'
        db.delete_table(u'cloudslave_slave')


    models = {
        u'cloudslave.cloud': {
            'Meta': {'object_name': 'Cloud'},
            'endpoint': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'flavor_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'floating_ip_mode': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'image_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'tenant_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'cloudslave.keypair': {
            'Meta': {'unique_together': "(('cloud', 'name'),)", 'object_name': 'KeyPair'},
            'cloud': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloudslave.Cloud']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'private_key': ('django.db.models.fields.TextField', [], {}),
            'public_key': ('django.db.models.fields.TextField', [], {})
        },
        u'cloudslave.reservation': {
            'Meta': {'object_name': 'Reservation'},
            'cloud': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloudslave.Cloud']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_slaves': ('django.db.models.fields.IntegerField', [], {}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'cloudslave.slave': {
            'Meta': {'object_name': 'Slave'},
            'cloud_node_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'reservation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloudslave.Reservation']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['cloudslave']