# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DemoModel'
        db.create_table('demoapp_demomodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sometext', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('demoapp', ['DemoModel'])

        # Adding M2M table for field attachments on 'DemoModel'
        db.create_table('demoapp_demomodel_attachments', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('demomodel', models.ForeignKey(orm['demoapp.demomodel'], null=False)),
            ('file', models.ForeignKey(orm['upload.file'], null=False))
        ))
        db.create_unique('demoapp_demomodel_attachments', ['demomodel_id', 'file_id'])

        # Adding M2M table for field foo on 'DemoModel'
        db.create_table('demoapp_demomodel_foo', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('demomodel', models.ForeignKey(orm['demoapp.demomodel'], null=False)),
            ('file', models.ForeignKey(orm['upload.file'], null=False))
        ))
        db.create_unique('demoapp_demomodel_foo', ['demomodel_id', 'file_id'])


    def backwards(self, orm):
        # Deleting model 'DemoModel'
        db.delete_table('demoapp_demomodel')

        # Removing M2M table for field attachments on 'DemoModel'
        db.delete_table('demoapp_demomodel_attachments')

        # Removing M2M table for field foo on 'DemoModel'
        db.delete_table('demoapp_demomodel_foo')


    models = {
        'demoapp.demomodel': {
            'Meta': {'object_name': 'DemoModel'},
            'attachments': ('upload.modelfields.FileSetField', [], {'related_name': "'_demoapp_demomodel_attachments_related'", 'symmetrical': 'False', 'to': "orm['upload.File']"}),
            'foo': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['upload.File']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sometext': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'upload.file': {
            'Meta': {'object_name': 'File'},
            'document': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_image': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['demoapp']