# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Slave.floating_ip'
        db.add_column(u'cloudslave_slave', 'floating_ip',
                      self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Slave.floating_ip'
        db.delete_column(u'cloudslave_slave', 'floating_ip')


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
            'floating_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'reservation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloudslave.Reservation']"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['cloudslave']